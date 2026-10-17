# notes-app

Un blocco note minimale: pagina web, API REST e database Postgres. Il codice è pronto. Tutto quello che serve per farlo girare in container, su Kubernetes e in automatico lo scrivi tu (vedi `PERCORSO.md`).

## Il "contratto" dell'app

Questo è quello che ti serve sapere per portarla in giro, come se l'avesse scritta un altro team e te l'avesse passata.

| | |
|---|---|
| Linguaggio | Python 3.12 (FastAPI + uvicorn) |
| Dipendenze | `app/requirements.txt` (per sviluppo e test: `requirements-dev.txt`) |
| Avvio | dalla cartella `app/`: `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Porta | 8000 |
| Database | Postgres 16. La tabella `notes` viene creata da sola alla prima richiesta |
| File scritti su disco | nessuno (l'app non ha bisogno di scrivere nel filesystem) |

**Variabili d'ambiente**

| Variabile | Default | Note |
|---|---|---|
| `DB_HOST` | `localhost` | |
| `DB_PORT` | `5432` | |
| `DB_NAME` | `notes` | |
| `DB_USER` | `notes` | |
| `DB_PASSWORD` | `notes` | è un segreto |
| `APP_TITLE` | `Notes Demo` | titolo mostrato nella pagina |
| `APP_ENV` | `local` | etichetta mostrata nella pagina (dev, prod...) |
| `LOG_LEVEL` | `INFO` | |

**Endpoint**

| Endpoint | A cosa serve |
|---|---|
| `GET /` | pagina web |
| `GET /api/notes`, `POST /api/notes` | leggere e creare note |
| `GET /api/info` | ambiente e nome del pod che risponde |
| `GET /health` | l'app è viva (non guarda il database) |
| `GET /ready` | l'app è pronta a ricevere traffico (risponde 503 se il database non c'è) |
| `GET /metrics` | metriche in formato Prometheus |

## Provarla sul tuo computer

```bash
# 1. un Postgres usa e getta
docker run --rm --name pg -p 5432:5432 \
  -e POSTGRES_USER=notes -e POSTGRES_PASSWORD=notes -e POSTGRES_DB=notes \
  postgres:16-alpine

# 2. in un altro terminale: ambiente Python isolato e avvio
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cd app && uvicorn main:app --reload
```

Apri http://localhost:8000. I test si lanciano dalla radice con `pytest -q` e il controllo di stile con `ruff check .`
