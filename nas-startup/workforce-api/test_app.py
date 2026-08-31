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
        "api_version": "v8",
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


# --- Cleartext transport for credential-bearing endpoints ------------------
# Security review 2026-08-31, F2: the bus already refused plain HTTP, but the
# legacy registry endpoints and the web UI did not, so WORKFORCE_API_KEY and all
# document content travelled in the clear over the published port 8080.


def test_legacy_endpoint_refuses_cleartext_before_checking_the_api_key():
    response = TestClient(workforce_app.app).get(
        "/workers", headers={"X-API-Key": os.environ["WORKFORCE_API_KEY"]}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "HTTPS_REQUIRED"}


def test_web_ui_refuses_cleartext():
    response = TestClient(workforce_app.app).get("/")
    assert response.status_code == 503
    assert response.json() == {"detail": "HTTPS_REQUIRED"}


def test_web_ui_is_served_over_https():
    response = TestClient(workforce_app.app, base_url="https://testserver").get("/")
    assert response.status_code == 200
    assert "Workforce Kernel" in response.text


def test_legacy_endpoint_still_rejects_a_wrong_api_key_over_https():
    response = TestClient(workforce_app.app, base_url="https://testserver").get(
        "/workers", headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_health_and_db_check_stay_reachable_over_cleartext(monkeypatch):
    # The container healthcheck calls /health on loopback without a forwarded
    # proto header, and the tokenless network probe relies on both endpoints.
    # Neither exposes a credential or any content.
    monkeypatch.setattr(workforce_app, "connection", lambda: FakeConnection([(1,)]))
    client = TestClient(workforce_app.app)
    assert client.get("/health").status_code == 200
    assert client.get("/db-check").status_code == 200


# --- Denial audit (review finding G-018) ------------------------------------


def test_every_bus_call_carries_its_audit_context():
    """No bus operation may be refused without leaving a record.

    An AST check rather than a runtime one: the gap G-018 describes is a call
    site that simply forgets the argument, and that is invisible until the day
    somebody looks for the missing denial in the audit trail. This fails at
    test time instead.
    """
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(workforce_app.__file__).read_text(encoding="utf-8"))
    missing = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"execute_bus_one", "execute_bus_many"}
        and not any(keyword.arg == "audit" for keyword in node.keywords)
    ]
    assert missing == [], f"bus calls without audit context at lines {missing}"


def test_a_refused_call_is_recorded_once_with_identifiers_only(monkeypatch):
    import psycopg

    recorded = []

    def failing_connection():
        raise psycopg.errors.InsufficientPrivilege("BUS_TASK_TRANSITION_DENIED")

    monkeypatch.setattr(workforce_app, "connection", failing_connection)
    monkeypatch.setattr(
        workforce_app, "record_denial",
        lambda audit, error: recorded.append((audit, error)),
    )

    audit = workforce_app.BusAudit(
        "TASK_TRANSITION", "TASK", "hash", "REQ-1", "ENG-TEST-1"
    )
    with pytest.raises(Exception):
        workforce_app.execute_bus_one("SELECT 1", (), audit=audit)

    assert len(recorded) == 1
    written, error = recorded[0]
    assert written.record_key == "ENG-TEST-1"
    assert written.operation == "TASK_TRANSITION"
    # The token hash stays in the tuple but never reaches the table: the SQL
    # function resolves it to an employee id and stores that instead.
    assert error.status_code in {400, 401, 403, 404, 409, 413, 422, 503}


def test_a_broken_audit_never_turns_a_denial_into_a_server_error(monkeypatch):
    import psycopg

    def failing_connection():
        raise psycopg.OperationalError("audit database unreachable")

    monkeypatch.setattr(workforce_app, "connection", failing_connection)
    audit = workforce_app.BusAudit("TASK_TRANSITION", "TASK", "hash", "REQ-2", "ENG-2")

    # Must return, not raise. The original 403 has to reach the caller intact.
    workforce_app.record_denial(
        audit, workforce_app.HTTPException(status_code=403, detail="BUS_X_DENIED")
    )
