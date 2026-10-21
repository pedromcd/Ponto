"""Generate synthetic records; never import real employee information."""
import os
from datetime import date, datetime, timedelta
os.environ.setdefault("PONTO_DEMO", "1")
from app.main import connect, init_db

def seed():
    init_db()
    today = date.today()
    start = today.replace(day=1)
    employees = [("Ana Exemplo","TI"),("Bruno Exemplo","Administrativo"),("Carla Exemplo","RH"),("Diego Exemplo","Atendimento")]
    with connect() as db:
        if db.execute("SELECT COUNT(*) FROM employees").fetchone()[0]:
            print("Banco já contém funcionários. Nada alterado.")
            return
        for name, department in employees:
            db.execute("INSERT INTO employees(name,department) VALUES(?,?)",(name,department))
        for employee_id in range(1,5):
            for day_offset in range(min(8,(today-start).days+1)):
                day = start + timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue
                stamps = [(9,"entrada"),(12,"saida"),(13,"entrada"),(18,"saida")]
                if employee_id == 2 and day_offset == 1:
                    stamps = stamps[:-1]
                for hour,kind in stamps:
                    stamp = datetime(day.year,day.month,day.day,hour).isoformat(timespec="seconds")
                    db.execute("""INSERT INTO punches(employee_id,occurred_at,kind,source)
                        VALUES(?,?,?,'demo')""",(employee_id,stamp,kind))
    print("Dados de demonstração criados.")

if __name__ == "__main__":
    seed()
