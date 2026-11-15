
import sqlite3

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_pipeline_endpoint_rejects_empty_config():
    response = client.post(
        "/api/pipelines/run",
        json={"config": {}},
    )
    assert response.status_code == 400
    assert "Missing or invalid" in response.json()["detail"]


def test_pipeline_endpoint_rejects_missing_config():
    response = client.post(
        "/api/pipelines/run",
        json={},
    )
    assert response.status_code == 422


def test_pipeline_endpoint_success(tmp_path):
    csv_file = tmp_path / "customers.csv"
    csv_file.write_text(
        "customer_id,name,email,age\n"
        "1,Rajesh,rajesh@example.com,21\n",
        encoding="utf-8",
    )

    database = tmp_path / "test.db"

    config = {
        "source": {
            "path": str(csv_file),
            "format": "csv",
        },
        "schema": {
            "columns": [
                {"name": "customer_id", "type": "integer", "nullable": False},
                {"name": "name", "type": "string", "nullable": False},
                {"name": "email", "type": "string", "nullable": False},
                {"name": "age", "type": "integer", "nullable": True},
            ],
            "primary_keys": ["customer_id"],
        },
        "target": {
            "db_path": str(database),
            "table_name": "customers",
            "load_mode": "upsert",
            "primary_keys": ["customer_id"],
        },
    }

    response = client.post(
        "/api/pipelines/run",
        json={"config": config},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["metrics"]["loaded_count"] == 1

    with sqlite3.connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    assert count == 1
