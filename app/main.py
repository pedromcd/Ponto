"""Public demonstration of employee time attendance management.

No employee biometrics are accepted or stored in this release.
"""
import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.getenv("PONTO_DB", str(ROOT / "data" / "ponto.db")))
TZ = ZoneInfo("America/Sao_Paulo")
DEMO = os.getenv("PONTO_DEMO", "0") == "1"
ADMIN_TOKEN = os.getenv("PONTO_ADMIN_TOKEN", "")
app = FastAPI(title="Ponto | Demonstracao", version="1.0.0")
templates = Jinja2Templates(directory=str(ROOT / "app" / "templates"))


@contextmanager
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS employees(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS punches(
            id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(id),
            occurred_at TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('entrada','saida')),
            source TEXT NOT NULL CHECK(source IN ('demo','manual')),
            reason TEXT NOT NULL DEFAULT '', actor TEXT NOT NULL DEFAULT '',
            ignored INTEGER NOT NULL DEFAULT 0, ignored_reason TEXT NOT NULL DEFAULT '',
            ignored_by TEXT NOT NULL DEFAULT '');
        CREATE INDEX IF NOT EXISTS idx_punches_employee_time
            ON punches(employee_id, occurred_at);
        """)


@app.on_event("startup")
def startup():
    init_db()


def admin(request: Request):
    # All write operations in non-demo mode require an explicit secret header.
    if DEMO:
        return
    if not ADMIN_TOKEN or request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin token required")


def parse_day(raw: str):
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date")


def punches_for(db, employee_id, start, end):
    return db.execute(
        """SELECT * FROM punches WHERE employee_id=? AND occurred_at>=?
           AND occurred_at<? ORDER BY occurred_at,id""",
        (employee_id, start, end),
    ).fetchall()


def daily_summary(rows):
    valid = [r for r in rows if not r["ignored"]]
    pending = False
    seconds = 0
    entered = None
    for r in valid:
        ts = datetime.fromisoformat(r["occurred_at"])
        if r["kind"] == "entrada":
            if entered is not None:
                pending = True
            entered = ts
        else:
            if entered is None:
                pending = True
            else:
                seconds += max(0, (ts - entered).total_seconds())
                entered = None
    if entered is not None:
        pending = True
    return {"hours": round(seconds / 3600, 2), "pending": pending,
            "count": len(valid)}


def view(request, name, **kwargs):
    return templates.TemplateResponse(request, name, {"demo": DEMO, **kwargs})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return view(request, "home.html")


@app.get("/health")
def health():
    return {"status": "ok", "demo": DEMO}


@app.get("/funcionarios", response_class=HTMLResponse)
def employees(request: Request):
    with connect() as db:
        people = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
    return view(request, "employees.html", people=people)


@app.post("/funcionarios")
def create_employee(request: Request, name: str = Form(...),
                    department: str = Form("")):
    admin(request)
    name = name.strip()
    if not 2 <= len(name) <= 100:
        raise HTTPException(422, "Name must have 2 to 100 characters")
    with connect() as db:
        db.execute("INSERT INTO employees(name,department) VALUES(?,?)",
                   (name, department.strip()[:100]))
    return RedirectResponse("/funcionarios", status_code=303)


@app.post("/funcionarios/{employee_id}/desativar")
def deactivate_employee(employee_id: int, request: Request):
    admin(request)
    with connect() as db:
        changed = db.execute("UPDATE employees SET active=0 WHERE id=?", (employee_id,))
        if changed.rowcount == 0:
            raise HTTPException(404, "Employee not found")
    return RedirectResponse("/funcionarios", status_code=303)


@app.get("/diario", response_class=HTMLResponse)
def daily(request: Request, day: str | None = None):
    current = parse_day(day) if day else datetime.now(TZ).date()
    start = current.isoformat()
    end = (current + timedelta(days=1)).isoformat()
    with connect() as db:
        people = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
        details = []
        for person in people:
            punches = punches_for(db, person["id"], start, end)
            details.append({"person": person, "punches": punches,
                            "summary": daily_summary(punches)})
    return view(request, "daily.html", details=details, day=current.isoformat())


@app.get("/fechamento", response_class=HTMLResponse)
def closing(request: Request, month: str | None = None):
    now = datetime.now(TZ)
    period = month or now.strftime("%Y-%m")
    try:
        first = date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(422, "Month must be YYYY-MM")
    last = (date(first.year + 1, 1, 1) if first.month == 12
            else date(first.year, first.month + 1, 1))
    with connect() as db:
        people = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
        entries = []
        for p in people:
            rows = punches_for(db, p["id"], first.isoformat(), last.isoformat())
            by_day = {}
            for row in rows:
                by_day.setdefault(row["occurred_at"][:10], []).append(row)
            summaries = [daily_summary(v) for v in by_day.values()]
            entries.append({"person": p, "hours": round(sum(s["hours"] for s in summaries), 2),
                            "pending": sum(s["pending"] for s in summaries),
                            "punches": len(rows)})
    return view(request, "closing.html", entries=entries, month=period)


@app.get("/fechamento/{employee_id}", response_class=HTMLResponse)
def employee_closing(employee_id: int, request: Request, month: str | None = None):
    period = month or datetime.now(TZ).strftime("%Y-%m")
    try:
        first = date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(422, "Month must be YYYY-MM")
    last = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    with connect() as db:
        person = db.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
        if person is None:
            raise HTTPException(404, "Employee not found")
        rows = punches_for(db, employee_id, first.isoformat(), last.isoformat())
        grouped = {}
        for row in rows:
            grouped.setdefault(row["occurred_at"][:10], []).append(row)
        entries = [{"day": day, "punches": items, "summary": daily_summary(items)}
                   for day, items in sorted(grouped.items())]
    return view(request, "person.html", person=person, entries=entries, month=period)


@app.post("/marcacoes")
def manual_punch(request: Request, employee_id: int = Form(...),
                 day: str = Form(...), time: str = Form(...),
                 kind: str = Form(...), reason: str = Form(...),
                 actor: str = Form(...)):
    admin(request)
    if kind not in ("entrada", "saida"):
        raise HTTPException(422, "Invalid kind")
    try:
        stamp = datetime.fromisoformat(day + "T" + time)
    except ValueError:
        raise HTTPException(422, "Invalid timestamp")
    if not reason.strip() or not actor.strip():
        raise HTTPException(422, "Reason and actor are required")
    with connect() as db:
        if not db.execute("SELECT id FROM employees WHERE id=?", (employee_id,)).fetchone():
            raise HTTPException(404, "Employee not found")
        db.execute("""INSERT INTO punches(employee_id,occurred_at,kind,source,reason,actor)
                      VALUES(?,?,?,?,?,?)""",
                   (employee_id, stamp.isoformat(timespec="seconds"), kind, "manual",
                    reason.strip()[:500], actor.strip()[:100]))
    return RedirectResponse("/fechamento/" + str(employee_id) + "?month=" + day[:7], status_code=303)


@app.post("/marcacoes/{punch_id}/desconsiderar")
def ignore_punch(punch_id: int, request: Request, reason: str = Form(...),
                 actor: str = Form(...)):
    admin(request)
    if not reason.strip() or not actor.strip():
        raise HTTPException(422, "Reason and actor are required")
    with connect() as db:
        row = db.execute("SELECT * FROM punches WHERE id=?", (punch_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Punch not found")
        db.execute("""UPDATE punches SET ignored=1, ignored_reason=?, ignored_by=?
                      WHERE id=?""", (reason.strip()[:500], actor.strip()[:100], punch_id))
    return RedirectResponse(
        "/fechamento/" + str(row["employee_id"]) + "?month=" + row["occurred_at"][:7],
        status_code=303)


@app.get("/exportar.csv")
def export_csv(request: Request, month: str = Query(pattern=r"^\d{4}-\d{2}$")):
    admin(request)
    try:
        first = date.fromisoformat(month + "-01")
    except ValueError:
        raise HTTPException(422, "Invalid month")
    last = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    with connect() as db:
        rows = db.execute("""SELECT e.name,p.* FROM punches p JOIN employees e
            ON p.employee_id=e.id WHERE p.occurred_at>=? AND p.occurred_at<?
            ORDER BY e.name,p.occurred_at""", (first.isoformat(), last.isoformat())).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Funcionario", "Data e hora", "Tipo", "Origem", "Motivo",
                     "Autor", "Desconsiderado", "Motivo desconsideracao", "Responsavel"])
    for r in rows:
        writer.writerow([r["name"],r["occurred_at"],r["kind"],r["source"],r["reason"],
                         r["actor"],r["ignored"],r["ignored_reason"],r["ignored_by"]])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="registros.csv"'})


@app.get("/exportar.xlsx")
def export_xlsx(request: Request, month: str = Query(pattern=r"^\d{4}-\d{2}$")):
    admin(request)
    try:
        first = date.fromisoformat(month + "-01")
    except ValueError:
        raise HTTPException(422, "Invalid month")
    last = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    with connect() as db:
        people = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
        wb = Workbook()
        for index, person in enumerate(people):
            ws = wb.active if index == 0 else wb.create_sheet()
            ws.title = (person["name"][:25] + "_" + str(person["id"]))[:31]
            ws.append(["Data", "Marcacoes", "Horas", "Pendente"])
            rows = punches_for(db, person["id"], first.isoformat(), last.isoformat())
            grouped = {}
            for r in rows:
                grouped.setdefault(r["occurred_at"][:10], []).append(r)
            for day, items in sorted(grouped.items()):
                s = daily_summary(items)
                ws.append([day, " | ".join(r["occurred_at"][11:16] + " " + r["kind"]
                        for r in items if not r["ignored"]), s["hours"], "SIM" if s["pending"] else "NAO"])
        if not people:
            wb.active.title = "Sem funcionarios"
        output = io.BytesIO()
        wb.save(output)
    return Response(output.getvalue(),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="fechamento.xlsx"'})
