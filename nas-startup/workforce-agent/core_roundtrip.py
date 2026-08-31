"""ENG-008 core roundtrip: Gerd, Karl and Anastasia over the real bus.

DEC-027 defines the core gate:

    Task → Mitarbeiter A → Ergebnis → Handoff → Mitarbeiter B → ACCEPTED →
    Bearbeitung → Ergebnis → Statusabschluss → Audit

plus REJECTED, missing permission, error state, persistence across a restart
and audit reconstruction. It also says explicitly that earlier bus acceptances
may be reused as evidence but do **not** replace this roundtrip - which is why
the Karl↔Thorsten realtest of 2026-08-31 does not close this gate.

The cast is fixed by DEC-027: the core is Gerd, Karl and Anastasia.

    Karl       SAO-001   creates and closes the task
    Gerd       AI-ENG-001 owner, does the first piece and hands off
    Anastasia  PEO-001   accepts the handoff and returns her result

No model is involved anywhere in here. ENG-008 forbids an external paid
service, and the roundtrip is about the runtime, not about answer quality.

Every step is driven through the real HTTPS API, one client per identity, so
permissions are exercised as they really are rather than simulated.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

import bus_client

SOURCE_REF_DEFAULT = "DEC-027/ENG-008"


@dataclass
class Transcript:
    """One line per step, so a failure says which one and why."""

    steps: list[dict[str, Any]] = field(default_factory=list)

    def ok(self, step: str, **fields: Any) -> None:
        entry = {"step": step, "result": "PASS"}
        entry.update(fields)
        self.steps.append(entry)

    def fail(self, step: str, **fields: Any) -> None:
        entry = {"step": step, "result": "FAIL"}
        entry.update(fields)
        self.steps.append(entry)

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [s for s in self.steps if s["result"] == "FAIL"]


def expect_refusal(
    transcript: Transcript,
    step: str,
    action: Callable[[], Any],
    *,
    expected_status: int,
    expected_details: tuple[str, ...] = (),
) -> None:
    """Assert that an action is refused, and refused for the right reason.

    A negative case that passes for the wrong reason is worse than no test:
    it looks like proof while proving nothing.
    """
    try:
        payload = action()
    except bus_client.BusError as error:
        detail_ok = not expected_details or error.detail in expected_details
        if error.status == expected_status and detail_ok:
            transcript.ok(step, status=error.status, detail=error.detail)
        else:
            transcript.fail(
                step, status=error.status, detail=error.detail,
                expected_status=expected_status,
                expected_detail=list(expected_details) or None,
            )
        return
    transcript.fail(step, detail="NOT_REFUSED", payload_keys=sorted(payload) if isinstance(payload, dict) else None)


def run_core_roundtrip(
    clients: dict[str, Any],
    *,
    run_id: str,
    source_ref: str = SOURCE_REF_DEFAULT,
) -> dict[str, Any]:
    """Drive the full lifecycle. Returns a transcript, never raises for a
    failed step - a run that stops halfway still has to be reportable."""
    karl = clients["karl"]
    gerd = clients["gerd"]
    anastasia = clients["anastasia"]

    task_id = f"ENG-CORE-{run_id}"
    handoff_id = f"HO-CORE-{run_id}"
    transcript = Transcript()

    def request_id(name: str) -> str:
        return f"CORE-{run_id}-{name}"

    def idem(name: str) -> str:
        return f"IDEM-CORE-{run_id}-{name}"

    # --- Preconditions ----------------------------------------------------
    status = karl.status()
    if status.get("channel_status") not in {"TESTING", "ACTIVE"}:
        return {
            "result": "BLOCKED",
            "reason": "CORE_CHANNEL_NOT_OPEN",
            "channel_status": status.get("channel_status"),
        }
    transcript.ok("channel_open", channel_status=status.get("channel_status"))

    # --- 1. Karl creates the task for Gerd --------------------------------
    try:
        task = karl.create_task(
            task_id=task_id,
            owner_id="AI-ENG-001",
            title="Core-Roundtrip: technische Vorpruefung",
            expected_output="Kurze technische Einschaetzung, danach Uebergabe an People.",
            source_ref=source_ref,
            request_id=request_id("TASK-CREATE"),
            idempotency_key=idem("TASK"),
        )
    except bus_client.BusError as error:
        transcript.fail("karl_creates_task", detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("karl_creates_task", task_id=task_id,
                  task_status=task.get("task_status"), owner=task.get("owner_id"))

    # Replay immediately, while the stored record still matches what we send.
    # The bus compares the current task against the replayed payload, so this
    # has to happen before any transition - afterwards it is a stale request,
    # not a duplicate, and 409 would be the correct answer.
    try:
        replay = karl.create_task(
            task_id=task_id,
            owner_id="AI-ENG-001",
            title="Core-Roundtrip: technische Vorpruefung",
            expected_output="Kurze technische Einschaetzung, danach Uebergabe an People.",
            source_ref=source_ref,
            request_id=request_id("TASK-REPLAY"),
            idempotency_key=idem("TASK"),
        )
        transcript.ok("task_replay_is_idempotent",
                      same_task=replay.get("task_id") == task_id)
    except bus_client.BusError as error:
        transcript.fail("task_replay_is_idempotent",
                        detail=error.detail, status=error.status)

    # --- 2. Gerd (A) takes it and works it --------------------------------
    owned = gerd.tasks(scope="OWNED")
    if not any(t.get("task_id") == task_id for t in owned):
        transcript.fail("gerd_sees_task", detail="TASK_NOT_IN_OWNED_SCOPE")
        return _result(transcript, task_id, handoff_id)
    transcript.ok("gerd_sees_task", scope="OWNED")

    # The bus grants PENDING -> OPEN to SAO-001 only, and only for the three
    # named owners (002_workforce_bus.sql, bus_transition_task). The owner
    # cannot lift his own task out of PENDING - coordination stays with Karl.
    if task.get("task_status") == "PENDING":
        try:
            opened = karl.transition_task(
                task_id, new_status="OPEN", request_id=request_id("TASK-OPEN")
            )
        except bus_client.BusError as error:
            transcript.fail("karl_opens_task", detail=error.detail, status=error.status)
            return _result(transcript, task_id, handoff_id)
        transcript.ok("karl_opens_task", task_status=opened.get("task_status"))

    try:
        working = gerd.transition_task(
            task_id, new_status="IN_PROGRESS", request_id=request_id("TASK-INPROGRESS")
        )
    except bus_client.BusError as error:
        transcript.fail("gerd_starts_work", detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("gerd_starts_work", task_status=working.get("task_status"))

    # --- 3. Gerd's result, as a message back to Karl ----------------------
    try:
        result_message = gerd.send_message(
            recipient_id="SAO-001",
            subject=f"Zwischenergebnis {task_id}",
            body="Technische Vorpruefung abgeschlossen. Uebergabe an People folgt.",
            parent_message_id=None,
            request_id=request_id("GERD-RESULT"),
            idempotency_key=idem("GERD-RESULT"),
        )
    except bus_client.BusError as error:
        transcript.fail("gerd_reports_result", detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("gerd_reports_result", message_id=result_message.get("message_id"))

    # --- 4. Handoff Gerd → Anastasia (B) ----------------------------------
    try:
        handoff = gerd.create_handoff(
            handoff_id=handoff_id,
            recipient_id="PEO-001",
            input_summary="Technische Vorpruefung liegt vor.",
            expected_output="Organisatorische Einordnung und Rueckmeldung.",
            source_ref=source_ref,
            task_ref=task_id,
            request_id=request_id("HANDOFF-CREATE"),
            idempotency_key=idem("HANDOFF"),
        )
    except bus_client.BusError as error:
        transcript.fail("gerd_creates_handoff", detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("gerd_creates_handoff", handoff_id=handoff_id,
                  handoff_status=handoff.get("handoff_status"))

    # A handoff is born PENDING and only its sender may move it to OPEN
    # (002_workforce_bus.sql, bus_transition_handoff). The recipient decides
    # only once it is OPEN - the sender finalises, then the other side rules.
    if handoff.get("handoff_status") == "PENDING":
        try:
            handoff = gerd.transition_handoff(
                handoff_id, new_status="OPEN",
                request_id=request_id("HANDOFF-OPEN"),
            )
        except bus_client.BusError as error:
            transcript.fail("gerd_opens_handoff", detail=error.detail, status=error.status)
            return _result(transcript, task_id, handoff_id)
        transcript.ok("gerd_opens_handoff", handoff_status=handoff.get("handoff_status"))

    # --- 5. Anastasia accepts --------------------------------------------
    inbox = anastasia.handoffs(scope="INBOX")
    if not any(h.get("handoff_id") == handoff_id for h in inbox):
        transcript.fail("anastasia_sees_handoff", detail="HANDOFF_NOT_IN_INBOX")
        return _result(transcript, task_id, handoff_id)
    transcript.ok("anastasia_sees_handoff")

    try:
        accepted = anastasia.transition_handoff(
            handoff_id, new_status="ACCEPTED",
            request_id=request_id("HANDOFF-ACCEPT"),
            response_note="Uebernommen zur organisatorischen Einordnung.",
        )
    except bus_client.BusError as error:
        transcript.fail("anastasia_accepts_handoff",
                        detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("anastasia_accepts_handoff",
                  handoff_status=accepted.get("handoff_status"))

    # --- 6. Anastasia's result -------------------------------------------
    try:
        peo_result = anastasia.send_message(
            recipient_id="AI-ENG-001",
            subject=f"Rueckmeldung {task_id}",
            body="Organisatorische Einordnung abgeschlossen, keine Einwaende.",
            parent_message_id=None,
            request_id=request_id("PEO-RESULT"),
            idempotency_key=idem("PEO-RESULT"),
        )
    except bus_client.BusError as error:
        transcript.fail("anastasia_reports_result",
                        detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("anastasia_reports_result", message_id=peo_result.get("message_id"))

    # --- 7. Owner to REVIEW, creator closes as DONE -----------------------
    try:
        reviewed = gerd.transition_task(
            task_id, new_status="REVIEW", request_id=request_id("TASK-REVIEW")
        )
    except bus_client.BusError as error:
        transcript.fail("gerd_moves_task_review",
                        detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("gerd_moves_task_review", task_status=reviewed.get("task_status"))

    # DONE without evidence must be refused - the error-state case from the
    # DEC-027 gate, checked here rather than as an afterthought.
    expect_refusal(
        transcript, "done_without_evidence_refused",
        lambda: karl.transition_task(
            task_id, new_status="DONE", request_id=request_id("TASK-DONE-NOEV")
        ),
        expected_status=400,
        expected_details=("BUS_TASK_COMPLETION_EVIDENCE_REQUIRED",),
    )

    try:
        done = karl.transition_task(
            task_id, new_status="DONE",
            request_id=request_id("TASK-DONE"),
            completion_evidence=(
                f"Core-Roundtrip {run_id}: Vorpruefung durch AI-ENG-001, "
                f"Handoff {handoff_id} durch PEO-001 angenommen und beantwortet."
            ),
        )
    except bus_client.BusError as error:
        transcript.fail("karl_closes_task", detail=error.detail, status=error.status)
        return _result(transcript, task_id, handoff_id)
    transcript.ok("karl_closes_task", task_status=done.get("task_status"))

    # --- 8. Negative cases ------------------------------------------------
    _negative_cases(transcript, clients, run_id, source_ref, handoff_id, request_id, idem)

    return _result(transcript, task_id, handoff_id)


def _negative_cases(transcript, clients, run_id, source_ref, handoff_id, request_id, idem) -> None:
    """REJECTED and missing permission, both required by the DEC-027 gate."""
    karl = clients["karl"]
    gerd = clients["gerd"]
    anastasia = clients["anastasia"]

    # REJECTED: a second handoff that B turns down.
    reject_id = f"HO-CORE-{run_id}-REJ"
    try:
        gerd.create_handoff(
            handoff_id=reject_id,
            recipient_id="PEO-001",
            input_summary="Zweite Uebergabe, bewusst zur Ablehnung.",
            expected_output="Ablehnung mit Begruendung.",
            source_ref=source_ref,
            request_id=request_id("HANDOFF-REJ-CREATE"),
            idempotency_key=idem("HANDOFF-REJ"),
        )
    except bus_client.BusError as error:
        transcript.fail("handoff_for_rejection_created",
                        detail=error.detail, status=error.status)
        return
    transcript.ok("handoff_for_rejection_created", handoff_id=reject_id)

    try:
        gerd.transition_handoff(
            reject_id, new_status="OPEN", request_id=request_id("HANDOFF-REJ-OPEN")
        )
    except bus_client.BusError as error:
        transcript.fail("handoff_for_rejection_opened",
                        detail=error.detail, status=error.status)
        return
    transcript.ok("handoff_for_rejection_opened")

    try:
        rejected = anastasia.transition_handoff(
            reject_id, new_status="REJECTED",
            request_id=request_id("HANDOFF-REJ"),
            response_note="Ausserhalb des organisatorischen Scopes.",
        )
        transcript.ok("anastasia_rejects_handoff",
                      handoff_status=rejected.get("handoff_status"))
    except bus_client.BusError as error:
        transcript.fail("anastasia_rejects_handoff",
                        detail=error.detail, status=error.status)

    # Missing permission: only the recipient may decide a handoff.
    # REJECTED, not ACCEPTED: the handoff is already ACCEPTED, and asking for
    # the status it already has is answered as an idempotency conflict before
    # permissions are looked at. A negative case has to reach the check it
    # claims to test.
    expect_refusal(
        transcript, "third_party_cannot_decide_handoff",
        lambda: karl.transition_handoff(
            handoff_id, new_status="REJECTED",
            request_id=request_id("HANDOFF-STEAL"),
            response_note="Unbefugter Zugriffsversuch im Negativtest.",
        ),
        expected_status=403,
        expected_details=("BUS_HANDOFF_TRANSITION_DENIED", "BUS_HANDOFF_NOT_FOUND"),
    )

    # Missing permission: a non-owner may not drive someone else's task.
    expect_refusal(
        transcript, "non_owner_cannot_transition_task",
        lambda: anastasia.transition_task(
            f"ENG-CORE-{run_id}", new_status="IN_PROGRESS",
            request_id=request_id("TASK-STEAL"),
        ),
        expected_status=403,
        expected_details=("BUS_TASK_TRANSITION_DENIED",),
    )


def _result(transcript: Transcript, task_id: str, handoff_id: str) -> dict[str, Any]:
    return {
        "result": "PASS" if not transcript.failed else "FAIL",
        "task_id": task_id,
        "handoff_id": handoff_id,
        "steps_total": len(transcript.steps),
        "steps_failed": len(transcript.failed),
        "transcript": transcript.steps,
    }


def build_clients(base_url: str, token_files: dict[str, str]) -> dict[str, Any]:
    context = ssl.create_default_context()
    return {
        name: bus_client.BusClient(
            base_url=base_url,
            token=bus_client.read_token(path),
            context=context,
        )
        for name, path in token_files.items()
    }


def main() -> int:
    try:
        base_url = bus_client.validate_base_url(os.environ.get("CORE_BUS_BASE_URL", ""))
        token_files = {
            "karl": os.environ["KARL_BUS_TOKEN_FILE"],
            "gerd": os.environ["GERD_BUS_TOKEN_FILE"],
            "anastasia": os.environ["ANASTASIA_BUS_TOKEN_FILE"],
        }
        run_id = os.environ["CORE_RUN_ID"].strip()
        if not run_id:
            raise ValueError("CORE_RUN_ID_EMPTY")
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    clients = build_clients(base_url, token_files)
    result = run_core_roundtrip(
        clients,
        run_id=run_id,
        source_ref=os.environ.get("CORE_SOURCE_REF", SOURCE_REF_DEFAULT),
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
