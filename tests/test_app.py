import importlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PONTO_DB",str(tmp_path/"test.db"))
    monkeypatch.setenv("PONTO_DEMO","1")
    import app.main as module
    module = importlib.reload(module)
    module.init_db()
    with TestClient(module.app) as c:
        yield c

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_add_and_deactivate_employee(client):
    r=client.post("/funcionarios",data={"name":"Pessoa Teste","department":"TI"},follow_redirects=True)
    assert r.status_code == 200
    assert "Pessoa Teste" in r.text
    assert client.post("/funcionarios/1/desativar",follow_redirects=True).status_code == 200

def test_manual_and_export(client):
    client.post("/funcionarios",data={"name":"Pessoa Exemplo","department":"RH"})
    data={"employee_id":"1","day":"2026-10-20","time":"09:00","kind":"entrada","reason":"Teste","actor":"Admin"}
    assert client.post("/marcacoes",data=data,follow_redirects=False).status_code == 303
    csv=client.get("/exportar.csv?month=2026-10")
    assert csv.status_code == 200
    assert "Pessoa Exemplo" in csv.text
    assert client.get("/exportar.xlsx?month=2026-10").status_code == 200
    assert "Pendente" in client.get("/fechamento/1?month=2026-10").text

def test_reject_invalid_correction(client):
    client.post("/funcionarios",data={"name":"Pessoa Exemplo"})
    assert client.post("/marcacoes",data={"employee_id":1,"day":"2026-10-20","time":"09:00","kind":"outro","reason":"x","actor":"a"}).status_code == 422

def test_real_mode_requires_admin_token(client, monkeypatch):
    import app.main as module
    monkeypatch.setattr(module, "DEMO", False)
    monkeypatch.setattr(module, "ADMIN_TOKEN", "secret")
    assert client.post("/funcionarios",data={"name":"Teste"}).status_code == 403
