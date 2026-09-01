import hashlib
import hmac
import ipaddress
import json
import os
import pathlib
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Literal, NamedTuple

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

def _api_key() -> str:
    """The API key, from a file - never from the environment.

    Review finding G-035: the API service loaded the whole startup.env, so the
    owner name and the owner's superuser password sat in the container. That
    `app.py` no longer reads them is not protection: a compromised process can
    read its own environment and connect as the owner directly, around every
    grant migration 007 makes.

    So the service gets no startup.env at all, and the two things it does need
    come from their own files. An environment variable would also be readable
    in `docker inspect`, which is the same argument that moved the bus tokens
    into files (G-010).
    """
    path = os.environ.get("WORKFORCE_API_KEY_FILE", "").strip()
    if path:
        key = pathlib.Path(path).read_text(encoding="utf-8").strip()
        if not key:
            raise RuntimeError(f"WORKFORCE_API_KEY_FILE_EMPTY: {path}")
        return key
    # Only for the local test suite, which has no file to mount. On the NAS the
    # compose file always sets WORKFORCE_API_KEY_FILE.
    key = os.environ.get("WORKFORCE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "WORKFORCE_API_KEY_FILE_REQUIRED: der Schluessel kommt aus einer "
            "Datei, nicht aus startup.env"
        )
    return key


API_KEY = _api_key()
BUS_PROJECT_ID = "START-UP"
BUS_REQUIRE_HTTPS = os.environ.get("BUS_REQUIRE_HTTPS", "true").lower() not in {"0", "false", "no"}
BUS_TRUSTED_PROXY_CIDRS = tuple(
    item.strip()
    for item in os.environ.get("BUS_TRUSTED_PROXY_CIDRS", "").split(",")
    if item.strip()
)


def database_login() -> tuple[str, str]:
    """The account the API connects with - never the owner.

    Review finding G-035: migration 007 created a least-privilege role, and
    the stack went on connecting as `workforce_app`, which owns the schema,
    every table and every function. The separation existed on paper only.

    Fail-closed on purpose: no fallback to POSTGRES_USER. A missing variable
    used to mean "use the owner", which is the one outcome that must not
    happen silently. The password comes from a file, like every other secret
    in this project - an environment variable is readable in `docker inspect`.
    """
    user = os.environ.get("WORKFORCE_DB_USER", "").strip()
    if not user:
        raise RuntimeError(
            "WORKFORCE_DB_USER_REQUIRED: die API verbindet sich nicht mehr als "
            "Eigentuemer; setze WORKFORCE_DB_USER=workforce_api"
        )
    path = os.environ.get("WORKFORCE_DB_PASSWORD_FILE", "").strip()
    if not path:
        raise RuntimeError(
            "WORKFORCE_DB_PASSWORD_FILE_REQUIRED: Passwort nur aus einer Datei, "
            "nie aus der Umgebung"
        )
    password = pathlib.Path(path).read_text(encoding="utf-8").strip()
    if not password:
        raise RuntimeError(f"WORKFORCE_DB_PASSWORD_FILE_EMPTY: {path}")
    return user, password


def connection():
    user, password = database_login()
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ["POSTGRES_DB"],
        user=user,
        password=password,
        connect_timeout=3,
    )


def rows_as_dicts(cursor) -> list[dict]:
    columns = [column.name for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def row_as_dict(cursor) -> dict:
    columns = [column.name for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="BUS_RECORD_NOT_FOUND")
    return dict(zip(columns, row, strict=True))


def bus_error(exc: psycopg.Error) -> HTTPException:
    code = exc.sqlstate
    message = getattr(exc.diag, "message_primary", None) or "BUS_DATABASE_ERROR"
    # Both prefixes, not just BUS_ (review finding G-027). A KNOWLEDGE_ code
    # used to be normalised away into BUS_DATABASE_UNAVAILABLE, so an access
    # refusal reached the caller - and the denial audit - as a database fault.
    # A permission error that looks like an outage is worse than either.
    stable_message = message.startswith(("BUS_", "KNOWLEDGE_")) and all(
        character.isupper() or character.isdigit() or character == "_"
        for character in message
    )

    if not stable_message:
        message = {
            "23505": "BUS_CONFLICT",
            "23514": "BUS_REQUEST_INVALID",
            "23502": "BUS_REQUEST_INVALID",
            "23503": "BUS_REQUEST_INVALID",
        }.get(code, "BUS_DATABASE_UNAVAILABLE")

    if code == "42501":
        http_status = 401 if message in {"BUS_AUTH_FAILED", "KNOWLEDGE_AUTH_FAILED"} else 403
    elif code == "P0002":
        http_status = 404
    elif code in {"23505", "55000"}:
        http_status = 409
    elif code == "22001":
        http_status = 413
    elif code == "54000":
        http_status = 422
    elif code in {"22023", "23514", "23502", "23503"}:
        http_status = 400
    else:
        http_status = 503
        message = "BUS_DATABASE_UNAVAILABLE"

    return HTTPException(status_code=http_status, detail=message)


def trusted_https_proxy(request: Request) -> bool:
    if request.headers.get("x-forwarded-proto", "").lower() != "https":
        return False

    client_host = request.client.host if request.client else ""
    try:
        client_ip = ipaddress.ip_address(client_host)
    except ValueError:
        return False

    if client_ip.is_loopback:
        return True

    for cidr in BUS_TRUSTED_PROXY_CIDRS:
        try:
            if client_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def require_bus_transport(request: Request) -> None:
    if not BUS_REQUIRE_HTTPS:
        return
    if request.url.scheme == "https" or trusted_https_proxy(request):
        return
    raise HTTPException(status_code=503, detail="BUS_HTTPS_REQUIRED")


def require_https_transport(request: Request) -> None:
    """Refuse cleartext for every endpoint that carries a credential.

    The bus already enforced this; the legacy registry endpoints and the web UI
    did not, so WORKFORCE_API_KEY and all document content travelled in the
    clear over the published port 8080 (security review 2026-08-31, F2).

    /health and /db-check deliberately stay reachable over plain HTTP: the
    container healthcheck calls them on loopback without a forwarded-proto
    header, and the documented tokenless network probe relies on them. Neither
    exposes a credential or any content.
    """
    if not BUS_REQUIRE_HTTPS:
        return
    if request.url.scheme == "https" or trusted_https_proxy(request):
        return
    raise HTTPException(status_code=503, detail="HTTPS_REQUIRED")


def require_bus_ready() -> None:
    try:
        with connection() as conn:
            if conn.execute("SELECT to_regclass('workforce.bus_channels')").fetchone()[0] is None:
                raise HTTPException(status_code=503, detail="BUS_MIGRATION_MISSING")
            row = conn.execute(
                "SELECT channel_status FROM workforce.bus_channels WHERE project_id = %s",
                (BUS_PROJECT_ID,),
            ).fetchone()
    except HTTPException:
        raise
    except psycopg.Error as exc:
        raise bus_error(exc) from exc

    if row is None or row[0] not in {"TESTING", "ACTIVE"}:
        raise HTTPException(status_code=503, detail="BUS_CHANNEL_NOT_ACTIVE")


def require_bus_token(
    request: Request,
    authorization: str = Header(default="", alias="Authorization"),
) -> str:
    require_bus_transport(request)
    require_bus_ready()

    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not 32 <= len(token) <= 512:
        raise HTTPException(status_code=401, detail="BUS_BEARER_TOKEN_REQUIRED")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_request_id(
    x_request_id: str = Header(default="", alias="X-Request-ID"),
) -> str:
    value = x_request_id.strip()
    if not 1 <= len(value) <= 128:
        raise HTTPException(status_code=400, detail="BUS_REQUEST_ID_REQUIRED")
    return value


def require_idempotency_key(
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
) -> str:
    value = idempotency_key.strip()
    if not 13 <= len(value) <= 101 or not value.startswith("IDEM-"):
        raise HTTPException(status_code=400, detail="BUS_IDEMPOTENCY_KEY_REQUIRED")
    return value


def require_knowledge_token(
    request: Request,
    authorization: str = Header(default="", alias="Authorization"),
) -> str:
    require_bus_transport(request)
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not 32 <= len(token) <= 512:
        raise HTTPException(status_code=401, detail="KNOWLEDGE_BEARER_TOKEN_REQUIRED")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class BusAudit(NamedTuple):
    """Everything the denial log is allowed to know about one call.

    Identifiers and nothing else: no subject, no body, no note, no token, and
    for knowledge no title and no content. The table's CHECK constraints refuse
    anything wider, so this is a shape, not a promise.
    """

    operation: str
    record_type: str
    token_hash: str
    # The read endpoints carry no X-Request-ID header, so they pass a marker of
    # the form READ:<scope> instead. It is not a request id and does not
    # pretend to be one - it says why there is none.
    request_id: str
    record_key: str | None = None


def record_denial(audit: BusAudit, error: HTTPException) -> None:
    """Write one refused operation to the append-only denial log.

    Review finding G-018: workforce.bus_events only holds successful changes,
    because a refused call rolls its transaction back and takes any audit row
    with it. The write therefore happens here, on a *fresh* connection after
    the failure - which is the only place it can happen at all.

    Never raises. An audit that can turn a clean 403 into a 500 would be worse
    than the gap it closes; a failure to record is reported on stderr and the
    original error travels on untouched.
    """
    try:
        with connection() as conn:
            conn.execute(
                "SELECT workforce.bus_record_denial(%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    BUS_PROJECT_ID,
                    audit.token_hash,
                    audit.request_id,
                    audit.operation,
                    audit.record_type,
                    audit.record_key,
                    str(error.detail),
                    int(error.status_code),
                ),
            )
    except (psycopg.Error, ValueError, TypeError) as exc:
        print(
            f"BUS_DENIAL_AUDIT_FAILED operation={audit.operation} "
            f"request_id={audit.request_id} reason={type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )


def execute_bus_one(sql: str, parameters: tuple, *, audit: BusAudit | None = None) -> dict:
    try:
        with connection() as conn:
            cursor = conn.execute(sql, parameters)
            return row_as_dict(cursor)
    except HTTPException as exc:
        if audit is not None:
            record_denial(audit, exc)
        raise
    except psycopg.Error as exc:
        error = bus_error(exc)
        if audit is not None:
            record_denial(audit, error)
        raise error from exc


def execute_bus_many(sql: str, parameters: tuple,
                     *, audit: BusAudit | None = None) -> list[dict]:
    try:
        with connection() as conn:
            cursor = conn.execute(sql, parameters)
            return rows_as_dicts(cursor)
    except psycopg.Error as exc:
        error = bus_error(exc)
        if audit is not None:
            record_denial(audit, error)
        raise error from exc


# The seven legacy registry tables the API reads and writes. Their definition
# lives in postgres-init/006_legacy_registry_tables.sql; the API only checks
# that they are there.
LEGACY_TABLES = (
    "roles", "workers", "tasks", "activity_log",
    "task_notes", "documents", "document_versions",
)


def verify_database() -> None:
    """Refuse to serve on a database that is not migrated.

    This used to be `initialize_database()`, which created the seven tables
    on every start. That is why the runtime account needed DDL rights and ended up as
    SUPERUSER - and a superuser can disable the append-only triggers the audit
    argument depends on (review finding G-025).

    Checking instead of creating costs one query and turns a silent, powerful
    startup side effect into a loud, powerless one: a missing table now names
    itself and the migration that provides it.
    """
    missing = []
    with connection() as conn:
        for table in LEGACY_TABLES:
            if conn.execute("SELECT to_regclass(%s)", (table,)).fetchone()[0] is None:
                missing.append(table)
    if missing:
        raise RuntimeError(
            "WORKFORCE_LEGACY_TABLES_MISSING: "
            + ", ".join(missing)
            + " - apply postgres-init/006_legacy_registry_tables.sql"
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    verify_database()
    yield


app = FastAPI(title="Workforce Kernel", docs_url=None, redoc_url=None,
              openapi_url=None, lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/bus/"):
        return JSONResponse(status_code=400, content={"detail": "BUS_REQUEST_INVALID"})
    if request.url.path.startswith("/knowledge/"):
        return JSONResponse(status_code=400, content={"detail": "KNOWLEDGE_REQUEST_INVALID"})
    return await request_validation_exception_handler(request, exc)

UI_HTML = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Workforce Kernel</title><style>
:root{font-family:system-ui,sans-serif;color:#172033;background:#f4f6fa}body{margin:0}header{background:#172033;color:white;padding:18px 5vw}main{max-width:1100px;margin:auto;padding:24px}section{background:white;border-radius:12px;padding:18px;margin-bottom:18px;box-shadow:0 2px 12px #17203318}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}input,select,textarea,button{box-sizing:border-box;width:100%;padding:10px;margin:5px 0;border:1px solid #ccd3df;border-radius:7px;font:inherit}button{background:#2563eb;color:white;border:0;cursor:pointer}button.secondary{background:#475569}.item{border-top:1px solid #e5e7eb;padding:10px 0}.muted{color:#64748b;font-size:.9rem}.ok{color:#16803c}.error{color:#b42318}code{word-break:break-all}
</style></head><body><header><h2>Workforce Kernel</h2></header><main>
<section id="login"><h3>Zugang</h3><input id="key" type="password" placeholder="API-Schlüssel aus startup.env"><button onclick="connect()">Verbinden</button><p id="message" class="muted">Der Schlüssel bleibt nur in diesem Browser-Tab.</p></section>
<div id="app" hidden><section><div class="grid"><div><b>Rollen</b><div id="cRoles">0</div></div><div><b>Mitarbeiter/Agenten</b><div id="cWorkers">0</div></div><div><b>Aufgaben</b><div id="cTasks">0</div></div><div><b>Aktivitäten</b><div id="cActivity">0</div></div></div></section>
<div class="grid"><section><h3>Rolle anlegen</h3><input id="roleName" placeholder="Name"><textarea id="roleDesc" placeholder="Beschreibung"></textarea><button onclick="createRole()">Speichern</button></section>
<section><h3>Mitarbeiter/Agent anlegen</h3><input id="workerName" placeholder="Name"><select id="workerKind"><option value="human">Mensch</option><option value="agent">KI-Agent</option></select><select id="workerRole"></select><button onclick="createWorker()">Speichern</button></section>
<section><h3>Aufgabe anlegen</h3><input id="taskTitle" placeholder="Titel"><textarea id="taskDesc" placeholder="Beschreibung"></textarea><select id="taskWorker"></select><button onclick="createTask()">Speichern</button></section></div>
<section><h3>Aufgaben</h3><div id="tasks"></div></section>
<section><h3>Architekturdokumentation</h3><input id="docTitle" value="Systemarchitektur" placeholder="Titel"><textarea id="docContent" rows="10" placeholder="Netzwerk, Synology, Container, Datenbank, API, Sicherheit und Wiederherstellung dokumentieren"></textarea><button onclick="saveDocument()">Dokument speichern</button><div id="documents"></div></section>
<section><h3>Aktivitäten</h3><div id="activities"></div></section></div>
</main><script>
let key=''; const $=id=>document.getElementById(id);
async function api(path,options={}){options.headers={...(options.headers||{}),'X-API-Key':key};if(options.body)options.headers['Content-Type']='application/json';let r=await fetch(path,options);if(!r.ok)throw new Error((await r.json()).detail||r.statusText);return r.json()}
async function connect(){key=$('key').value.trim();try{await refresh();$('login').hidden=true;$('app').hidden=false}catch(e){$('message').className='error';$('message').textContent='Zugriff abgelehnt: '+e.message}}
async function refresh(){let [k,r,w,t,a,d]=await Promise.all([api('/kernel'),api('/roles'),api('/workers'),api('/tasks'),api('/activities'),api('/documents')]);$('cRoles').textContent=k.counts.roles;$('cWorkers').textContent=k.counts.workers;$('cTasks').textContent=k.counts.tasks;$('cActivity').textContent=k.counts.activity_log;$('workerRole').innerHTML='<option value="">Keine Rolle</option>'+r.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('');$('taskWorker').innerHTML='<option value="">Nicht zugewiesen</option>'+w.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('');$('tasks').innerHTML=t.map(x=>`<div class="item"><b>${esc(x.title)}</b> <span class="muted">#${x.id}</span><br><span>${esc(x.description)}</span><select onchange="taskStatus(${x.id},this.value)">${['open','in_progress','blocked','done'].map(s=>`<option ${s===x.status?'selected':''}>${s}</option>`).join('')}</select><textarea id="note-${x.id}" placeholder="Notiz oder Ergebnis"></textarea><button class="secondary" onclick="addNote(${x.id},'note')">Notiz speichern</button><button onclick="addNote(${x.id},'result')">Ergebnis speichern</button><div class="muted">${(x.notes||[]).map(n=>`<p><b>${esc(n.note_type)}:</b> ${esc(n.content)}</p>`).join('')}</div></div>`).join('')||'<span class="muted">Keine Aufgaben</span>';$('documents').innerHTML=d.map(x=>`<div class="item"><b>${esc(x.title)}</b> <span class="muted">Versionen: ${x.version_count}</span><button class="secondary" onclick="loadDocument(${x.id})">Bearbeiten</button></div>`).join('')||'<span class="muted">Noch kein Dokument</span>';$('activities').innerHTML=a.map(x=>`<div class="item"><b>${esc(x.event_type)}</b> · ${esc(x.entity_type)} #${x.entity_id??'-'} <span class="muted">${new Date(x.created_at).toLocaleString()}</span></div>`).join('')||'<span class="muted">Keine Aktivitäten</span>'}
const val=id=>$(id).value.trim(), nullable=id=>val(id)?Number(val(id)):null, esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function createRole(){await api('/roles',{method:'POST',body:JSON.stringify({name:val('roleName'),description:val('roleDesc')})});$('roleName').value='';$('roleDesc').value='';await refresh()}
async function createWorker(){await api('/workers',{method:'POST',body:JSON.stringify({name:val('workerName'),kind:val('workerKind'),role_id:nullable('workerRole')})});$('workerName').value='';await refresh()}
async function createTask(){await api('/tasks',{method:'POST',body:JSON.stringify({title:val('taskTitle'),description:val('taskDesc'),assignee_id:nullable('taskWorker')})});$('taskTitle').value='';$('taskDesc').value='';await refresh()}
async function taskStatus(id,status){await api('/tasks/'+id,{method:'PATCH',body:JSON.stringify({status})});await refresh()}
async function addNote(id,note_type){let content=val('note-'+id);if(!content)return;await api('/tasks/'+id+'/notes',{method:'POST',body:JSON.stringify({note_type,content})});await refresh()}
async function saveDocument(){await api('/documents',{method:'POST',body:JSON.stringify({title:val('docTitle'),content:val('docContent')})});await refresh()}
async function loadDocument(id){let d=await api('/documents/'+id);$('docTitle').value=d.title;$('docContent').value=d.content;window.scrollTo({top:$('docTitle').offsetTop-80,behavior:'smooth'})}
</script></body></html>"""


def require_api_key(request: Request, x_api_key: str = Header(default="")) -> None:
    require_https_transport(request)
    if not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class WorkerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    kind: Literal["human", "agent"]
    role_id: int | None = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    assignee_id: int | None = None


class TaskStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "blocked", "done"]


class TaskNoteCreate(BaseModel):
    note_type: Literal["note", "result"]
    content: str = Field(min_length=1, max_length=10000)


class DocumentSave(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=100000)


class BusModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BusMessageCreate(BusModel):
    recipient_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=32000)
    action_class: Literal[
        "INTERNAL_COMMUNICATION",
        "INTERNAL_REVIEW",
        "INTERNAL_STATUS",
        "INTERNAL_COORDINATION",
    ] = "INTERNAL_COMMUNICATION"
    confidentiality: Literal["PROJECT_INTERNAL", "NEED_TO_KNOW"] = "NEED_TO_KNOW"
    task_ref: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    handoff_ref: str | None = Field(default=None, pattern=r"^HO-[A-Z0-9-]{3,63}$")
    parent_message_id: str | None = Field(default=None, pattern=r"^MSG-[A-Z0-9-]{8,80}$")


class BusMessageAcknowledge(BusModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    note: str | None = Field(default=None, max_length=1000)


class BusTaskCreate(BusModel):
    task_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    owner_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    task_status: Literal["PENDING", "OPEN"] = "PENDING"
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    title: str = Field(min_length=1, max_length=240)
    expected_output: str = Field(min_length=1, max_length=4000)
    source_ref: str = Field(min_length=1, max_length=400)
    review_at: datetime | None = None


class BusTaskTransition(BusModel):
    new_status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "BLOCKED",
        "HOLD",
        "REVIEW",
        "DONE",
        "CANCELLED",
    ]
    completion_evidence: str | None = Field(default=None, max_length=8000)


class BusHandoffCreate(BusModel):
    handoff_id: str = Field(pattern=r"^HO-[A-Z0-9-]{3,63}$")
    recipient_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    handoff_status: Literal["PENDING", "OPEN"] = "PENDING"
    input_summary: str = Field(min_length=1, max_length=8000)
    expected_output: str = Field(min_length=1, max_length=4000)
    source_ref: str = Field(min_length=1, max_length=400)
    task_ref: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    risks_and_assumptions: str | None = Field(default=None, max_length=8000)
    trigger_or_due: str | None = Field(default=None, max_length=2000)


class BusHandoffTransition(BusModel):
    new_status: Literal["OPEN", "ACCEPTED", "REJECTED", "CANCELLED"]
    response_note: str | None = Field(default=None, max_length=4000)


class KnowledgeAudience(BusModel):
    kind: Literal["PROJECT", "ROLE", "EMPLOYEE"]
    value: str = Field(min_length=1, max_length=128)


class KnowledgeCandidateCreate(BusModel):
    knowledge_id: str = Field(pattern=r"^KN-[A-Z0-9-]{3,60}$")
    title: str = Field(min_length=1, max_length=240)
    knowledge_class: Literal["K0", "K1", "K2", "K3", "K4", "K5"]
    domain: str = Field(min_length=1, max_length=120)
    owner_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    classification: Literal["PROJECT_INTERNAL", "NEED_TO_KNOW"]
    provenance_source: str = Field(min_length=1, max_length=1000)
    valid_from: datetime | None = None
    review_due: datetime | None = None
    stale_after: datetime | None = None
    tags: list[Annotated[str, Field(min_length=1, max_length=80)]] = Field(
        default_factory=list,
        max_length=40,
    )
    content: str = Field(min_length=1, max_length=100000)
    audiences: list[KnowledgeAudience] = Field(min_length=1, max_length=50)


class KnowledgeRevoke(BusModel):
    reason: str = Field(min_length=1, max_length=1000)


class KnowledgeRetrieve(BusModel):
    query: str = Field(min_length=1, max_length=1000)
    domain: str | None = Field(default=None, min_length=1, max_length=120)
    retrieval_mode: Literal["GENERAL", "ROLE_PACK"] = "GENERAL"
    task_ref: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    limit: int = Field(default=5, ge=1, le=20)


class CapabilityAssessmentCreate(BusModel):
    assessment_id: str = Field(pattern=r"^ASMT-[A-Z0-9-]{3,60}$")
    employee_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    capability_id: str = Field(pattern=r"^CAP-[A-Z0-9-]{3,60}$")
    score: int = Field(ge=0, le=5)
    target_level: int = Field(ge=0, le=5)
    error_class: Literal["E1", "E2", "E3", "E4", "E5", "E6"]
    feedback: str = Field(min_length=1, max_length=8000)
    training_action: str = Field(min_length=1, max_length=4000)
    context_run_id: str | None = Field(default=None, pattern=r"^KRUN-[A-Z0-9-]{8,80}$")
    retest_of: str | None = Field(default=None, pattern=r"^ASMT-[A-Z0-9-]{3,60}$")
    retest_result: str | None = Field(default=None, max_length=4000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(require_https_transport)])
def user_interface() -> str:
    return UI_HTML


# Review finding G-040: FastAPI serves its schema at /openapi.json without a
# credential, and that schema describes every route and every request model -
# the full internal attack surface, handed to anything that can reach the
# port. docs_url and redoc_url were already off; this was the last anonymous
# description of the API.
#
# Authenticated rather than removed. e2e_acceptance.rb reads the path list to
# check the contract against the running app, and a check that has to be
# deleted in order to close a finding is a worse outcome than one that has to
# send a key. require_api_key also refuses cleartext, so the schema never
# travels anywhere the key would not.
#
# openapi_url=None above removes FastAPI's own unauthenticated route; this one
# takes its place at the same path, so the route inventory is unchanged.
@app.get("/openapi.json", include_in_schema=False,
         dependencies=[Depends(require_api_key)])
def openapi_schema() -> dict:
    return app.openapi()


@app.get("/db-check")
def db_check() -> dict[str, str]:
    try:
        with connection() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"database": "ok"}


@app.get("/bus/v1/status")
def bus_status() -> dict:
    try:
        with connection() as conn:
            if conn.execute("SELECT to_regclass('workforce.bus_channels')").fetchone()[0] is None:
                return {
                    "api_version": "v9",
                    "project_id": BUS_PROJECT_ID,
                    "migration": "missing",
                    "channel_status": "MISSING",
                }
            row = conn.execute(
                """
                SELECT
                    ch.channel_status,
                    ch.max_hops,
                    ch.max_body_chars,
                    EXISTS (
                        SELECT 1
                        FROM workforce.schema_migrations sm
                        WHERE sm.migration_id = '002_workforce_bus'
                    ) AS migration_present
                FROM workforce.bus_channels ch
                WHERE ch.project_id = %s
                """,
                (BUS_PROJECT_ID,),
            ).fetchone()
    except psycopg.Error as exc:
        raise bus_error(exc) from exc

    if row is None:
        return {
            "api_version": "v9",
            "project_id": BUS_PROJECT_ID,
            "migration": "missing",
            "channel_status": "MISSING",
        }
    return {
        "api_version": "v9",
        "project_id": BUS_PROJECT_ID,
        "migration": "002_workforce_bus" if row[3] else "missing",
        "channel_status": row[0],
        "max_hops": row[1],
        "max_body_chars": row[2],
    }


@app.get("/bus/v1/messages")
def bus_list_messages(
    scope: Literal["INBOX", "OUTBOX", "PROJECT"] = Query(default="INBOX"),
    limit: int = Query(default=100, ge=1, le=200),
    token_hash: str = Depends(require_bus_token),
) -> list[dict]:
    return execute_bus_many(
        "SELECT * FROM workforce.bus_list_messages(%s, %s, %s, %s)",
        (token_hash, BUS_PROJECT_ID, scope, limit),
        audit=BusAudit("MESSAGE_LIST", "MESSAGE", token_hash, f"READ:{scope}"),
    )


@app.post("/bus/v1/messages", status_code=201)
def bus_send_message(
    item: BusMessageCreate,
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
    idempotency_key: str = Depends(require_idempotency_key),
) -> dict:
    stable_input = f"{token_hash}:{BUS_PROJECT_ID}:{idempotency_key}".encode("utf-8")
    message_id = "MSG-" + hashlib.sha256(stable_input).hexdigest().upper()[:32]
    return execute_bus_one(
        """
        SELECT (workforce.bus_send_message(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            message_id,
            BUS_PROJECT_ID,
            item.recipient_id,
            idempotency_key,
            item.subject,
            item.body,
            item.action_class,
            item.confidentiality,
            item.task_ref,
            item.handoff_ref,
            item.parent_message_id,
        ),
        audit=BusAudit("MESSAGE_SEND", "MESSAGE", token_hash, request_id, message_id),
    )


@app.post("/bus/v1/messages/{message_id}/ack")
def bus_acknowledge_message(
    item: BusMessageAcknowledge,
    message_id: str = Path(pattern=r"^MSG-[A-Z0-9-]{8,80}$"),
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.bus_acknowledge_message(
            %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            message_id,
            item.decision,
            item.note,
        ),
        audit=BusAudit("MESSAGE_ACK", "MESSAGE", token_hash, request_id, message_id),
    )


@app.get("/bus/v1/tasks")
def bus_list_tasks(
    scope: Literal["OWNED", "CREATED", "PROJECT"] = Query(default="OWNED"),
    limit: int = Query(default=100, ge=1, le=200),
    token_hash: str = Depends(require_bus_token),
) -> list[dict]:
    return execute_bus_many(
        "SELECT * FROM workforce.bus_list_tasks(%s, %s, %s, %s)",
        (token_hash, BUS_PROJECT_ID, scope, limit),
        audit=BusAudit("TASK_LIST", "TASK", token_hash, f"READ:{scope}"),
    )


@app.post("/bus/v1/tasks", status_code=201)
def bus_create_task(
    item: BusTaskCreate,
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.bus_create_task(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            item.task_id,
            BUS_PROJECT_ID,
            item.owner_id,
            item.task_status,
            item.priority,
            item.title,
            item.expected_output,
            item.source_ref,
            item.review_at,
        ),
        audit=BusAudit("TASK_CREATE", "TASK", token_hash, request_id, item.task_id),
    )


@app.post("/bus/v1/tasks/{task_id}/transition")
def bus_transition_task(
    item: BusTaskTransition,
    task_id: str = Path(pattern=r"^[A-Z][A-Z0-9-]{2,63}$"),
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.bus_transition_task(
            %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            task_id,
            item.new_status,
            item.completion_evidence,
        ),
        audit=BusAudit("TASK_TRANSITION", "TASK", token_hash, request_id, task_id),
    )


@app.get("/bus/v1/handoffs")
def bus_list_handoffs(
    scope: Literal["INBOX", "OUTBOX", "PROJECT"] = Query(default="INBOX"),
    limit: int = Query(default=100, ge=1, le=200),
    token_hash: str = Depends(require_bus_token),
) -> list[dict]:
    return execute_bus_many(
        "SELECT * FROM workforce.bus_list_handoffs(%s, %s, %s, %s)",
        (token_hash, BUS_PROJECT_ID, scope, limit),
        audit=BusAudit("HANDOFF_LIST", "HANDOFF", token_hash, f"READ:{scope}"),
    )


@app.post("/bus/v1/handoffs", status_code=201)
def bus_create_handoff(
    item: BusHandoffCreate,
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.bus_create_handoff(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            item.handoff_id,
            BUS_PROJECT_ID,
            item.recipient_id,
            item.handoff_status,
            item.input_summary,
            item.expected_output,
            item.source_ref,
            item.task_ref,
            item.risks_and_assumptions,
            item.trigger_or_due,
        ),
        audit=BusAudit("HANDOFF_CREATE", "HANDOFF", token_hash, request_id,
                       item.handoff_id),
    )


@app.post("/bus/v1/handoffs/{handoff_id}/transition")
def bus_transition_handoff(
    item: BusHandoffTransition,
    handoff_id: str = Path(pattern=r"^HO-[A-Z0-9-]{3,63}$"),
    token_hash: str = Depends(require_bus_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.bus_transition_handoff(
            %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            handoff_id,
            item.new_status,
            item.response_note,
        ),
        audit=BusAudit("HANDOFF_TRANSITION", "HANDOFF", token_hash, request_id,
                       handoff_id),
    )


@app.get("/knowledge/v1/status")
def knowledge_status() -> dict:
    try:
        with connection() as conn:
            if conn.execute(
                "SELECT to_regclass('workforce.knowledge_systems')"
            ).fetchone()[0] is None:
                return {
                    "api_version": "v9",
                    "project_id": BUS_PROJECT_ID,
                    "migration": "missing",
                    "system_status": "MISSING",
                }
            row = conn.execute(
                """
                SELECT
                    system.system_status,
                    EXISTS (
                        SELECT 1
                        FROM workforce.schema_migrations AS migration
                        WHERE migration.migration_id = '004_knowledge_capability'
                    ) AS migration_present
                FROM workforce.knowledge_systems AS system
                WHERE system.project_id = %s
                """,
                (BUS_PROJECT_ID,),
            ).fetchone()
    except psycopg.Error as exc:
        raise bus_error(exc) from exc

    if row is None:
        return {
            "api_version": "v9",
            "project_id": BUS_PROJECT_ID,
            "migration": "missing",
            "system_status": "MISSING",
        }
    return {
        "api_version": "v9",
        "project_id": BUS_PROJECT_ID,
        "migration": "004_knowledge_capability" if row[1] else "missing",
        "system_status": row[0],
    }


@app.post("/knowledge/v1/candidates", status_code=201)
def knowledge_create_candidate(
    item: KnowledgeCandidateCreate,
    token_hash: str = Depends(require_knowledge_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    audience_payload = json.dumps(
        [audience.model_dump() for audience in item.audiences],
        separators=(",", ":"),
    )
    return execute_bus_one(
        """
        SELECT (workforce.knowledge_create_candidate(
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s::jsonb
        )).*
        """,
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            item.knowledge_id,
            item.title,
            item.knowledge_class,
            item.domain,
            item.owner_id,
            item.classification,
            item.provenance_source,
            item.valid_from,
            item.review_due,
            item.stale_after,
            item.tags,
            item.content,
            audience_payload,
        ),
        audit=BusAudit("KNOWLEDGE_CREATE", "KNOWLEDGE", token_hash, request_id,
                       item.knowledge_id),
    )


@app.post("/knowledge/v1/objects/{knowledge_id}/versions/{version}/submit-review")
def knowledge_submit_review(
    knowledge_id: str = Path(pattern=r"^KN-[A-Z0-9-]{3,60}$"),
    version: int = Path(ge=1),
    token_hash: str = Depends(require_knowledge_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.knowledge_submit_review(%s, %s, %s, %s, %s)).*
        """,
        (token_hash, request_id, BUS_PROJECT_ID, knowledge_id, version),
        audit=BusAudit("KNOWLEDGE_SUBMIT_REVIEW", "KNOWLEDGE", token_hash, request_id,
                       knowledge_id),
    )


@app.post("/knowledge/v1/objects/{knowledge_id}/versions/{version}/approve")
def knowledge_approve(
    knowledge_id: str = Path(pattern=r"^KN-[A-Z0-9-]{3,60}$"),
    version: int = Path(ge=1),
    token_hash: str = Depends(require_knowledge_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        "SELECT (workforce.knowledge_approve(%s, %s, %s, %s, %s)).*",
        (token_hash, request_id, BUS_PROJECT_ID, knowledge_id, version),
        audit=BusAudit("KNOWLEDGE_APPROVE", "KNOWLEDGE", token_hash, request_id, knowledge_id),
    )


@app.post("/knowledge/v1/objects/{knowledge_id}/versions/{version}/revoke")
def knowledge_revoke(
    item: KnowledgeRevoke,
    knowledge_id: str = Path(pattern=r"^KN-[A-Z0-9-]{3,60}$"),
    version: int = Path(ge=1),
    token_hash: str = Depends(require_knowledge_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        "SELECT (workforce.knowledge_revoke(%s, %s, %s, %s, %s, %s)).*",
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            knowledge_id,
            version,
            item.reason,
        ),
        audit=BusAudit("KNOWLEDGE_REVOKE", "KNOWLEDGE", token_hash, request_id, knowledge_id),
    )


@app.post("/knowledge/v1/retrieve")
def knowledge_retrieve(
    item: KnowledgeRetrieve,
    token_hash: str = Depends(require_knowledge_token),
) -> list[dict]:
    run_id = "KRUN-" + uuid.uuid4().hex.upper()
    return execute_bus_many(
        """
        SELECT * FROM workforce.knowledge_retrieve(
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            token_hash,
            run_id,
            BUS_PROJECT_ID,
            item.query,
            item.domain,
            item.retrieval_mode,
            item.task_ref,
            item.limit,
        ),
        audit=BusAudit("KNOWLEDGE_RETRIEVE", "KNOWLEDGE", token_hash, run_id),
    )


@app.post("/knowledge/v1/assessments", status_code=201)
def knowledge_record_assessment(
    item: CapabilityAssessmentCreate,
    token_hash: str = Depends(require_knowledge_token),
    request_id: str = Depends(require_request_id),
) -> dict:
    return execute_bus_one(
        """
        SELECT (workforce.knowledge_record_assessment(
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )).*
        """,
        (
            token_hash,
            request_id,
            BUS_PROJECT_ID,
            item.assessment_id,
            item.employee_id,
            item.capability_id,
            item.score,
            item.target_level,
            item.error_class,
            item.feedback,
            item.training_action,
            item.context_run_id,
            item.retest_of,
            item.retest_result,
        ),
        audit=BusAudit("KNOWLEDGE_ASSESSMENT", "KNOWLEDGE", token_hash, request_id,
                       item.assessment_id),
    )


@app.get("/kernel", dependencies=[Depends(require_api_key)])
def kernel_status() -> dict:
    with connection() as conn:
        counts = {}
        for table in ("roles", "workers", "tasks", "activity_log"):
            counts[table] = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    return {"status": "ready", "counts": counts, "time": datetime.now().astimezone().isoformat()}


@app.get("/roles", dependencies=[Depends(require_api_key)])
def list_roles() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT id, name, description, created_at FROM roles ORDER BY name").fetchall()
    return [{"id": r[0], "name": r[1], "description": r[2], "created_at": r[3]} for r in rows]


@app.get("/workers", dependencies=[Depends(require_api_key)])
def list_workers() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT id, name, kind, role_id, active, created_at FROM workers ORDER BY name").fetchall()
    return [{"id": r[0], "name": r[1], "kind": r[2], "role_id": r[3], "active": r[4], "created_at": r[5]} for r in rows]


@app.get("/tasks", dependencies=[Depends(require_api_key)])
def list_tasks() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT id, title, description, status, assignee_id, created_at, updated_at FROM tasks ORDER BY id DESC").fetchall()
        notes = conn.execute("SELECT id, task_id, note_type, content, created_at FROM task_notes ORDER BY id").fetchall()
    by_task = {}
    for n in notes:
        by_task.setdefault(n[1], []).append({"id": n[0], "note_type": n[2], "content": n[3], "created_at": n[4]})
    return [{"id": r[0], "title": r[1], "description": r[2], "status": r[3], "assignee_id": r[4], "created_at": r[5], "updated_at": r[6], "notes": by_task.get(r[0], [])} for r in rows]


@app.post("/tasks/{task_id}/notes", status_code=201, dependencies=[Depends(require_api_key)])
def add_task_note(task_id: int, item: TaskNoteCreate) -> dict:
    with connection() as conn:
        if conn.execute("SELECT 1 FROM tasks WHERE id = %s", (task_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="task not found")
        row = conn.execute("INSERT INTO task_notes (task_id, note_type, content) VALUES (%s, %s, %s) RETURNING id, created_at", (task_id, item.note_type, item.content)).fetchone()
        conn.execute("INSERT INTO activity_log (event_type, entity_type, entity_id) VALUES (%s, 'task', %s)", (item.note_type + '_added', task_id))
    return {"id": row[0], "task_id": task_id, "note_type": item.note_type, "content": item.content, "created_at": row[1]}


@app.get("/documents", dependencies=[Depends(require_api_key)])
def list_documents() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT d.id, d.title, d.updated_at, count(v.id) FROM documents d LEFT JOIN document_versions v ON v.document_id=d.id GROUP BY d.id ORDER BY d.title").fetchall()
    return [{"id": r[0], "title": r[1], "updated_at": r[2], "version_count": r[3]} for r in rows]


@app.get("/documents/{document_id}", dependencies=[Depends(require_api_key)])
def get_document(document_id: int) -> dict:
    with connection() as conn:
        row = conn.execute("SELECT id, title, content, updated_at FROM documents WHERE id=%s", (document_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {"id": row[0], "title": row[1], "content": row[2], "updated_at": row[3]}


@app.post("/documents", dependencies=[Depends(require_api_key)])
def save_document(item: DocumentSave) -> dict:
    with connection() as conn:
        existing = conn.execute("SELECT id, content FROM documents WHERE title=%s", (item.title,)).fetchone()
        if existing:
            conn.execute("INSERT INTO document_versions (document_id, content) VALUES (%s, %s)", (existing[0], existing[1]))
            row = conn.execute("UPDATE documents SET content=%s, updated_at=now() WHERE id=%s RETURNING id, updated_at", (item.content, existing[0])).fetchone()
            event = 'updated'
        else:
            row = conn.execute("INSERT INTO documents (title, content) VALUES (%s, %s) RETURNING id, updated_at", (item.title, item.content)).fetchone()
            event = 'created'
        conn.execute("INSERT INTO activity_log (event_type, entity_type, entity_id) VALUES (%s, 'document', %s)", (event, row[0]))
    return {"id": row[0], "title": item.title, "content": item.content, "updated_at": row[1]}


@app.get("/activities", dependencies=[Depends(require_api_key)])
def list_activities() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT id, event_type, entity_type, entity_id, details, created_at FROM activity_log ORDER BY id DESC LIMIT 100").fetchall()
    return [{"id": r[0], "event_type": r[1], "entity_type": r[2], "entity_id": r[3], "details": r[4], "created_at": r[5]} for r in rows]


@app.post("/roles", status_code=201, dependencies=[Depends(require_api_key)])
def create_role(item: RoleCreate) -> dict:
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO roles (name, description) VALUES (%s, %s) RETURNING id, name, description",
            (item.name, item.description),
        ).fetchone()
        conn.execute(
            "INSERT INTO activity_log (event_type, entity_type, entity_id) VALUES ('created', 'role', %s)",
            (row[0],),
        )
    return {"id": row[0], "name": row[1], "description": row[2]}


@app.post("/workers", status_code=201, dependencies=[Depends(require_api_key)])
def create_worker(item: WorkerCreate) -> dict:
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO workers (name, kind, role_id) VALUES (%s, %s, %s) RETURNING id, name, kind, role_id",
            (item.name, item.kind, item.role_id),
        ).fetchone()
        conn.execute(
            "INSERT INTO activity_log (event_type, entity_type, entity_id) VALUES ('created', 'worker', %s)",
            (row[0],),
        )
    return {"id": row[0], "name": row[1], "kind": row[2], "role_id": row[3]}


@app.post("/tasks", status_code=201, dependencies=[Depends(require_api_key)])
def create_task(item: TaskCreate) -> dict:
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title, description, assignee_id) VALUES (%s, %s, %s) RETURNING id, title, status, assignee_id",
            (item.title, item.description, item.assignee_id),
        ).fetchone()
        conn.execute(
            "INSERT INTO activity_log (event_type, entity_type, entity_id) VALUES ('created', 'task', %s)",
            (row[0],),
        )
    return {"id": row[0], "title": row[1], "status": row[2], "assignee_id": row[3]}


@app.patch("/tasks/{task_id}", dependencies=[Depends(require_api_key)])
def update_task(task_id: int, item: TaskStatusUpdate) -> dict:
    with connection() as conn:
        row = conn.execute(
            "UPDATE tasks SET status = %s, updated_at = now() WHERE id = %s RETURNING id, title, status, assignee_id",
            (item.status, task_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="task not found")
        conn.execute(
            "INSERT INTO activity_log (event_type, entity_type, entity_id, details) VALUES ('status_changed', 'task', %s, jsonb_build_object('status', %s::text))",
            (task_id, item.status),
        )
    return {"id": row[0], "title": row[1], "status": row[2], "assignee_id": row[3]}
