from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_incident_contains_all_levels_and_context():
    response = client.get("/incident")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["error_count"] >= 1
    assert data["summary"]["warning_count"] >= 1
    assert any(item["level"] == "INFO" for item in data["logs"])
    assert "context_before" in data["logs"][0]


def test_export_json():
    response = client.get("/export?format=json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_export_csv():
    response = client.get("/export?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


def test_bad_export_format():
    response = client.get("/export?format=xml")
    assert response.status_code == 400


def test_upload_and_reset(monkeypatch, tmp_path):
    sample = tmp_path / "sample_logs.txt"
    uploaded = tmp_path / "uploaded_logs.txt"
    sample.write_text("2026-10-21 10:00:00 INFO Test sample\n", encoding="utf-8")
    monkeypatch.setattr(main, "SAMPLE_LOG_FILE", sample)
    monkeypatch.setattr(main, "UPLOADED_LOG_FILE", uploaded)

    response = client.post(
        "/upload",
        content="2026-10-21 10:01:00 ERROR Test uploaded failure\n",
        headers={"content-type": "text/plain"},
    )
    assert response.status_code == 200
    assert response.json()["summary"]["error_count"] == 1

    response = client.post("/reset-logs")
    assert response.status_code == 200
    assert response.json()["source_file"] == sample.name
    assert not uploaded.exists()


def test_upload_rejects_empty():
    response = client.post("/upload", content="   ")
    assert response.status_code == 400
