"""Contract test: does the real bus answer the way bus_rules.py claims?

bus_rules.py is a transcription of 002_workforce_bus.sql. A transcription can
drift: change the migration and the local suite keeps passing while being
wrong. This closes that gap by asking the running bus itself.

Two halves, reported separately - review finding G-014.

**DENY.** At every state a record reaches, every transition the table predicts
as denied is attempted. A denial changes nothing, so this half is nearly free.
It is not enough to see *a* failure: the earlier version counted any BusError
as a correct refusal, which meant a 401, a 500 or a closed channel scored as a
pass and a broken bus could look green. Every denial now has to arrive as the
exact status and error identifier the migration raises; anything else is
reported as WRONG_REASON, which is a failure.

**ALLOW.** Every (from, to) pair the table permits is executed positively
against the real bus at least once, and the run fails if a single pair is left
uncovered. Some states are only reachable once per record - nothing leads back
to OPEN - so this needs five tasks and four handoffs rather than one of each.
The count is the price of the claim: a one-sided denial matrix proves the bus
refuses things, never that it permits what it should.

Footprint: nine records, all left in a final state (DONE, CANCELLED, ACCEPTED,
REJECTED). Nothing to clean up afterwards, which matters because the bus
refuses to cancel anything past PENDING.

Run inside the same window as any other credentialed test.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from dataclasses import dataclass
from typing import Any

import bus_client
import bus_rules

KARL, GERD, ANASTASIA = "SAO-001", "AI-ENG-001", "PEO-001"
IDENTITY_OF = {"karl": KARL, "gerd": GERD, "anastasia": ANASTASIA}

# What a permission refusal must look like. Sourced from the migration:
# bus_transition_task / bus_transition_handoff raise ERRCODE 42501, which
# workforce-api maps to HTTP 403.
DENIAL_EXPECTED = {
    "TASK": ("BUS_TASK_TRANSITION_DENIED", 403),
    "HANDOFF": ("BUS_HANDOFF_TRANSITION_DENIED", 403),
}


@dataclass(frozen=True)
class Plan:
    """One record and the allowed transitions it walks, in order."""
    key: str
    steps: tuple[tuple[str, str], ...]  # (actor name, target status)


# Five tasks. OPEN is reachable exactly once per task and nothing leads back to
# it, so each of the four OPEN -> x pairs needs its own record; the long walk
# in A carries the nine owner pairs among IN_PROGRESS/BLOCKED/HOLD and both
# creator pairs out of REVIEW. E exists for PENDING -> CANCELLED alone.
TASK_PLANS: tuple[Plan, ...] = (
    Plan("A", (
        ("karl", "OPEN"), ("gerd", "IN_PROGRESS"),
        ("gerd", "BLOCKED"), ("gerd", "HOLD"), ("gerd", "IN_PROGRESS"),
        ("gerd", "HOLD"), ("gerd", "BLOCKED"), ("gerd", "IN_PROGRESS"),
        ("gerd", "REVIEW"), ("karl", "IN_PROGRESS"),
        ("gerd", "BLOCKED"), ("gerd", "REVIEW"), ("karl", "IN_PROGRESS"),
        ("gerd", "HOLD"), ("gerd", "REVIEW"),
        ("karl", "DONE"),
    )),
    Plan("B", (("karl", "OPEN"), ("gerd", "BLOCKED"), ("gerd", "REVIEW"), ("karl", "DONE"))),
    Plan("C", (("karl", "OPEN"), ("gerd", "HOLD"), ("gerd", "REVIEW"), ("karl", "DONE"))),
    Plan("D", (("karl", "OPEN"), ("gerd", "REVIEW"), ("karl", "DONE"))),
    Plan("E", (("karl", "CANCELLED"),)),
)

HANDOFF_PLANS: tuple[Plan, ...] = (
    Plan("A", (("gerd", "OPEN"), ("anastasia", "ACCEPTED"))),
    Plan("B", (("gerd", "OPEN"), ("anastasia", "REJECTED"))),
    Plan("C", (("gerd", "OPEN"), ("gerd", "CANCELLED"))),
    Plan("D", (("gerd", "CANCELLED"),)),
)


class Report:
    """Collects both halves and keeps them apart."""

    def __init__(self) -> None:
        self.deny: list[dict[str, Any]] = []
        self.allow: list[dict[str, Any]] = []
        self.covered: dict[str, set[tuple[str, str]]] = {"TASK": set(), "HANDOFF": set()}
        self.blocked: str | None = None

    def record_denial(self, *, kind: str, identity: str, current: str, target: str,
                      observed: str, status: int | None, detail: str | None) -> None:
        self.deny.append({
            "kind": kind, "identity": identity, "from": current, "to": target,
            "predicted": "DENY", "observed": observed,
            "status": status, "detail": detail,
            "result": "PASS" if observed == "DENY" else "FAIL",
        })

    def record_allowance(self, *, kind: str, record_id: str, identity: str,
                         current: str, target: str, ok: bool,
                         status: int | None = None, detail: str | None = None) -> None:
        if ok:
            self.covered[kind].add((current, target))
        self.allow.append({
            "kind": kind, "record": record_id, "identity": identity,
            "from": current, "to": target,
            "predicted": "ALLOW", "observed": "ALLOW" if ok else "DENY",
            "status": status, "detail": detail,
            "result": "PASS" if ok else "FAIL",
        })

    def uncovered(self) -> dict[str, list[list[str]]]:
        missing = {
            "TASK": bus_rules.allowed_pairs(bus_rules.TASK_RULES) - self.covered["TASK"],
            "HANDOFF": bus_rules.allowed_pairs(bus_rules.HANDOFF_RULES) - self.covered["HANDOFF"],
        }
        return {kind: sorted([list(p) for p in pairs]) for kind, pairs in missing.items() if pairs}


def _classify_denial(kind: str, error: bus_client.BusError) -> str:
    """DENY only for the exact refusal the migration raises."""
    detail, status = DENIAL_EXPECTED[kind]
    return "DENY" if error.detail == detail and error.status == status else "WRONG_REASON"


def probe_task_denials(clients, task_id: str, current: str, creator_id: str,
                       owner_id: str, run_id: str, report: Report) -> None:
    """Attempt every denied task transition from the current state."""
    for name, client in clients.items():
        identity = IDENTITY_OF[name]
        for target in bus_rules.TASK_STATUSES:
            if target == current:
                continue  # answered as an idempotency conflict, not a permission
            if bus_rules.may_transition_task(
                identity, creator_id=creator_id, owner_id=owner_id,
                current=current, target=target,
            ):
                continue  # would mutate; the allow half covers it
            try:
                client.transition_task(
                    task_id, new_status=target,
                    request_id=f"CONTRACT-{run_id}-T-{identity}-{current}-{target}",
                    # Supplied so a refusal can only be about permissions. The
                    # migration checks evidence after the permission check, so
                    # this changes nothing - it removes an argument, not a risk.
                    completion_evidence="Vertragstest." if target == "DONE" else None,
                )
                report.record_denial(kind="TASK", identity=identity, current=current,
                                     target=target, observed="ALLOW", status=None,
                                     detail=None)
            except bus_client.BusError as error:
                report.record_denial(
                    kind="TASK", identity=identity, current=current, target=target,
                    observed=_classify_denial("TASK", error),
                    status=error.status, detail=error.detail,
                )


def probe_handoff_denials(clients, handoff_id: str, current: str, sender_id: str,
                          recipient_id: str, run_id: str, report: Report) -> None:
    for name, client in clients.items():
        identity = IDENTITY_OF[name]
        for target in bus_rules.HANDOFF_STATUSES:
            if target == current:
                continue
            if bus_rules.may_transition_handoff(
                identity, sender_id=sender_id, recipient_id=recipient_id,
                current=current, target=target,
            ):
                continue
            try:
                client.transition_handoff(
                    handoff_id, new_status=target,
                    request_id=f"CONTRACT-{run_id}-H-{identity}-{current}-{target}",
                    response_note="Vertragstest." if target == "REJECTED" else None,
                )
                report.record_denial(kind="HANDOFF", identity=identity, current=current,
                                     target=target, observed="ALLOW", status=None,
                                     detail=None)
            except bus_client.BusError as error:
                report.record_denial(
                    kind="HANDOFF", identity=identity, current=current, target=target,
                    observed=_classify_denial("HANDOFF", error),
                    status=error.status, detail=error.detail,
                )


def _walk_task(clients, plan: Plan, run_id: str, source_ref: str,
               report: Report, probed: set[str]) -> str | None:
    task_id = f"ENG-CONTRACT-{run_id}-{plan.key}"
    try:
        clients["karl"].create_task(
            task_id=task_id, owner_id=GERD,
            title=f"Vertragstest der Uebergangsregeln ({plan.key})",
            expected_output="Regelpruefung; keine fachliche Arbeit.",
            source_ref=source_ref,
            request_id=f"CONTRACT-{run_id}-{plan.key}-CREATE",
            idempotency_key=f"IDEM-CONTRACT-{run_id}-T{plan.key}",
        )
    except bus_client.BusError as error:
        report.record_allowance(kind="TASK", record_id=task_id, identity=KARL,
                                current="-", target="PENDING", ok=False,
                                status=error.status, detail=error.detail)
        return None

    current = "PENDING"
    if current not in probed:
        probed.add(current)
        probe_task_denials(clients, task_id, current, KARL, GERD, run_id, report)

    for actor, target in plan.steps:
        identity = IDENTITY_OF[actor]
        # The walk is checked against the table too. A step the table calls
        # denied is a bug in this plan or in the transcription; either way it
        # must be loud rather than silently skipped.
        if not bus_rules.may_transition_task(
            identity, creator_id=KARL, owner_id=GERD, current=current, target=target
        ):
            report.record_allowance(kind="TASK", record_id=task_id, identity=identity,
                                    current=current, target=target, ok=False,
                                    detail="PLAN_CONTRADICTS_TABLE")
            return current
        try:
            clients[actor].transition_task(
                task_id, new_status=target,
                request_id=f"CONTRACT-{run_id}-{plan.key}-{current}-{target}",
                completion_evidence=(
                    f"Vertragstest {run_id}: nur Regelpruefung, keine fachliche Arbeit."
                    if target == "DONE" else None
                ),
            )
        except bus_client.BusError as error:
            report.record_allowance(kind="TASK", record_id=task_id, identity=identity,
                                    current=current, target=target, ok=False,
                                    status=error.status, detail=error.detail)
            return current
        report.record_allowance(kind="TASK", record_id=task_id, identity=identity,
                                current=current, target=target, ok=True)
        current = target
        if current not in probed:
            probed.add(current)
            probe_task_denials(clients, task_id, current, KARL, GERD, run_id, report)
    return current


def _walk_handoff(clients, plan: Plan, run_id: str, source_ref: str,
                  report: Report, probed: set[str], task_ref: str) -> str | None:
    handoff_id = f"HO-CONTRACT-{run_id}-{plan.key}"
    try:
        clients["gerd"].create_handoff(
            handoff_id=handoff_id, recipient_id=ANASTASIA,
            input_summary=f"Vertragstest der Uebergangsregeln ({plan.key}).",
            expected_output="Regelpruefung.",
            source_ref=source_ref, task_ref=task_ref,
            request_id=f"CONTRACT-{run_id}-H{plan.key}-CREATE",
            idempotency_key=f"IDEM-CONTRACT-{run_id}-H{plan.key}",
        )
    except bus_client.BusError as error:
        report.record_allowance(kind="HANDOFF", record_id=handoff_id, identity=GERD,
                                current="-", target="PENDING", ok=False,
                                status=error.status, detail=error.detail)
        return None

    current = "PENDING"
    if current not in probed:
        probed.add(current)
        probe_handoff_denials(clients, handoff_id, current, GERD, ANASTASIA, run_id, report)

    for actor, target in plan.steps:
        identity = IDENTITY_OF[actor]
        if not bus_rules.may_transition_handoff(
            identity, sender_id=GERD, recipient_id=ANASTASIA,
            current=current, target=target,
        ):
            report.record_allowance(kind="HANDOFF", record_id=handoff_id,
                                    identity=identity, current=current, target=target,
                                    ok=False, detail="PLAN_CONTRADICTS_TABLE")
            return current
        try:
            clients[actor].transition_handoff(
                handoff_id, new_status=target,
                request_id=f"CONTRACT-{run_id}-H{plan.key}-{current}-{target}",
                response_note="Vertragstest." if target == "REJECTED" else None,
            )
        except bus_client.BusError as error:
            report.record_allowance(kind="HANDOFF", record_id=handoff_id,
                                    identity=identity, current=current, target=target,
                                    ok=False, status=error.status, detail=error.detail)
            return current
        report.record_allowance(kind="HANDOFF", record_id=handoff_id, identity=identity,
                                current=current, target=target, ok=True)
        current = target
        if current not in probed:
            probed.add(current)
            probe_handoff_denials(clients, handoff_id, current, GERD, ANASTASIA,
                                  run_id, report)
    return current


def run_contract_test(clients: dict[str, Any], *, run_id: str,
                      source_ref: str = "DEC-027/ENG-008") -> dict[str, Any]:
    report = Report()

    status = clients["karl"].status()
    if status.get("channel_status") not in {"TESTING", "ACTIVE"}:
        return {"result": "BLOCKED", "reason": "CONTRACT_CHANNEL_NOT_OPEN",
                "channel_status": status.get("channel_status")}

    task_states_probed: set[str] = set()
    handoff_states_probed: set[str] = set()

    for plan in TASK_PLANS:
        _walk_task(clients, plan, run_id, source_ref, report, task_states_probed)

    anchor = f"ENG-CONTRACT-{run_id}-A"
    for plan in HANDOFF_PLANS:
        _walk_handoff(clients, plan, run_id, source_ref, report,
                      handoff_states_probed, anchor)

    return _summarise(report, run_id)


def _summarise(report: Report, run_id: str) -> dict[str, Any]:
    deny_failed = [r for r in report.deny if r["result"] == "FAIL"]
    allow_failed = [r for r in report.allow if r["result"] == "FAIL"]
    uncovered = report.uncovered()

    return {
        "result": "PASS" if not (deny_failed or allow_failed or uncovered) else "FAIL",
        "run_id": run_id,
        "deny": {
            "checked": len(report.deny),
            "matched": len(report.deny) - len(deny_failed),
            # Split out on purpose: a wrongly permitted transition and a
            # refusal for the wrong reason are different defects.
            "wrongly_allowed": sum(1 for r in deny_failed if r["observed"] == "ALLOW"),
            "wrong_reason": sum(1 for r in deny_failed if r["observed"] == "WRONG_REASON"),
        },
        "allow": {
            "checked": len(report.allow),
            "matched": len(report.allow) - len(allow_failed),
            "pairs_covered": {
                "TASK": f"{len(report.covered['TASK'])}/"
                        f"{len(bus_rules.allowed_pairs(bus_rules.TASK_RULES))}",
                "HANDOFF": f"{len(report.covered['HANDOFF'])}/"
                           f"{len(bus_rules.allowed_pairs(bus_rules.HANDOFF_RULES))}",
            },
        },
        "uncovered_allow": uncovered,
        # A full transcript would be hundreds of lines; only divergences are
        # interesting, and a divergence is exactly what this test exists for.
        "divergences": deny_failed + allow_failed,
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
