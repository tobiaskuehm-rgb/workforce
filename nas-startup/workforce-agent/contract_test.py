"""Contract test: does the real bus answer the way bus_rules.py claims?

bus_rules.py is a transcription of 002_workforce_bus.sql. A transcription can
drift: change the migration and the local suite keeps passing while being
wrong. This closes that gap by asking the running bus itself.

The design keeps the footprint small on purpose. A naive matrix test would
create a task per state and leave a trail of abandoned records - and the bus
deliberately refuses to cancel anything past PENDING, so that trail could not
be cleaned up afterwards.

Instead: **one** task and **one** handoff, walked through their states, and at
every state every transition the table predicts as *denied* is attempted.
A denial changes nothing, so the whole denial matrix costs two records. The
allowed transitions are the walk itself, and the task ends DONE - a clean
final state rather than litter.

Run inside the same window as any other credentialed test. Read-only in
effect apart from the one task and one handoff it completes.
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

# States we can reach with one record, and what may be attempted from each.
TASK_STATES = ("PENDING", "OPEN", "IN_PROGRESS", "REVIEW", "DONE")
TASK_TARGETS = ("OPEN", "IN_PROGRESS", "BLOCKED", "HOLD", "REVIEW", "DONE", "CANCELLED")
HANDOFF_STATES = ("PENDING", "OPEN", "ACCEPTED")
HANDOFF_TARGETS = ("OPEN", "ACCEPTED", "REJECTED", "CANCELLED")


def _record(results: list[dict[str, Any]], *, kind: str, identity: str,
            current: str, target: str, predicted: bool, observed: bool,
            detail: str | None) -> None:
    results.append({
        "kind": kind, "identity": identity, "from": current, "to": target,
        "predicted": "ALLOW" if predicted else "DENY",
        "observed": "ALLOW" if observed else "DENY",
        "detail": detail,
        "result": "PASS" if predicted == observed else "FAIL",
    })


def probe_task_denials(clients, task_id: str, current: str,
                       creator_id: str, owner_id: str,
                       run_id: str, results: list[dict[str, Any]]) -> None:
    """Attempt every denied task transition from the current state.

    Only denials: an allowed transition would move the record and invalidate
    the rest of the sweep. The allowed ones are covered by the walk itself.
    """
    for name, client in clients.items():
        identity = {"karl": KARL, "gerd": GERD, "anastasia": ANASTASIA}[name]
        for target in TASK_TARGETS:
            if target == current:
                continue  # answered as an idempotency conflict, not a permission
            predicted = bus_rules.may_transition_task(
                identity, creator_id=creator_id, owner_id=owner_id,
                current=current, target=target,
            )
            if predicted:
                continue  # would mutate; covered by the walk
            try:
                client.transition_task(
                    task_id, new_status=target,
                    request_id=f"CONTRACT-{run_id}-T-{identity}-{current}-{target}",
                    completion_evidence="Vertragstest." if target == "DONE" else None,
                )
                observed, detail = True, None
            except bus_client.BusError as error:
                observed, detail = False, error.detail
            _record(results, kind="TASK", identity=identity, current=current,
                    target=target, predicted=False, observed=observed, detail=detail)


def probe_handoff_denials(clients, handoff_id: str, current: str,
                          sender_id: str, recipient_id: str,
                          run_id: str, results: list[dict[str, Any]]) -> None:
    for name, client in clients.items():
        identity = {"karl": KARL, "gerd": GERD, "anastasia": ANASTASIA}[name]
        for target in HANDOFF_TARGETS:
            if target == current:
                continue
            predicted = bus_rules.may_transition_handoff(
                identity, sender_id=sender_id, recipient_id=recipient_id,
                current=current, target=target,
            )
            if predicted:
                continue
            try:
                client.transition_handoff(
                    handoff_id, new_status=target,
                    request_id=f"CONTRACT-{run_id}-H-{identity}-{current}-{target}",
                    response_note="Vertragstest." if target == "REJECTED" else None,
                )
                observed, detail = True, None
            except bus_client.BusError as error:
                observed, detail = False, error.detail
            _record(results, kind="HANDOFF", identity=identity, current=current,
                    target=target, predicted=False, observed=observed, detail=detail)


def run_contract_test(clients: dict[str, Any], *, run_id: str,
                      source_ref: str = "DEC-027/ENG-008") -> dict[str, Any]:
    karl, gerd, anastasia = clients["karl"], clients["gerd"], clients["anastasia"]
    task_id = f"ENG-CONTRACT-{run_id}"
    handoff_id = f"HO-CONTRACT-{run_id}"
    results: list[dict[str, Any]] = []

    status = karl.status()
    if status.get("channel_status") not in {"TESTING", "ACTIVE"}:
        return {"result": "BLOCKED", "reason": "CONTRACT_CHANNEL_NOT_OPEN",
                "channel_status": status.get("channel_status")}

    # --- One task, walked through its states -----------------------------
    try:
        karl.create_task(
            task_id=task_id, owner_id=GERD,
            title="Vertragstest der Uebergangsregeln",
            expected_output="Nur Ablehnungen pruefen; keine fachliche Arbeit.",
            source_ref=source_ref,
            request_id=f"CONTRACT-{run_id}-TASK-CREATE",
            idempotency_key=f"IDEM-CONTRACT-{run_id}-TASK",
        )
    except bus_client.BusError as error:
        return {"result": "BLOCKED", "reason": f"TASK_CREATE_FAILED:{error.detail}"}

    walk = [
        ("PENDING", None, None),
        ("OPEN", karl, f"CONTRACT-{run_id}-TASK-OPEN"),
        ("IN_PROGRESS", gerd, f"CONTRACT-{run_id}-TASK-PROGRESS"),
        ("REVIEW", gerd, f"CONTRACT-{run_id}-TASK-REVIEW"),
        ("DONE", karl, f"CONTRACT-{run_id}-TASK-DONE"),
    ]
    for state, mover, request_id in walk:
        if mover is not None:
            try:
                mover.transition_task(
                    task_id, new_status=state, request_id=request_id,
                    completion_evidence=(
                        f"Vertragstest {run_id}: nur Regelpruefung, keine fachliche Arbeit."
                        if state == "DONE" else None
                    ),
                )
            except bus_client.BusError as error:
                results.append({"kind": "WALK", "step": state, "result": "FAIL",
                                "detail": error.detail})
                break
        probe_task_denials(clients, task_id, state, KARL, GERD, run_id, results)

    # --- One handoff, same treatment -------------------------------------
    try:
        gerd.create_handoff(
            handoff_id=handoff_id, recipient_id=ANASTASIA,
            input_summary="Vertragstest der Uebergangsregeln.",
            expected_output="Nur Ablehnungen pruefen.",
            source_ref=source_ref, task_ref=task_id,
            request_id=f"CONTRACT-{run_id}-HANDOFF-CREATE",
            idempotency_key=f"IDEM-CONTRACT-{run_id}-HANDOFF",
        )
    except bus_client.BusError as error:
        results.append({"kind": "WALK", "step": "HANDOFF_CREATE", "result": "FAIL",
                        "detail": error.detail})
        return _summarise(results, task_id, handoff_id)

    handoff_walk = [
        ("PENDING", None, None),
        ("OPEN", gerd, f"CONTRACT-{run_id}-HANDOFF-OPEN"),
        ("ACCEPTED", anastasia, f"CONTRACT-{run_id}-HANDOFF-ACCEPT"),
    ]
    for state, mover, request_id in handoff_walk:
        if mover is not None:
            try:
                mover.transition_handoff(handoff_id, new_status=state,
                                         request_id=request_id)
            except bus_client.BusError as error:
                results.append({"kind": "WALK", "step": state, "result": "FAIL",
                                "detail": error.detail})
                break
        probe_handoff_denials(clients, handoff_id, state, GERD, ANASTASIA,
                              run_id, results)

    return _summarise(results, task_id, handoff_id)


def _summarise(results, task_id, handoff_id) -> dict[str, Any]:
    failed = [r for r in results if r["result"] == "FAIL"]
    return {
        "result": "PASS" if not failed else "FAIL",
        "task_id": task_id,
        "handoff_id": handoff_id,
        "checks_total": len(results),
        "checks_failed": len(failed),
        # A full transcript would be hundreds of lines; only divergences are
        # interesting, and a divergence is exactly what this test exists for.
        "divergences": failed,
    }


def main() -> int:
    try:
        base_url = bus_client.validate_base_url(os.environ.get("CORE_BUS_BASE_URL", ""))
        run_id = os.environ["CORE_RUN_ID"].strip()
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
                ("anastasia", "ANASTASIA_BUS_TOKEN_FILE"),
            )
        }
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    result = run_contract_test(clients, run_id=run_id)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
