# FDE Incident Assistant — Final Local Project

A beginner-friendly FastAPI application for analyzing application logs and triaging incidents through a dark web dashboard.

## Features

- FastAPI endpoints: `/health`, `/info`, `/summary`, `/errors`, `/info-logs`, `/incident`
- Validates log timestamps and detects malformed entries.
- Counts INFO, WARNING, ERROR, and malformed entries.
- Determines incident severity (HIGH / MEDIUM / LOW).
- Rule-based recommendations for database, payment, network, latency, memory, disk, and malformed-log issues.
- Dashboard search across log messages and recommendations.
- Filters for All, ERROR, WARNING, INFO, and MALFORMED.
- Incident details with timestamp, line number, recommendation, and surrounding log context.
- Auto-refresh toggle with selectable refresh intervals.
- Upload a `.txt` log file and restore the bundled sample logs.
- Export the full report to JSON or CSV.
- Automated tests.
- Docker support.

## Requirements

- Python 3.11 or newer
- VS Code (recommended)

## Run locally on Windows PowerShell

Open PowerShell in the project folder.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

If PowerShell blocks activation, run the server with the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open the dashboard at http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

## Run tests

In a second terminal, activate `.venv`, then run:

```powershell
python -m pytest -v
```

## Upload log files

The dashboard accepts UTF-8 `.txt` files up to 2 MB. Each non-empty line should use this format:

```text
YYYY-MM-DD HH:MM:SS LEVEL Message text
```

Supported levels: `INFO`, `WARNING`, and `ERROR`. Invalid lines are retained and counted as malformed. Uploads are saved locally as `uploaded_logs.txt`. Use **Restore sample logs** to return to the included example.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/health` | Health status |
| GET | `/info` | App metadata and features |
| GET | `/summary` | Log counters |
| GET | `/errors` | Error messages |
| GET | `/info-logs` | INFO entries |
| GET | `/incident` | Full report with all logs, recommendations, and context |
| POST | `/upload` | Upload UTF-8 log text using `text/plain` |
| POST | `/reset-logs` | Restore sample logs |
| GET | `/export?format=json` | Download JSON report |
| GET | `/export?format=csv` | Download CSV report |

## Docker

Build and run:

```powershell
docker build -t fde-incident-assistant .
docker run --rm -p 8000:8000 fde-incident-assistant
```

The application runs locally. Uploads inside a Docker container are not persistent after the container is removed unless you mount a volume.

## Architecture

- `main.py`: API endpoints, upload/reset, report export.
- `log_analyzer.py`: parsing, validation, metrics, severity, context, recommendations.
- `index.html`: complete frontend dashboard.
- `sample_logs.txt`: sample input.
- `tests/`: automated tests.

## Scope and limitations

This version uses explainable rule-based recommendations and does not call an external LLM. It is designed as a local portfolio/demo project, not a hardened production incident-management platform. Before production use, add authentication, authorization, audit logging, secure multi-user storage, and deployment-specific configuration. No cloud deployment or external AI provider is configured by default.
