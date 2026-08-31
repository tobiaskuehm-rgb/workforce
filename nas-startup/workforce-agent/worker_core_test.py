"""Integrated runtime test: the real worker, a real state file, real restarts.

Review finding G-015. `core_roundtrip.py` drives three bus clients directly and
proves the *bus* lifecycle - task and handoff semantics, permissions, order,
idempotency. It touches neither `agent_worker.py` nor `state_store.py`, so it
says nothing about the runtime `ENG-008` actually asks for. This does.

What runs here is the real thing: `agent_worker.poll_once()`, the real
`AgentStateStore` on a real file, the real data boundary, the real budget. The
only stand-in is the model, and that is on purpose - `DEC-027` and `ENG-008`
forbid an external paid service, and this gate is about the runtime, not about
answer quality. The echo provider is the requirement, not a shortcut.

## The four scenarios

  A  happy path        answered, acknowledged, DONE
  C  crash before ACK   the reply is on the bus, the acknowledgement fails, the
                        process restarts and resumes *without asking the model
                        again* - proven by a provider that raises if called
  B  retryable failure  two dropped replies, then success - and exactly one
                        reply on the bus at the end
  D  exhaustion         replies keep failing past max_attempts, and then the
                        final notice fails too. The run that triggered
                        EXHAUSTED is the one that dies, which is the case
                        review finding G-012 was about: a later run has to
                        pick it up, or the message stays DELIVERED forever.
  F  forbidden route   the bus refuses a message the agent must never be able
                        to send. Asked of the bus directly, because the whole
                        safety argument rests on that refusal - and because
                        without it the denial audit of this run would be empty.
  E  lost state volume  the state file is deleted between two runs. The store
                        can no longer prevent anything, so the worker asks the
                        model again - and the *bus* has to be what keeps the
                        answer single, through the idempotency key derived
                        from the inbound message id.

Scenario E was added after the first version of the suite passed a deliberately
broken, non-idempotent bus. It passed because with a working state file the
worker never sends twice at all, so bus idempotency was never reached. The
exactly-once property in A to D rests on the state store; E is what shows the
second line of defence actually holds when the first one is gone. Worth writing
down, because it also names the real cost of losing that volume: one repeated
model call per message in flight, not a lost or duplicated answer.

A and C run first, because the restart between them has to happen while B and
D do not yet exist - otherwise the run after the restart would have to ask the
model for them and the forbidden-provider check would be meaningless.

## How the failures are injected, and why that is honest

A retryable failure cannot be ordered from the real bus, so it is injected in a
client wrapper. The wrapper raises **before** delegating: the request never
reaches the bus, which is what a dropped connection looks like. It never
pretends the bus refused something it accepted, and every drop is listed in the
transcript - a test that injects faults silently is one whose result cannot be
read.

Every assertion about what is on the bus is answered by the bus, not by local
bookkeeping. That is the whole point: local state claiming success proves
nothing about the record of truth.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import agent_worker
import budget as budget_module
import bus_client
import providers
import state_store

# Enough passes for D: three ordinary attempts, the exhaustion transition, the
# dropped final notice, and the run that finally delivers it. Two spare so a
# small change in the retry arithmetic shows up as a failing check rather than
# as a hang.
MAX_PASSES = 8


class InjectedFailure(bus_client.BusError):
    """A transport failure that never reached the bus.

    A distinct type so a reader can tell an injected fault from a real one, and
    so the wrapper can never be mistaken for the bus having refused something.
    """


@dataclass
class FaultInjectingClient:
    """Wraps a bus client and drops specific calls before they are sent."""

    inner: Any
    fail_reply_for: dict[str, int] = field(default_factory=dict)
    fail_ack_for: dict[str, int] = field(default_factory=dict)
    dropped: list[dict[str, str]] = field(default_factory=list)

    def __getattr__(self, name: str) -> Any:
        # status(), inbox() and everything else go straight through.
        return getattr(self.inner, name)

    def send_message(self, **kwargs: Any) -> dict[str, Any]:
        # Keyed on the message being answered, so one scenario's faults cannot
        # bleed into another's.
        parent = str(kwargs.get("parent_message_id") or "")
        remaining = self.fail_reply_for.get(parent, 0)
        if remaining > 0:
            self.fail_reply_for[parent] = remaining - 1
            self.dropped.append({"call": "send_message", "message_id": parent})
            raise InjectedFailure("INJECTED_REPLY_TRANSPORT_FAILURE")
        return self.inner.send_message(**kwargs)

    def acknowledge(self, message_id: str, **kwargs: Any) -> dict[str, Any]:
        remaining = self.fail_ack_for.get(message_id, 0)
        if remaining > 0:
            self.fail_ack_for[message_id] = remaining - 1
            self.dropped.append({"call": "acknowledge", "message_id": message_id})
            raise InjectedFailure("INJECTED_ACK_TRANSPORT_FAILURE")
        return self.inner.acknowledge(message_id, **kwargs)


class ForbiddenProvider:
    """Fails loudly if the model is asked at all.

    Used for the run after the restart. The point of the state file is that a
    resumed message does not pay for the model twice; a provider that quietly
    answered again would let that regression through unnoticed.
    """

    name = "forbidden"
    is_paid = False

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, system: str, content: str) -> providers.Reply:
        self.calls += 1
        raise providers.ProviderError("PROVIDER_CALLED_AFTER_RESUME")


class _CountingProvider:
    """Delegates, and counts. Used where a second model call is the finding."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.calls = 0
        self.name = getattr(inner, "name", "counting")
        self.is_paid = getattr(inner, "is_paid", True)

    def complete(self, *, system: str, content: str) -> providers.Reply:
        self.calls += 1
        return self.inner.complete(system=system, content=content)


def _discard_state(state_path: str | Path) -> None:
    """Delete the state file the way a lost volume would.

    The WAL and shared-memory sidecars go too - leaving them behind would
    simulate a corrupted volume rather than an absent one, which is a different
    scenario and not the one being tested.
    """
    base = Path(state_path)
    for path in (base, Path(f"{base}-wal"), Path(f"{base}-shm")):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@dataclass
class Harness:
    """What the runner needs from the outside world.

    Two implementations: the integrated fake in test_worker_core_test.py, and
    the live one in main() below. The runner cannot tell them apart, which is
    what makes the local run meaningful evidence for the NAS run.
    """

    agent_client: Any
    send_request: Callable[..., str]
    bus_messages: Callable[[], list[dict[str, Any]]]
    state_path: str | Path
    agent_identity: str = "AGENT-ENG-001"


class Transcript:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, name: str, condition: bool, **fields: Any) -> bool:
        self.checks.append(
            {"check": name, "result": "PASS" if condition else "FAIL", **fields}
        )
        return bool(condition)

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [c for c in self.checks if c["result"] == "FAIL"]


def replies_to(messages: list[dict[str, Any]], message_id: str) -> list[dict[str, Any]]:
    """Every message on the bus that answers one inbound message."""
    return [
        m for m in messages
        if str(m.get("parent_message_id") or "") == message_id
    ]


def state_of(store: state_store.AgentStateStore, message_id: str) -> dict[str, Any] | None:
    for row in store.snapshot():
        if row.get("message_id") == message_id:
            return row
    return None


def result_for(results: list[dict[str, Any]], message_id: str) -> dict[str, Any] | None:
    for item in results:
        if item.get("message_id") == message_id:
            return item
    return None


def _fresh_budget() -> budget_module.Budget:
    # One budget per container run, as in production. Generous on purpose: the
    # ceilings have their own suite, and a budget stop here would mask the
    # behaviour under test.
    return budget_module.Budget(max_messages=50, max_provider_calls=50)


def _request(harness: Harness, run_id: str, name: str, body: str) -> str:
    """Send one request, or get the same message id back if it exists.

    Phase two re-sends with the same idempotency key rather than being handed
    the ids from phase one. That is not a trick: it is what makes the split
    survive a real container restart, where nothing is passed between the two
    processes except the bus and the state volume.
    """
    return harness.send_request(
        subject=f"Worker-Core {run_id} {name}",
        body=body,
        key=f"{run_id}-{name}",
    )


BODIES = {
    "A": "Bitte kurz fachlich einordnen. Szenario A, Gutfall.",
    "B": "Bitte kurz fachlich einordnen. Szenario B, zwei Fehlversuche.",
    "C": "Bitte kurz fachlich einordnen. Szenario C, Absturz vor Bestaetigung.",
    "D": "Bitte kurz fachlich einordnen. Szenario D, Erschoepfung.",
    "E": "Bitte kurz fachlich einordnen. Szenario E, verlorener Zustand.",
}


def _phase_one(harness: Harness, transcript: Transcript, client: FaultInjectingClient,
               ids: dict[str, str], store, run_id: str) -> None:
    """Send A and C, run one pass, and leave C mid-flight for phase two."""
    ids["A"] = _request(harness, run_id, "A", BODIES["A"])
    ids["C"] = _request(harness, run_id, "C", BODIES["C"])
    client.fail_ack_for[ids["C"]] = 1

    first = store()
    echo = providers.EchoProvider()
    pass_one = agent_worker.poll_once(client, echo, state=first,
                                      budget=_fresh_budget())

    transcript.check("A_answered_in_first_pass",
                     (result_for(pass_one, ids["A"]) or {}).get("result") == "ANSWERED",
                     message_id=ids["A"])
    transcript.check("A_state_done",
                     (state_of(first, ids["A"]) or {}).get("state") == "DONE")
    transcript.check("C_acknowledgement_failed",
                     (result_for(pass_one, ids["C"]) or {}).get("result") == "ACK_FAILED",
                     message_id=ids["C"])
    transcript.check("C_state_replied_not_done",
                     (state_of(first, ids["C"]) or {}).get("state") == "REPLIED")

    on_bus = harness.bus_messages()
    transcript.check("C_reply_is_already_on_the_bus",
                     len(replies_to(on_bus, ids["C"])) == 1,
                     replies=len(replies_to(on_bus, ids["C"])))
    # The bus is the record of truth: an unacknowledged message must still be
    # DELIVERED there, or no later run would ever see it (finding G-001).
    inbox = {m["message_id"]: m for m in client.inbox()}
    transcript.check("C_still_delivered_in_the_bus",
                     inbox.get(ids["C"], {}).get("delivery_status") == "DELIVERED")

    first.close()  # the crash

    # Nothing is handed to phase two but the bus and the state volume. The
    # reply id it needs is in the state file, where a restarted process finds
    # it - which is the property under test, not a convenience.


def _phase_two(harness: Harness, transcript: Transcript, client: FaultInjectingClient,
               ids: dict[str, str], store, run_id: str, max_attempts: int) -> int:
    """Resume C after the restart, then run B, D and E. Returns the pass count."""
    ids.setdefault("A", _request(harness, run_id, "A", BODIES["A"]))
    ids.setdefault("C", _request(harness, run_id, "C", BODIES["C"]))

    # --- The restart ------------------------------------------------------
    # A new store over the same file is what a new process gets. On the NAS
    # phase two runs in its own container, so the restart is a real one.
    second = store()
    reply_before_restart = (state_of(second, ids["C"]) or {}).get("reply_message_id")
    transcript.check("the_state_volume_survived_the_restart",
                     reply_before_restart is not None,
                     reply_message_id=reply_before_restart)
    forbidden = ForbiddenProvider()
    pass_two = agent_worker.poll_once(client, forbidden, state=second,
                                      budget=_fresh_budget())

    transcript.check("restart_did_not_ask_the_model", forbidden.calls == 0,
                     provider_calls=forbidden.calls)
    transcript.check("C_finished_after_restart",
                     (state_of(second, ids["C"]) or {}).get("state") == "DONE")
    transcript.check("C_kept_its_reply_id",
                     (state_of(second, ids["C"]) or {}).get("reply_message_id")
                     == reply_before_restart,
                     reply_message_id=reply_before_restart)
    transcript.check("A_was_not_handled_twice",
                     result_for(pass_two, ids["A"]) is None,
                     detail="A is ACCEPTED in the bus and no longer pending")

    on_bus = harness.bus_messages()
    transcript.check("C_has_exactly_one_reply_after_restart",
                     len(replies_to(on_bus, ids["C"])) == 1,
                     replies=len(replies_to(on_bus, ids["C"])))
    second.close()

    # --- Phase 2: B and D -------------------------------------------------
    ids["B"] = _request(harness, run_id, "B", BODIES["B"])
    ids["D"] = _request(harness, run_id, "D", BODIES["D"])
    client.fail_reply_for[ids["B"]] = 2
    # Three ordinary attempts plus the first exhaustion notice. Dropping the
    # notice as well is the G-012 case: the run that consumed the transition
    # into EXHAUSTED dies before the notice is out.
    client.fail_reply_for[ids["D"]] = max_attempts + 1

    third = store()
    passes: list[list[dict[str, Any]]] = []
    for _ in range(MAX_PASSES):
        passes.append(agent_worker.poll_once(client, providers.EchoProvider(),
                                             state=third, budget=_fresh_budget()))
        done = {
            name: (state_of(third, ids[name]) or {}).get("state")
            for name in ("B", "D")
        }
        if all(value == "DONE" for value in done.values()):
            break

    transcript.check("B_finished", (state_of(third, ids["B"]) or {}).get("state") == "DONE",
                     attempts=(state_of(third, ids["B"]) or {}).get("attempts"))
    transcript.check("B_took_three_attempts",
                     (state_of(third, ids["B"]) or {}).get("attempts") == 3)
    transcript.check("D_finished_after_exhaustion",
                     (state_of(third, ids["D"]) or {}).get("state") == "DONE",
                     attempts=(state_of(third, ids["D"]) or {}).get("attempts"))
    transcript.check("D_went_past_the_attempt_ceiling",
                     (state_of(third, ids["D"]) or {}).get("attempts", 0) > max_attempts)

    on_bus = harness.bus_messages()
    for name in ("A", "B", "C", "D"):
        transcript.check(
            f"{name}_has_exactly_one_reply",
            len(replies_to(on_bus, ids[name])) == 1,
            replies=len(replies_to(on_bus, ids[name])),
        )

    inbox_ids = {m["message_id"] for m in client.inbox()
                 if m.get("delivery_status") == "DELIVERED"}
    transcript.check("nothing_is_left_pending", not (set(ids.values()) & inbox_ids),
                     still_pending=sorted(set(ids.values()) & inbox_ids))
    third.close()

    # --- Phase 3: E, the lost state volume --------------------------------
    ids["E"] = _request(harness, run_id, "E", BODIES["E"])
    client.fail_ack_for[ids["E"]] = 1

    counting = _CountingProvider(providers.EchoProvider())
    fourth = store()
    agent_worker.poll_once(client, counting, state=fourth, budget=_fresh_budget())
    transcript.check("E_reply_out_acknowledgement_missing",
                     (state_of(fourth, ids["E"]) or {}).get("state") == "REPLIED")
    reply_before_loss = (state_of(fourth, ids["E"]) or {}).get("reply_message_id")
    fourth.close()

    _discard_state(harness.state_path)

    fifth = store()
    transcript.check("the_state_volume_is_really_gone",
                     state_of(fifth, ids["E"]) is None)
    agent_worker.poll_once(client, counting, state=fifth, budget=_fresh_budget())

    # The store cannot help here - it has forgotten everything. What keeps the
    # answer single is the bus: the idempotency key is derived from the inbound
    # message id, so the second send returns the first reply instead of a new
    # one.
    transcript.check("E_finished_without_the_old_state",
                     (state_of(fifth, ids["E"]) or {}).get("state") == "DONE")
    on_bus = harness.bus_messages()
    transcript.check("E_has_exactly_one_reply_despite_the_lost_state",
                     len(replies_to(on_bus, ids["E"])) == 1,
                     replies=len(replies_to(on_bus, ids["E"])))
    transcript.check("E_kept_the_same_reply_id",
                     (state_of(fifth, ids["E"]) or {}).get("reply_message_id")
                     == reply_before_loss,
                     reply_message_id=reply_before_loss)
    # Named, not hidden: losing the volume costs a repeated model call. That is
    # the price the state store exists to avoid, and it is worth seeing.
    transcript.check("a_lost_volume_costs_one_repeated_model_call",
                     counting.calls == 2, provider_calls=counting.calls)
    fifth.close()

    # --- F: the route the model must never be able to change ---------------
    # Not a worker path - the worker takes the recipient from the bus record
    # and never from model output. This asks the bus directly whether it would
    # refuse an unauthorised route at all, because the entire safety argument
    # for pointing an agent at untrusted content rests on that refusal. A
    # self-route is denied by the schema itself, independently of whatever the
    # allowlist happens to contain today.
    #
    # It also gives the denial audit something real to hold: the injected
    # transport faults never reach the bus, so without this the negative half
    # of the audit would be empty (review finding G-018).
    try:
        client.inner.send_message(
            recipient_id=harness.agent_identity,
            subject=f"Worker-Core {run_id} F",
            body="Negativfall: Route auf sich selbst.",
            parent_message_id=None,
            request_id=f"WORKERCORE-{run_id}-F-SELFROUTE",
            idempotency_key=f"IDEM-WORKERCORE-{run_id}-F",
        )
        transcript.check("self_route_is_refused", False,
                         detail="the bus accepted a message from the agent to itself")
    except bus_client.BusError as error:
        transcript.check("self_route_is_refused",
                         error.detail == "BUS_SELF_ROUTE_DENIED",
                         detail=error.detail, status=error.status)

    # --- The single-writer guard ------------------------------------------
    # Two workers sharing one state file must not both take the same message.
    # Checked against the real store, not against the description of it.
    holder = store()
    rival = store()
    probe = f"MSG-PROBE-{run_id}"
    first_claim = holder.claim(probe)
    second_claim = rival.claim(probe)
    transcript.check("a_second_worker_cannot_steal_a_live_claim",
                     first_claim is not None and second_claim is None)
    holder.close()
    rival.close()
    return len(passes) + 3


def run_worker_core_test(harness: Harness, *, run_id: str, max_attempts: int = 3,
                         phase: str = "all") -> dict[str, Any]:
    """Run the gate. `phase` is "1", "2" or "all".

    Split into two so the NAS run can put a genuine container restart between
    them: phase one leaves C answered but unacknowledged, phase two picks it up
    in a new process over the same state volume. "all" runs both back to back,
    which is what the local suite does - there the restart is a fresh store
    over the same file, which is what a new process gets.
    """
    if phase not in {"1", "2", "all"}:
        raise ValueError("WORKER_CORE_PHASE_INVALID")

    transcript = Transcript()
    client = FaultInjectingClient(harness.agent_client)
    ids: dict[str, str] = {}

    def store() -> state_store.AgentStateStore:
        return state_store.AgentStateStore(harness.state_path,
                                           max_attempts=max_attempts)

    passes = 1
    if phase in {"1", "all"}:
        _phase_one(harness, transcript, client, ids, store, run_id)
    if phase in {"2", "all"}:
        passes = _phase_two(harness, transcript, client, ids, store, run_id,
                            max_attempts)

    return {
        "result": "PASS" if not transcript.failed else "FAIL",
        "run_id": run_id,
        "phase": phase,
        "message_ids": ids,
        "checks_total": len(transcript.checks),
        "checks_failed": len(transcript.failed),
        "injected_faults": client.dropped,
        "passes": passes,
        "divergences": transcript.failed,
    }


def main() -> int:
    """Live run against the real bus. Needs two credentials and a state volume."""
    try:
        base_url = bus_client.validate_base_url(os.environ.get("CORE_BUS_BASE_URL", ""))
        run_id = os.environ["CORE_RUN_ID"].strip()
        state_path = os.environ.get("AGENT_STATE_PATH",
                                    "/var/lib/startup-agent/worker_core.sqlite3")
        agent_identity = os.environ.get("AGENT_IDENTITY", "AGENT-ENG-001")
        context = ssl.create_default_context()
        agent = bus_client.BusClient(
            base_url=base_url,
            token=bus_client.read_token(os.environ["AGENT_BUS_TOKEN_FILE"]),
            context=context,
        )
        requester = bus_client.BusClient(
            base_url=base_url,
            token=bus_client.read_token(os.environ["KARL_BUS_TOKEN_FILE"]),
            context=context,
        )
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": str(exc)}))
        return 2

    task_ref = os.environ.get("WORKER_CORE_TASK_REF") or None

    def send_request(*, subject: str, body: str, key: str) -> str:
        sent = requester.send_message(
            recipient_id=agent_identity,
            subject=subject,
            body=body,
            parent_message_id=None,
            task_ref=task_ref,
            request_id=f"WORKERCORE-{key}",
            idempotency_key=f"IDEM-WORKERCORE-{key}",
        )
        return str(sent["message_id"])

    def bus_messages() -> list[dict[str, Any]]:
        # The replies come back to the requester, so its inbox is where they
        # are counted - read from the bus, never from local bookkeeping.
        return requester.inbox(limit=100)

    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    # "1" and "2" put a real container restart between the halves; "all"
    # runs both in one process.
    phase = os.environ.get("WORKER_CORE_PHASE", "all").strip() or "all"
    result = run_worker_core_test(
        Harness(agent_client=agent, send_request=send_request,
                bus_messages=bus_messages, state_path=state_path,
                agent_identity=agent_identity),
        run_id=run_id,
        phase=phase,
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
