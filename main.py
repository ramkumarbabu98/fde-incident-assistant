from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from log_analyzer import (
    analyze_logs,
    build_incident_report,
    determine_severity,
    extract_error_messages,
    generate_recommendations,
    read_log_lines,
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_LOG_FILE = BASE_DIR / "sample_logs.txt"
UPLOADED_LOG_FILE = BASE_DIR / "uploaded_logs.txt"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024

app = FastAPI(
    title="FDE Incident Assistant",
    description="A local-first application log analysis and incident triage API.",
    version="2.0.0",
)


def active_log_file() -> Path:
    return UPLOADED_LOG_FILE if UPLOADED_LOG_FILE.exists() else SAMPLE_LOG_FILE


def get_current_report() -> dict:
    path = active_log_file()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    lines = read_log_lines(path)
    return build_incident_report(lines, source_file=path.name)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "project": "FDE Incident Assistant",
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/info")
def info():
    return {
        "project": "FDE Incident Assistant",
        "description": "Log analysis, incident triage, recommendations, and report export.",
        "active_log_file": active_log_file().name,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "features": [
            "log-level classification",
            "malformed-entry detection",
            "incident severity",
            "rule-based recommendations",
            "keyword search and filters",
            "auto-refresh",
            "incident details and context",
            "JSON and CSV export",
            "log file upload and reset",
        ],
    }


@app.get("/summary")
def summary():
    report = get_current_report()
    return report["summary"]


@app.get("/errors")
def errors():
    report = get_current_report()
    return report["errors"]


@app.get("/info-logs")
def info_logs():
    report = get_current_report()
    return [item for item in report["logs"] if item["level"] == "INFO"]


@app.get("/incident")
def incident():
    return get_current_report()


@app.post("/upload")
async def upload_logs(request: Request):
    body = await request.body()
    if not body.strip():
        raise HTTPException(status_code=400, detail="Uploaded log file is empty")
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Log file exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    try:
        content = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Log file must be UTF-8 text") from exc

    UPLOADED_LOG_FILE.write_text(content, encoding="utf-8")
    report = get_current_report()
    return {
        "message": "Log file uploaded and analyzed",
        "source_file": UPLOADED_LOG_FILE.name,
        "summary": report["summary"],
        "severity": report["severity"],
    }


@app.post("/reset-logs")
def reset_logs():
    if UPLOADED_LOG_FILE.exists():
        UPLOADED_LOG_FILE.unlink()
    report = get_current_report()
    return {
        "message": "Sample logs restored",
        "source_file": SAMPLE_LOG_FILE.name,
        "summary": report["summary"],
        "severity": report["severity"],
    }


@app.get("/export")
def export_report(format: str = "json"):
    report = get_current_report()
    if format.lower() == "json":
        content = json.dumps(report, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="incident-report.json"'},
        )

    if format.lower() == "csv":
        output = io.StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp", "level", "message", "recommendation",
                "context_before", "context_after",
            ],
        )
        writer.writeheader()
        for item in report["logs"]:
            writer.writerow({
                "timestamp": item["timestamp"] or "",
                "level": item["level"],
                "message": item["message"],
                "recommendation": item["recommendation"] or "",
                "context_before": " | ".join(item["context_before"]),
                "context_after": " | ".join(item["context_after"]),
            })
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="incident-report.csv"'},
        )

    raise HTTPException(status_code=400, detail="Unsupported format. Use json or csv.")
