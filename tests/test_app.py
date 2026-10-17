import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_health_non_dipende_dal_db():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_risponde_503_se_il_db_e_giu(monkeypatch):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "check_db", boom)
    assert client.get("/ready").status_code == 503


def test_ready_ok_se_il_db_risponde(monkeypatch):
    monkeypatch.setattr(main, "check_db", lambda: None)
    assert client.get("/ready").status_code == 200


def test_creazione_e_lettura_note(monkeypatch):
    store = []

    def add(text):
        note = {"id": len(store) + 1, "text": text}
        store.append(note)
        return note

    monkeypatch.setattr(main, "insert_note", add)
    monkeypatch.setattr(main, "fetch_notes", lambda: list(store))

    r = client.post("/api/notes", json={"text": "  ciao  "})
    assert r.status_code == 201
    assert r.json()["text"] == "ciao"
    assert client.get("/api/notes").json()[0]["text"] == "ciao"


def test_testo_vuoto_rifiutato():
    assert client.post("/api/notes", json={"text": ""}).status_code == 422


def test_errore_db_diventa_503(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "fetch_notes", boom)
    assert client.get("/api/notes").status_code == 503


def test_metrics_esposte():
    client.get("/health")
    body = client.get("/metrics").text
    assert "http_requests_total" in body


def test_pagina_html():
    r = client.get("/")
    assert r.status_code == 200
    assert main.APP_TITLE in r.text
