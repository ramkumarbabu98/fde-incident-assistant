from log_analyzer import analyze_logs, build_incident_report, parse_log_line, determine_severity


def test_counts_valid_levels_and_malformed():
    logs = [
        "2026-10-21 10:00:00 INFO Started",
        "2026-10-21 10:00:01 WARNING Slow",
        "2026-10-21 10:00:02 ERROR Failed",
        "not a valid log",
    ]
    assert analyze_logs(logs) == {
        "total_logs": 3,
        "info_count": 1,
        "warning_count": 1,
        "error_count": 1,
        "malformed_count": 1,
    }


def test_invalid_date_is_malformed():
    parsed = parse_log_line("2026-99-99 10:00:00 ERROR Broken date")
    assert parsed["level"] == "MALFORMED"
    assert parsed["valid"] is False


def test_severity():
    assert determine_severity({"error_count": 1, "warning_count": 0}) == "HIGH"
    assert determine_severity({"error_count": 0, "warning_count": 1}) == "MEDIUM"
    assert determine_severity({"error_count": 0, "warning_count": 0}) == "LOW"


def test_report_has_context_and_recommendations():
    report = build_incident_report([
        "2026-10-21 10:00:00 INFO Started",
        "2026-10-21 10:00:01 ERROR Database connection failed",
        "2026-10-21 10:00:02 WARNING Response time exceeded",
    ])
    error = report["logs"][1]
    assert error["timestamp"] == "2026-10-21 10:00:01"
    assert error["context_before"]
    assert "database" in error["recommendation"].lower()
    assert report["summary"]["warning_count"] == 1
