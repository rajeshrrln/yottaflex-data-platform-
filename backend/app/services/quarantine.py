
import json
import uuid

from datetime import datetime, timezone

from app.services.run_history import get_connection


def initialize_quarantine_table():
    """Create the persistent rejected-record storage table."""

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS quarantined_records (
                quarantine_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                source_path TEXT,
                source_row INTEGER,
                stage TEXT NOT NULL,
                source_record TEXT,
                issues TEXT,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_quarantine_run_id
            ON quarantined_records(run_id)
        """)


def save_quarantined_records(
    run_id,
    source_path,
    rejected_records,
):
    """Persist rejected records and their validation reasons."""

    if not rejected_records:
        return 0

    created_at = datetime.now(timezone.utc).isoformat()

    rows = []

    for item in rejected_records:
        source_record = item.get("source_record", {})

        if not isinstance(source_record, dict):
            source_record = {}

        source_row = item.get("source_row")

        if source_row is None:
            source_row = source_record.get("_source_row")

        rows.append((
            str(uuid.uuid4()),
            run_id,
            source_path,
            source_row,
            item.get("stage", "unknown"),
            json.dumps(source_record, default=str),
            json.dumps(item.get("issues", []), default=str),
            created_at,
        ))

    with get_connection() as connection:
        connection.executemany("""
            INSERT INTO quarantined_records (
                quarantine_id,
                run_id,
                source_path,
                source_row,
                stage,
                source_record,
                issues,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    return len(rows)


def get_quarantined_records(limit=100, run_id=None):
    """Retrieve persisted rejected records."""

    query = """
        SELECT *
        FROM quarantined_records
    """

    params = []

    if run_id:
        query += " WHERE run_id = ?"
        params.append(run_id)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    records = []

    for row in rows:
        item = dict(row)

        item["source_record"] = json.loads(
            item.pop("source_record") or "{}"
        )

        item["issues"] = json.loads(
            item.pop("issues") or "[]"
        )

        records.append(item)

    return records


def get_quarantine_summary():
    """Return quarantine record counts grouped by validation stage."""

    with get_connection() as connection:
        total = connection.execute("""
            SELECT COUNT(*) AS count
            FROM quarantined_records
        """).fetchone()["count"]

        stages = connection.execute("""
            SELECT stage, COUNT(*) AS count
            FROM quarantined_records
            GROUP BY stage
        """).fetchall()

    return {
        "total": total,
        "by_stage": {
            row["stage"]: row["count"]
            for row in stages
        },
    }
