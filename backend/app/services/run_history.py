
import json
import sqlite3
import uuid

from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "yottaflex.db"
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_history_table():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                pipeline_name TEXT,
                source TEXT,
                target TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_ms REAL,
                metrics_json TEXT,
                error TEXT
            )
        """)


def start_run(config):
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    source = config.get("source", {})
    target = config.get("target", {})

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO pipeline_runs (
                run_id,
                pipeline_name,
                source,
                target,
                status,
                started_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            config.get("pipeline_name", "Untitled Pipeline"),
            source.get("path"),
            target.get("table_name"),
            "running",
            started_at,
        ))

    return run_id, started_at


def finish_run(
    run_id,
    started_at,
    status,
    result=None,
    error=None,
):
    completed_at = datetime.now(timezone.utc).isoformat()

    start_time = datetime.fromisoformat(started_at)
    end_time = datetime.fromisoformat(completed_at)

    duration_ms = (
        end_time - start_time
    ).total_seconds() * 1000

    result = result or {}

    with get_connection() as connection:
        connection.execute("""
            UPDATE pipeline_runs
            SET status = ?,
                completed_at = ?,
                duration_ms = ?,
                metrics_json = ?,
                error = ?
            WHERE run_id = ?
        """, (
            status,
            completed_at,
            duration_ms,
            json.dumps(result.get("metrics", {})),
            error,
            run_id,
        ))


def get_run_history(limit=50):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

    history = []

    for row in rows:
        item = dict(row)
        item["metrics"] = json.loads(
            item.pop("metrics_json") or "{}"
        )
        history.append(item)

    return history
