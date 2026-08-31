"""Negative and boundary checks for the Workforce Bus over the real HTTPS API.

Closes activation-gate item 6 from WORKFORCE_BUS_ROLLOUT.md: the fail-closed
controls are already proven transactionally by
postgres-tests/002_workforce_bus_acceptance.sql, but never over the real
transport. This script runs inside the same short TESTING window as
bus_realtest_run.py and reuses the two ACCEPTANCE tokens created by
prepare_realtest_once.sh.

Every case asserts that the bus refuses an invalid request with the documented
status code and stable error identifier. A case that is "refused for the wrong
reason" counts as a failure, so a weakened control cannot pass unnoticed.

Never logs a raw token, a full message body or a stack trace.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable

TIMEOUT_SECONDS = 8
MAX_BODY_CHARS = 8000
MAX_HOPS = 4


def validate_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    parsed = urllib.parse.urlparse(base_url)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("BUS_NEGTEST_BASE_URL_INVALID")
    return base_url


def read_token(token_file: str) -> str:
    with open(token_file, encoding="utf-8") as handle:
        token = handle.read().strip()
    if not 32 <= len(token) <= 512:
        raise ValueError(f"BUS_NEGTEST_TOKEN_INVALID:{token_file}")
    return token


def raw_call(
    base_url: str,
    method: str,
    path: str,
    headers: dict[str, str],
    *,
    body: dict[str, Any] | None = None,
    context: ssl.SSLContext,
) -> tuple[int, Any]:
    """Issue one request with full control over the headers.

    Negative testing needs to omit or corrupt individual headers, so this does
    not reuse the realtest client, which always sends a well-formed set.
    """
    outgoing = dict(headers)
    outgoing.setdefault("Accept", "application/json")
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        outgoing["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{base_url}{path}", data=data, headers=outgoing, method=method
    )
    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS, context=context
        ) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"detail": f"HTTP_{exc.code}"}
        return exc.code, payload


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def writing(token: str, request_id: str, idempotency_key: str | None = None) -> dict[str, str]:
    headers = bearer(token)
    headers["X-Request-ID"] = request_id
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def message_body(recipient_id: str, body: str, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "recipient_id": recipient_id,
        "subject": "Bus-Negativtest",
        "body": body,
        "action_class": "INTERNAL_COMMUNICATION",
        "confidentiality": "NEED_TO_KNOW",
    }
    payload.update(overrides)
    return payload


class Recorder:
    """Collects one entry per case and tracks whether all of them passed."""

    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []

    def check(
        self,
        case: str,
        *,
        expected_status: int,
        expected_detail: str | Iterable[str] | None,
        actual_status: int,
        payload: Any,
    ) -> bool:
        detail = payload.get("detail") if isinstance(payload, dict) else None
        accepted = (
            None
            if expected_detail is None
            else {expected_detail} if isinstance(expected_detail, str)
            else set(expected_detail)
        )
        passed = actual_status == expected_status and (
            accepted is None or detail in accepted
        )
        self.cases.append(
            {
                "case": case,
                "result": "PASS" if passed else "FAIL",
                "expected_status": expected_status,
                "actual_status": actual_status,
                "expected_detail": sorted(accepted) if accepted else None,
                "actual_detail": detail,
            }
        )
        return passed

    def note(self, case: str, passed: bool, **fields: Any) -> bool:
        entry = {"case": case, "result": "PASS" if passed else "FAIL"}
        entry.update(fields)
        self.cases.append(entry)
        return passed

    @property
    def all_passed(self) -> bool:
        return all(case["result"] == "PASS" for case in self.cases)


def build_loop_chain(
    base_url: str,
    karl_token: str,
    thorsten_token: str,
    run_id: str,
    context: ssl.SSLContext,
) -> tuple[str | None, dict[str, Any]]:
    """Send a reply chain until one hop beyond max_hops.

    hop_count starts at 0 for a root message and the guard rejects
    hop_count > max_hops, so the chain needs max_hops + 2 messages in total and
    only the last one must be refused.
    """
    parent: str | None = None
    for index in range(MAX_HOPS + 2):
        sender_is_karl = index % 2 == 0
        token = karl_token if sender_is_karl else thorsten_token
        recipient = "RAS-001" if sender_is_karl else "SAO-001"
        body = message_body(recipient, f"Schleifentest Glied {index}.")
        if parent is not None:
            body["parent_message_id"] = parent

        status, payload = raw_call(
            base_url,
            "POST",
            "/bus/v1/messages",
            writing(
                token,
                f"BUS-NEGTEST-LOOP-{run_id}-{index}",
                f"IDEM-BUS-NEGTEST-LOOP-{run_id}-{index}",
            ),
            body=body,
            context=context,
        )

        if index == MAX_HOPS + 1:
            return parent, {"status": status, "payload": payload}
        if status != 201:
            return None, {"status": status, "payload": payload, "failed_at_hop": index}
        parent = payload["message_id"]

    return parent, {"status": 0, "payload": None}


def run(base_url: str, karl_token: str, thorsten_token: str, run_id: str) -> dict[str, Any]:
    base_url = validate_base_url(base_url)
    context = ssl.create_default_context()
    recorder = Recorder()

    status, payload = raw_call(
        base_url, "GET", "/bus/v1/status", {}, context=context
    )
    if status != 200 or payload.get("channel_status") != "TESTING":
        return {
            "result": "BLOCKED",
            "reason": "BUS_NEGTEST_CHANNEL_NOT_TESTING",
            "channel_status": payload.get("channel_status") if isinstance(payload, dict) else None,
        }

    # --- Authentication ---------------------------------------------------
    status, payload = raw_call(
        base_url, "GET", "/bus/v1/messages?scope=INBOX", bearer("Z" * 64), context=context
    )
    recorder.check(
        "unknown_token_rejected",
        expected_status=401,
        expected_detail="BUS_AUTH_FAILED",
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url, "GET", "/bus/v1/messages?scope=INBOX", bearer("tooshort"), context=context
    )
    recorder.check(
        "malformed_bearer_rejected",
        expected_status=401,
        expected_detail="BUS_BEARER_TOKEN_REQUIRED",
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url, "GET", "/bus/v1/messages?scope=INBOX", {}, context=context
    )
    recorder.check(
        "missing_authorization_rejected",
        expected_status=401,
        expected_detail="BUS_BEARER_TOKEN_REQUIRED",
        actual_status=status,
        payload=payload,
    )

    # --- Mandatory request headers ---------------------------------------
    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(karl_token, f"BUS-NEGTEST-NOIDEM-{run_id}"),
        body=message_body("RAS-001", "Ohne Idempotency-Key."),
        context=context,
    )
    recorder.check(
        "missing_idempotency_key_rejected",
        expected_status=400,
        expected_detail="BUS_IDEMPOTENCY_KEY_REQUIRED",
        actual_status=status,
        payload=payload,
    )

    headers = bearer(karl_token)
    headers["Idempotency-Key"] = f"IDEM-BUS-NEGTEST-NOREQ-{run_id}"
    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        headers,
        body=message_body("RAS-001", "Ohne Request-ID."),
        context=context,
    )
    recorder.check(
        "missing_request_id_rejected",
        expected_status=400,
        expected_detail="BUS_REQUEST_ID_REQUIRED",
        actual_status=status,
        payload=payload,
    )

    # --- Request shape ----------------------------------------------------
    status, payload = raw_call(
        base_url,
        "GET",
        "/bus/v1/messages?scope=EVERYTHING",
        bearer(karl_token),
        context=context,
    )
    recorder.check(
        "invalid_scope_rejected",
        expected_status=400,
        expected_detail="BUS_REQUEST_INVALID",
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(
            karl_token,
            f"BUS-NEGTEST-EXTRA-{run_id}",
            f"IDEM-BUS-NEGTEST-EXTRA-{run_id}",
        ),
        body=message_body("RAS-001", "Mit unbekanntem Feld.", sender_id="RAS-001"),
        context=context,
    )
    recorder.check(
        "unknown_field_rejected",
        expected_status=400,
        expected_detail="BUS_REQUEST_INVALID",
        actual_status=status,
        payload=payload,
    )

    # --- Routing and identity --------------------------------------------
    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(
            karl_token,
            f"BUS-NEGTEST-SELF-{run_id}",
            f"IDEM-BUS-NEGTEST-SELF-{run_id}",
        ),
        body=message_body("SAO-001", "Nachricht an mich selbst."),
        context=context,
    )
    recorder.check(
        "self_route_rejected",
        expected_status=403,
        expected_detail="BUS_SELF_ROUTE_DENIED",
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(
            karl_token,
            f"BUS-NEGTEST-UNKNOWN-{run_id}",
            f"IDEM-BUS-NEGTEST-UNKNOWN-{run_id}",
        ),
        body=message_body("ZZZ-999", "Empfaenger ausserhalb der Allowlist."),
        context=context,
    )
    recorder.check(
        "unlisted_recipient_rejected",
        expected_status=403,
        expected_detail=(
            "BUS_ROUTE_DENIED",
            "BUS_RECIPIENT_NOT_ACTIVE",
            "BUS_SEND_CAPABILITY_DENIED",
        ),
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url,
        "GET",
        "/bus/v1/messages?scope=PROJECT",
        bearer(thorsten_token),
        context=context,
    )
    recorder.check(
        "project_scope_denied_for_specialist",
        expected_status=403,
        expected_detail="BUS_PROJECT_READ_DENIED",
        actual_status=status,
        payload=payload,
    )

    # --- Acknowledgement controls ----------------------------------------
    status, seed = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(
            karl_token,
            f"BUS-NEGTEST-SEED-{run_id}",
            f"IDEM-BUS-NEGTEST-SEED-{run_id}",
        ),
        body=message_body("RAS-001", "Grundlage fuer die Ack-Negativtests."),
        context=context,
    )
    if status != 201:
        recorder.note("ack_seed_message", False, detail=seed)
        return {"result": "FAIL", "cases": recorder.cases}
    seed_message_id = seed["message_id"]
    recorder.note("ack_seed_message", True, message_id=seed_message_id)

    status, payload = raw_call(
        base_url,
        "POST",
        f"/bus/v1/messages/{seed_message_id}/ack",
        writing(karl_token, f"BUS-NEGTEST-ACKSENDER-{run_id}"),
        body={"decision": "ACCEPTED", "note": "Absender bestaetigt sich selbst."},
        context=context,
    )
    recorder.check(
        "ack_by_non_recipient_rejected",
        expected_status=403,
        expected_detail="BUS_ACK_DENIED",
        actual_status=status,
        payload=payload,
    )

    status, payload = raw_call(
        base_url,
        "POST",
        f"/bus/v1/messages/MSG-{'F' * 32}/ack",
        writing(thorsten_token, f"BUS-NEGTEST-ACKGHOST-{run_id}"),
        body={"decision": "ACCEPTED", "note": "Unbekannte Nachricht."},
        context=context,
    )
    recorder.check(
        # Deliberately BUS_ACK_DENIED and not 404: the bus must not reveal
        # whether an unknown message id exists.
        "ack_unknown_message_does_not_leak_existence",
        expected_status=403,
        expected_detail="BUS_ACK_DENIED",
        actual_status=status,
        payload=payload,
    )

    status, first_ack = raw_call(
        base_url,
        "POST",
        f"/bus/v1/messages/{seed_message_id}/ack",
        writing(thorsten_token, f"BUS-NEGTEST-ACK1-{run_id}"),
        body={"decision": "ACCEPTED", "note": "Erste Bestaetigung."},
        context=context,
    )
    recorder.note("ack_by_recipient_accepted", status == 200, actual_status=status)

    status, payload = raw_call(
        base_url,
        "POST",
        f"/bus/v1/messages/{seed_message_id}/ack",
        writing(thorsten_token, f"BUS-NEGTEST-ACK2-{run_id}"),
        body={"decision": "ACCEPTED", "note": "Wiederholte gleiche Bestaetigung."},
        context=context,
    )
    recorder.note(
        "ack_repeat_same_decision_is_idempotent",
        status == 200,
        actual_status=status,
    )

    status, payload = raw_call(
        base_url,
        "POST",
        f"/bus/v1/messages/{seed_message_id}/ack",
        writing(thorsten_token, f"BUS-NEGTEST-ACK3-{run_id}"),
        body={"decision": "REJECTED", "note": "Widersprechende Entscheidung."},
        context=context,
    )
    recorder.check(
        "conflicting_ack_decision_rejected",
        expected_status=409,
        expected_detail="BUS_ACK_ALREADY_FINAL",
        actual_status=status,
        payload=payload,
    )

    # --- Idempotency ------------------------------------------------------
    idem_key = f"IDEM-BUS-NEGTEST-REPLAY-{run_id}"
    replay_body = message_body("RAS-001", "Idempotenz-Wiederholung.")
    status_first, first = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(karl_token, f"BUS-NEGTEST-REPLAY1-{run_id}", idem_key),
        body=replay_body,
        context=context,
    )
    status_second, second = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(karl_token, f"BUS-NEGTEST-REPLAY2-{run_id}", idem_key),
        body=replay_body,
        context=context,
    )
    recorder.note(
        "identical_replay_creates_no_duplicate",
        status_first == 201
        and status_second == 201
        and first.get("message_id") == second.get("message_id"),
        message_id=first.get("message_id") if isinstance(first, dict) else None,
    )

    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(karl_token, f"BUS-NEGTEST-REPLAY3-{run_id}", idem_key),
        body=message_body("RAS-001", "Gleicher Schluessel, anderer Inhalt."),
        context=context,
    )
    recorder.check(
        "idempotency_key_reuse_with_different_body_rejected",
        expected_status=409,
        expected_detail="BUS_IDEMPOTENCY_CONFLICT",
        actual_status=status,
        payload=payload,
    )

    # --- Size and loop limits --------------------------------------------
    status, payload = raw_call(
        base_url,
        "POST",
        "/bus/v1/messages",
        writing(
            karl_token,
            f"BUS-NEGTEST-BIG-{run_id}",
            f"IDEM-BUS-NEGTEST-BIG-{run_id}",
        ),
        body=message_body("RAS-001", "x" * (MAX_BODY_CHARS + 1)),
        context=context,
    )
    recorder.check(
        "oversized_body_rejected",
        expected_status=413,
        expected_detail="BUS_BODY_TOO_LARGE",
        actual_status=status,
        payload=payload,
    )

    _, loop_result = build_loop_chain(
        base_url, karl_token, thorsten_token, run_id, context
    )
    recorder.check(
        "loop_limit_enforced",
        expected_status=422,
        expected_detail="BUS_LOOP_LIMIT_EXCEEDED",
        actual_status=loop_result["status"],
        payload=loop_result["payload"],
    )

    return {
        "result": "PASS" if recorder.all_passed else "FAIL",
        "cases_total": len(recorder.cases),
        "cases_failed": sum(1 for case in recorder.cases if case["result"] == "FAIL"),
        "cases": recorder.cases,
    }


def main() -> int:
    try:
        base_url = validate_base_url(os.environ.get("BUS_NEGTEST_BASE_URL", ""))
        karl_token = read_token(os.environ["KARL_BUS_TOKEN_FILE"])
        thorsten_token = read_token(os.environ["THORSTEN_BUS_TOKEN_FILE"])
        run_id = os.environ.get("BUS_NEGTEST_RUN_ID", "001").strip() or "001"
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    result = run(base_url, karl_token, thorsten_token, run_id)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
