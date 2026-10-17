"""Notes demo: piccola API FastAPI con Postgres, pensata per essere deployata su Kubernetes."""

import logging
import os
import socket
from contextlib import contextmanager

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("notes")

APP_TITLE = os.getenv("APP_TITLE", "Notes Demo")
APP_ENV = os.getenv("APP_ENV", "local")

app = FastAPI(title=APP_TITLE)

REQUESTS = Counter("http_requests_total", "Richieste HTTP", ["method", "path", "status"])
NOTES_CREATED = Counter("notes_created_total", "Note create")


# ---------------------------------------------------------------- database
def dsn() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'notes')} "
        f"user={os.getenv('DB_USER', 'notes')} "
        f"password={os.getenv('DB_PASSWORD', 'notes')} "
        "connect_timeout=3"
    )


@contextmanager
def connect():
    with psycopg.connect(dsn()) as conn:
        yield conn


def ensure_schema() -> None:
    # Per una demo basta questo. In produzione useresti migrazioni (Alembic, Flyway...).
    # Niente cache in memoria: se il database viene ricreato vuoto, la tabella torna da sola.
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id SERIAL PRIMARY KEY, "
            "text TEXT NOT NULL, "
            "created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )


def check_db() -> None:
    ensure_schema()
    with connect() as conn:
        conn.execute("SELECT 1")


def fetch_notes() -> list[dict]:
    ensure_schema()
    with connect() as conn:
        rows = conn.execute("SELECT id, text FROM notes ORDER BY id DESC LIMIT 50").fetchall()
    return [{"id": r[0], "text": r[1]} for r in rows]


def insert_note(text: str) -> dict:
    ensure_schema()
    with connect() as conn:
        row = conn.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id, text", (text,)).fetchone()
    return {"id": row[0], "text": row[1]}


# ---------------------------------------------------------------- modelli
class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=280)


# ---------------------------------------------------------------- middleware metriche
@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route else "unmatched"
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


# ---------------------------------------------------------------- endpoint operativi
@app.get("/health")
def health():
    """Liveness: il processo risponde. Non tocca il database, altrimenti un DB lento riavvierebbe l'app."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: l'app può ricevere traffico solo se il database risponde."""
    try:
        check_db()
    except Exception as exc:  # noqa: BLE001
        log.warning("readiness fallita: %s", exc)
        return JSONResponse({"status": "db-unavailable"}, status_code=503)
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------- API
@app.get("/api/info")
def info():
    return {"title": APP_TITLE, "env": APP_ENV, "pod": socket.gethostname()}


@app.get("/api/notes")
def list_notes():
    try:
        return fetch_notes()
    except Exception as exc:  # noqa: BLE001
        log.error("lettura note fallita: %s", exc)
        raise HTTPException(status_code=503, detail="database non disponibile") from exc


@app.post("/api/notes", status_code=201)
def create_note(note: NoteIn):
    try:
        created = insert_note(note.text.strip())
    except Exception as exc:  # noqa: BLE001
        log.error("scrittura nota fallita: %s", exc)
        raise HTTPException(status_code=503, detail="database non disponibile") from exc
    NOTES_CREATED.inc()
    return created


# ---------------------------------------------------------------- pagina web
PAGE = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; color: #1c1c1c; }
  header { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: .5rem; }
  .badge { font-size: .8rem; background: #eef2ff; color: #3730a3; padding: .2rem .6rem; border-radius: 999px; }
  form { display: flex; gap: .5rem; margin: 1.5rem 0; }
  input { flex: 1; padding: .6rem; border: 1px solid #c7c7c7; border-radius: 6px; font-size: 1rem; }
  button { padding: .6rem 1rem; border: 0; border-radius: 6px; background: #3730a3; color: #fff; font-size: 1rem; cursor: pointer; }
  li { padding: .5rem 0; border-bottom: 1px solid #eee; }
  #err { color: #b91c1c; }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <span class="badge" id="meta">...</span>
</header>
<form id="f">
  <input id="t" maxlength="280" placeholder="Scrivi una nota" required>
  <button>Aggiungi</button>
</form>
<p id="err"></p>
<ul id="list"></ul>
<script>
const err = document.getElementById('err');
async function loadInfo() {
  const i = await (await fetch('/api/info')).json();
  document.getElementById('meta').textContent = i.env + ' · pod ' + i.pod;
}
async function loadNotes() {
  const r = await fetch('/api/notes');
  if (!r.ok) { err.textContent = 'Database non raggiungibile'; return; }
  err.textContent = '';
  const notes = await r.json();
  const ul = document.getElementById('list');
  ul.innerHTML = '';
  for (const n of notes) {
    const li = document.createElement('li');
    li.textContent = n.text;
    ul.appendChild(li);
  }
}
document.getElementById('f').addEventListener('submit', async (e) => {
  e.preventDefault();
  const t = document.getElementById('t');
  const r = await fetch('/api/notes', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: t.value})});
  if (r.ok) { t.value = ''; loadNotes(); loadInfo(); } else { err.textContent = 'Salvataggio non riuscito'; }
});
loadInfo(); loadNotes();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE.replace("__TITLE__", APP_TITLE)
