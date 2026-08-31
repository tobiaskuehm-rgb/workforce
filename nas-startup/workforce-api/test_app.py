import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("WORKFORCE_API_KEY", "test-only-global-api-key")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")

import app as workforce_app


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, rows):
        self.rows = iter(rows)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_):
        return FakeCursor(next(self.rows))


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    workforce_app.app.dependency_overrides.clear()
    yield
    workforce_app.app.dependency_overrides.clear()


def test_existing_health_endpoint_is_preserved():
    response = TestClient(workforce_app.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_bus_status_reports_missing_migration_without_credentials(monkeypatch):
    monkeypatch.setattr(
        workforce_app,
        "connection",
        lambda: FakeConnection([(None,)]),
    )
    response = TestClient(workforce_app.app).get("/bus/v1/status")
    assert response.status_code == 200
    assert response.json() == {
        "api_version": "v6",
        "project_id": "START-UP",
        "migration": "missing",
        "channel_status": "MISSING",
    }


def test_bus_status_reports_disabled_channel(monkeypatch):
    monkeypatch.setattr(
        workforce_app,
        "connection",
        lambda: FakeConnection(
            [
                (("workforce.bus_channels",)),
                (("DISABLED", 4, 8000, True)),
            ]
        ),
    )
    response = TestClient(workforce_app.app).get("/bus/v1/status")
    assert response.status_code == 200
    assert response.json()["channel_status"] == "DISABLED"
    assert response.json()["migration"] == "002_workforce_bus"


def test_direct_http_rejects_bus_credentials_before_database_access():
    response = TestClient(workforce_app.app).get(
        "/bus/v1/messages",
        headers={"Authorization": "Bearer " + "x" * 48},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "BUS_HTTPS_REQUIRED"}


def test_invalid_bearer_is_rejected_over_https(monkeypatch):
    monkeypatch.setattr(workforce_app, "require_bus_ready", lambda: None)
    response = TestClient(workforce_app.app, base_url="https://testserver").get(
        "/bus/v1/messages",
        headers={"Authorization": "Bearer short"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "BUS_BEARER_TOKEN_REQUIRED"}


def test_message_id_is_stable_and_sender_is_not_client_controlled(monkeypatch):
    captured = []

    def fake_execute(sql, parameters):
        captured.append((sql, parameters))
        return {"message_id": parameters[2], "project_id": parameters[3]}

    monkeypatch.setattr(workforce_app, "execute_bus_one", fake_execute)
    workforce_app.app.dependency_overrides[workforce_app.require_bus_token] = lambda: "a" * 64
    workforce_app.app.dependency_overrides[workforce_app.require_request_id] = lambda: "REQ-TEST-001"
    workforce_app.app.dependency_overrides[workforce_app.require_idempotency_key] = lambda: "IDEM-TEST-00000001"

    client = TestClient(workforce_app.app, base_url="https://testserver")
    payload = {
        "recipient_id": "AI-ENG-001",
        "subject": "Technikstatus",
        "body": "Bitte prüfen.",
        "action_class": "INTERNAL_REVIEW",
        "confidentiality": "NEED_TO_KNOW",
        "task_ref": "ENG-003",
        "handoff_ref": "HO-020",
    }
    first = client.post("/bus/v1/messages", json=payload)
    second = client.post("/bus/v1/messages", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["message_id"] == second.json()["message_id"]
    assert first.json()["project_id"] == "START-UP"
    assert len(captured) == 2
    assert all(call[1][3] == "START-UP" for call in captured)
    assert all(len(call[1]) == 13 for call in captured)


def test_sender_spoof_and_external_action_are_rejected_before_sql(monkeypatch):
    called = False

    def fake_execute(*_):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(workforce_app, "execute_bus_one", fake_execute)
    workforce_app.app.dependency_overrides[workforce_app.require_bus_token] = lambda: "a" * 64
    workforce_app.app.dependency_overrides[workforce_app.require_request_id] = lambda: "REQ-TEST-002"
    workforce_app.app.dependency_overrides[workforce_app.require_idempotency_key] = lambda: "IDEM-TEST-00000002"
    client = TestClient(workforce_app.app, base_url="https://testserver")

    spoof = client.post(
        "/bus/v1/messages",
        json={
            "sender_id": "EAC-001",
            "recipient_id": "AI-ENG-001",
            "subject": "Spoof",
            "body": "Denied",
        },
    )
    external = client.post(
        "/bus/v1/messages",
        json={
            "recipient_id": "AI-ENG-001",
            "subject": "External",
            "body": "Denied",
            "action_class": "EXTERNAL_EMAIL",
        },
    )

    assert spoof.status_code == 400
    assert external.status_code == 400
    assert spoof.json() == {"detail": "BUS_REQUEST_INVALID"}
    assert external.json() == {"detail": "BUS_REQUEST_INVALID"}
    assert called is False


@pytest.mark.parametrize(
    ("sqlstate", "message", "expected"),
    [
        ("42501", "BUS_AUTH_FAILED", 401),
        ("42501", "BUS_ROUTE_DENIED", 403),
        ("23505", "BUS_IDEMPOTENCY_CONFLICT", 409),
        ("54000", "BUS_LOOP_LIMIT_EXCEEDED", 422),
        ("22001", "BUS_BODY_TOO_LARGE", 413),
        ("99999", "internal detail", 503),
    ],
)
def test_database_errors_are_mapped_without_unknown_details(sqlstate, message, expected):
    class Diag:
        message_primary = message

    class FakeError:
        diag = Diag()

    FakeError.sqlstate = sqlstate
    result = workforce_app.bus_error(FakeError())
    assert result.status_code == expected
    if sqlstate == "99999":
        assert result.detail == "BUS_DATABASE_UNAVAILABLE"


def test_no_bus_admin_or_external_action_endpoint_exists():
    paths = {route.path for route in workforce_app.app.routes}
    assert "/bus/v1/admin" not in paths
    assert "/bus/v1/credentials" not in paths
    assert "/bus/v1/email" not in paths
    assert "/bus/v1/whatsapp" not in paths
