"""Closes records left behind by aborted test runs, through the bus's own rules.

The core roundtrip needed four attempts on 2026-08-31. Attempts one and two
left a task at IN_PROGRESS and a handoff at PENDING each - records that look
like open work but are not.

Tempting shortcut: an UPDATE straight against the database. Refused, for a
reason worth stating: the bus grants CANCELLED only out of PENDING, so
abandoned work cannot be swept away silently. That constraint is the point,
not an obstacle, and going around it with SQL would undermine exactly the
controls this project spent the day proving.

So the records are closed the way any other work is closed:

  Task     owner IN_PROGRESS -> REVIEW, creator REVIEW -> DONE with evidence
  Handoff  sender PENDING -> CANCELLED

The evidence text says plainly what these were. A cleanup that dressed an
aborted test up as completed work would be worse than leaving the mess.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from typing import Any

import bus_client
import bus_rules

KARL, GERD, ANASTASIA = "SAO-001", "AI-ENG-001", "PEO-001"

EVIDENCE = (
    "Abgebrochener Testlauf des Core-Roundtrips vom 2026-08-31. Keine fachliche "
    "Arbeit, kein fachliches Ergebnis. Geschlossen, damit der Datensatz nicht "
    "als offene Arbeit erscheint."
)
CANCEL_NOTE = "Abgebrochener Testlauf, nie an den Empfaenger uebergeben."


def close_task(clients, task_id: str, *, run_id: str,
               steps: list[dict[str, Any]]) -> None:
    """Walk one abandoned task to DONE, from wherever it stands."""
    karl, gerd = clients["karl"], clients["gerd"]

    task = next((t for t in karl.tasks(scope="CREATED")
                 if t.get("task_id") == task_id), None)
    if task is None:
        steps.append({"record": task_id, "result": "SKIPPED", "detail": "NOT_FOUND"})
        return

    current = task.get("task_status")
    if current in ("DONE", "CANCELLED"):
        steps.append({"record": task_id, "result": "SKIPPED",
                      "detail": f"ALREADY_{current}"})
        return

    # PENDING has its own exit that costs nothing: the creator may cancel it
    # outright, which is honest and leaves no completion claim behind.
    if current == "PENDING":
        try:
            karl.transition_task(task_id, new_status="CANCELLED",
                                 request_id=f"LEFTOVER-{run_id}-{task_id}-CANCEL")
            steps.append({"record": task_id, "result": "CANCELLED"})
        except bus_client.BusError as error:
            steps.append({"record": task_id, "result": "FAILED",
                          "detail": error.detail})
        return

    if current != "REVIEW":
        if not bus_rules.may_transition_task(
            GERD, creator_id=KARL, owner_id=GERD, current=current, target="REVIEW"
        ):
            steps.append({"record": task_id, "result": "FAILED",
                          "detail": f"NO_PATH_FROM_{current}"})
            return
        try:
            gerd.transition_task(task_id, new_status="REVIEW",
                                 request_id=f"LEFTOVER-{run_id}-{task_id}-REVIEW")
        except bus_client.BusError as error:
            steps.append({"record": task_id, "result": "FAILED",
                          "detail": error.detail})
            return

    try:
        karl.transition_task(task_id, new_status="DONE",
                             request_id=f"LEFTOVER-{run_id}-{task_id}-DONE",
                             completion_evidence=EVIDENCE)
        steps.append({"record": task_id, "result": "CLOSED", "from": current})
    except bus_client.BusError as error:
        steps.append({"record": task_id, "result": "FAILED", "detail": error.detail})


def cancel_handoff(clients, handoff_id: str, *, run_id: str,
                   steps: list[dict[str, Any]]) -> None:
    gerd = clients["gerd"]
    handoff = next((h for h in gerd.handoffs(scope="OUTBOX")
                    if h.get("handoff_id") == handoff_id), None)
    if handoff is None:
        steps.append({"record": handoff_id, "result": "SKIPPED", "detail": "NOT_FOUND"})
        return

    current = handoff.get("handoff_status")
    if current in ("ACCEPTED", "REJECTED", "CANCELLED"):
        steps.append({"record": handoff_id, "result": "SKIPPED",
                      "detail": f"ALREADY_{current}"})
        return

    try:
        gerd.transition_handoff(handoff_id, new_status="CANCELLED",
                                request_id=f"LEFTOVER-{run_id}-{handoff_id}-CANCEL",
                                response_note=CANCEL_NOTE)
        steps.append({"record": handoff_id, "result": "CANCELLED", "from": current})
    except bus_client.BusError as error:
        steps.append({"record": handoff_id, "result": "FAILED", "detail": error.detail})


def run_cleanup(clients: dict[str, Any], *, run_id: str,
                task_ids: tuple[str, ...], handoff_ids: tuple[str, ...]) -> dict[str, Any]:
    status = clients["karl"].status()
    if status.get("channel_status") not in {"TESTING", "ACTIVE"}:
        return {"result": "BLOCKED", "reason": "LEFTOVER_CHANNEL_NOT_OPEN",
                "channel_status": status.get("channel_status")}

    steps: list[dict[str, Any]] = []
    for handoff_id in handoff_ids:
        cancel_handoff(clients, handoff_id, run_id=run_id, steps=steps)
    for task_id in task_ids:
        close_task(clients, task_id, run_id=run_id, steps=steps)

    failed = [s for s in steps if s["result"] == "FAILED"]
    return {
        "result": "PASS" if not failed else "FAIL",
        "handled": len(steps),
        "failed": len(failed),
        "steps": steps,
    }


def main() -> int:
    try:
        base_url = bus_client.validate_base_url(os.environ.get("CORE_BUS_BASE_URL", ""))
        run_id = os.environ["CORE_RUN_ID"].strip()
        task_ids = tuple(
            item.strip() for item in os.environ.get("LEFTOVER_TASK_IDS", "").split(",")
            if item.strip()
        )
        handoff_ids = tuple(
            item.strip() for item in os.environ.get("LEFTOVER_HANDOFF_IDS", "").split(",")
            if item.strip()
        )
        if not task_ids and not handoff_ids:
            raise ValueError("LEFTOVER_NOTHING_TO_DO")
        context = ssl.create_default_context()
        clients = {
            name: bus_client.BusClient(
                base_url=base_url,
                token=bus_client.read_token(os.environ[var]),
                context=context,
            )
            for name, var in (
                ("karl", "KARL_BUS_TOKEN_FILE"),
                ("gerd", "GERD_BUS_TOKEN_FILE"),
            )
        }
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    result = run_cleanup(clients, run_id=run_id, task_ids=task_ids,
                         handoff_ids=handoff_ids)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
