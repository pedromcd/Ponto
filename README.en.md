**English** | [Português](README.md)

# Ponto Facial | Public demo

Demo application for attendance management, auditable punch corrections, and monthly closing, built with **Python, FastAPI, SQLite, Jinja2, and OpenPyXL**.

> **Scope of this version:** the original system was designed for facial recognition, but the biometric code and employee data are not part of this release. This version demonstrates the administrative workflows using entirely fictitious data. **It is not a certified Brazilian time-recording system (REP-P) and must not be used as an official record of working hours.** It is not ready for business deployment without proper authentication and a review of security, privacy, and labor-law requirements.

## Features

- Registration and deactivation of fictitious employees.
- Daily view of time punches and computed hours.
- Closing view by month and by employee.
- Manual corrections with the reason and the person responsible recorded.
- Auditable punch dismissal that never deletes the original record.
- CSV and Excel exports.
- Test data with no camera and no biometric enrollment.
- Token protection for administrative operations outside demo mode (a minimal safeguard for the demo; it does not replace user authentication).

## How to run

Python 3.10+:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set up the demo environment:

```powershell
$env:PONTO_DEMO="1"
$env:PONTO_DB="data/demo.db"
python semear.py
uvicorn app.main:app --reload
```

On Linux/macOS, use `export PONTO_DEMO=1` and `export PONTO_DB=data/demo.db`.

Open http://127.0.0.1:8000/fechamento. You can also visit `/funcionarios` (employees), `/diario` (daily view), and `/health`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Security and privacy

Do not publish `data/*.db`, face models, employee images, credentials, exports, or backups. With `PONTO_DEMO=1`, all administrative operations are intentionally open for local testing. **Do not expose this mode to the internet.** Outside demo mode, writes and exports require the `X-Admin-Token` header, configured through `PONTO_ADMIN_TOKEN`. Read-only pages remain accessible, so the project must not be hosted with real personal data.

## Known limitations

- No camera or facial recognition in this public version.
- Hours are calculated from clock-in/clock-out pairs; contractual schedules, holidays, pay premiums, and legal rules are not interpreted.
- Days without punches are not automatically classified as absences.
- No user or role management, CSRF protection, complete access control, or immutable audit trail.
- Intended for demonstration and study, not for official use.

Author: [Pedro Marques Correa Domingues](https://github.com/pedromcd).
