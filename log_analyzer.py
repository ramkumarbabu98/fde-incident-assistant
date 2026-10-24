from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2})\s+"
    r"(\d{2}:\d{2}:\d{2})\s+"
    r"(INFO|WARNING|ERROR)\s+(.+)$"
)


def read_log_lines(log_file: Path) -> list[str]:
    with log_file.open("r", encoding="utf-8-sig") as file:
        return [line.strip() for line in file if line.strip()]


def parse_log_line(line: str, index: int = 0) -> dict:
    match = LOG_PATTERN.fullmatch(line.strip())
    if not match:
        return {
            "index": index,
            "timestamp": None,
            "level": "MALFORMED",
            "message": line.strip(),
            "valid": False,
        }

    timestamp_text = f"{match.group(1)} {match.group(2)}"
    try:
        datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return {
            "index": index,
            "timestamp": None,
            "level": "MALFORMED",
            "message": line.strip(),
            "valid": False,
        }

    return {
        "index": index,
        "timestamp": timestamp_text,
        "level": match.group(3),
        "message": match.group(4).strip(),
        "valid": True,
    }


def extract_log_level(line: str) -> str | None:
    parsed = parse_log_line(line)
    return parsed["level"] if parsed["valid"] else None


def analyze_logs(logs: list[str]) -> dict:
    parsed = [parse_log_line(line, index) for index, line in enumerate(logs)]
    valid = [item for item in parsed if item["valid"]]
    return {
        "total_logs": len(valid),
        "info_count": sum(item["level"] == "INFO" for item in valid),
        "warning_count": sum(item["level"] == "WARNING" for item in valid),
        "error_count": sum(item["level"] == "ERROR" for item in valid),
        "malformed_count": len(parsed) - len(valid),
    }


def extract_error_messages(logs: list[str]) -> list[str]:
    return [
        parsed["message"]
        for line in logs
        if (parsed := parse_log_line(line))["valid"] and parsed["level"] == "ERROR"
    ]


def determine_severity(summary: dict) -> str:
    if summary.get("error_count", 0) > 0:
        return "HIGH"
    if summary.get("warning_count", 0) > 0:
        return "MEDIUM"
    return "LOW"


def recommend_for_message(message: str, level: str) -> str:
    text = message.lower()

    if "database" in text or "sql" in text:
        return "Check database availability, connectivity, credentials, connection pool usage, and recent database changes."
    if "payment" in text:
        return "Check payment-service health, dependency status, recent deployments, and failed transaction traces."
    if "timeout" in text or "response time" in text or "latency" in text:
        return "Inspect latency metrics, resource saturation, slow dependencies, and timeout thresholds."
    if "connection" in text or "network" in text:
        return "Verify network connectivity, DNS resolution, service availability, and connection settings."
    if "memory" in text or "out of memory" in text:
        return "Check memory utilization, recent memory growth, container limits, and application heap settings."
    if "disk" in text or "space" in text:
        return "Check disk utilization, log growth, inode usage, and retention/cleanup policies."
    if level == "WARNING":
        return "Review the warning trend and surrounding logs; compare latency, resource use, and service metrics before escalation."
    if level == "MALFORMED":
        return "Check the source log format, timestamp validity, and log pipeline configuration."
    return "Inspect surrounding application logs, recent changes, and relevant service metrics to narrow down the cause."


def generate_recommendations(error_messages: list[str]) -> list[dict[str, str]]:
    return [
        {"error": message, "recommendation": recommend_for_message(message, "ERROR")}
        for message in error_messages
    ]


def build_incident_report(logs: list[str], source_file: str = "sample_logs.txt") -> dict:
    parsed = [parse_log_line(line, index) for index, line in enumerate(logs)]
    summary = analyze_logs(logs)
    total_lines = len(parsed)
    enriched = []

    for position, item in enumerate(parsed):
        before = parsed[max(0, position - 2):position]
        after = parsed[position + 1:position + 3]
        enriched.append({
            "id": position + 1,
            "line_number": position + 1,
            "timestamp": item["timestamp"],
            "level": item["level"],
            "message": item["message"],
            "valid": item["valid"],
            "recommendation": (
                recommend_for_message(item["message"], item["level"])
                if item["level"] in {"ERROR", "WARNING", "MALFORMED"}
                else "No action normally required; retain for diagnostic context."
            ),
            "context_before": [
                f'{x["timestamp"] or "Invalid timestamp"} {x["level"]}: {x["message"]}'
                for x in before
            ],
            "context_after": [
                f'{x["timestamp"] or "Invalid timestamp"} {x["level"]}: {x["message"]}'
                for x in after
            ],
        })

    errors = [item["message"] for item in enriched if item["level"] == "ERROR"]
    return {
        "project": "FDE Incident Assistant",
        "version": "2.0.0",
        "source_file": source_file,
        "severity": determine_severity(summary),
        "summary": summary,
        "errors": errors,
        "recommendations": [
            {
                "error": item["message"],
                "recommendation": item["recommendation"],
                "timestamp": item["timestamp"],
                "line_number": item["line_number"],
            }
            for item in enriched if item["level"] == "ERROR"
        ],
        "logs": enriched,
        "total_lines": total_lines,
    }
