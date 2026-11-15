
import json
import sqlite3

import pytest

from app.services.pipeline_orchestrator import (
    PipelineOrchestrator,
    PipelineExecutionError,
)


@pytest.fixture
def pipeline_files(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    csv_path = data_dir / "customers.csv"
    csv_path.write_text(
        "customer_id,name,email,age\n"
        "1,Rajesh,rajesh@example.com,21\n"
        "2,Arun,arun@example.com,25\n"
        "3,Invalid,invalid-email,30\n"
        "4,MissingEmail,,22\n",
        encoding="utf-8",
    )

    return {
        "csv": str(csv_path),
        "database": str(data_dir / "test.db"),
    }


@pytest.fixture
def pipeline_config(pipeline_files):
    return {
        "source": {
            "path": pipeline_files["csv"],
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
        "business_rules": [
            {
                "field": "email",
                "type": "email",
                "nullable": False,
            },
        ],
        "transformation": {
            "strip_whitespace": True,
        },
        "target": {
            "db_path": pipeline_files["database"],
            "table_name": "customers",
            "load_mode": "upsert",
            "primary_keys": ["customer_id"],
        },
    }


def read_customers(database):
    with sqlite3.connect(database) as connection:
        return connection.execute(
            "SELECT customer_id, name, email, age "
            "FROM customers ORDER BY customer_id"
        ).fetchall()


def test_pipeline_end_to_end(pipeline_config, pipeline_files):
    orchestrator = PipelineOrchestrator()

    result = orchestrator.run(pipeline_config)

    assert result["status"] == "success"
    assert result["metrics"]["extracted_count"] == 4
    assert result["metrics"]["schema_valid_count"] == 3
    assert result["metrics"]["business_valid_count"] == 2
    assert result["metrics"]["loaded_count"] == 2
    assert result["metrics"]["rejected_count"] == 2

    assert len(read_customers(pipeline_files["database"])) == 2


def test_pipeline_rejected_records_include_stage(
    pipeline_config,
):
    result = PipelineOrchestrator().run(pipeline_config)

    stages = {item["stage"] for item in result["rejected_records"]}

    assert "schema_validation" in stages
    assert "business_rule_validation" in stages


def test_pipeline_upsert_is_safe_to_rerun(
    pipeline_config,
    pipeline_files,
):
    orchestrator = PipelineOrchestrator()

    first_result = orchestrator.run(pipeline_config)
    second_result = orchestrator.run(pipeline_config)

    assert first_result["metrics"]["loaded_count"] == 2
    assert second_result["metrics"]["loaded_count"] == 2
    assert len(read_customers(pipeline_files["database"])) == 2


def test_pipeline_empty_csv(
    pipeline_config,
    pipeline_files,
):
    empty_csv = pipeline_files["csv"]
    with open(empty_csv, "w", encoding="utf-8") as file:
        file.write("customer_id,name,email,age\n")

    result = PipelineOrchestrator().run(pipeline_config)

    assert result["status"] == "success"
    assert result["metrics"]["extracted_count"] == 0
    assert result["metrics"]["loaded_count"] == 0


def test_pipeline_invalid_configuration():
    with pytest.raises(PipelineExecutionError, match="Missing or invalid"):
        PipelineOrchestrator().run({})


def test_pipeline_missing_source_file(
    pipeline_config,
):
    pipeline_config["source"]["path"] = "missing.csv"

    with pytest.raises(PipelineExecutionError, match="extraction"):
        PipelineOrchestrator().run(pipeline_config)


def test_pipeline_invalid_load_mode(pipeline_config):
    pipeline_config["target"]["load_mode"] = "invalid"

    with pytest.raises(PipelineExecutionError, match="loading"):
        PipelineOrchestrator().run(pipeline_config)


def test_pipeline_loads_json_source(tmp_path):
    json_path = tmp_path / "customers.json"
    json_path.write_text(
        json.dumps([
            {
                "customer_id": 1,
                "name": "Rajesh",
                "email": "rajesh@example.com",
                "age": 21,
            }
        ]),
        encoding="utf-8",
    )

    config = {
        "source": {
            "path": str(json_path),
            "format": "json",
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
            "db_path": str(tmp_path / "json.db"),
            "table_name": "customers",
            "load_mode": "upsert",
            "primary_keys": ["customer_id"],
        },
    }

    result = PipelineOrchestrator().run(config)

    assert result["status"] == "success"
    assert result["metrics"]["loaded_count"] == 1
