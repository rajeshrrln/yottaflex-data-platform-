
import re
import sqlite3

from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(
    prefix="/api/datasets",
    tags=["Datasets"],
)

DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "yottaflex.db"
)


def get_connection():
    if not DATABASE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Database file not found.",
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@router.get("")
def list_datasets():
    """List tables and their record counts."""

    try:
        with get_connection() as connection:
            tables = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()

            datasets = []

            for item in tables:
                table_name = item["name"]

                count = connection.execute(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                ).fetchone()[0]

                datasets.append({
                    "name": table_name,
                    "record_count": count,
                })

            return {
                "total": len(datasets),
                "datasets": datasets,
            }

    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {exc}",
        ) from exc


@router.get("/{table_name}")
def get_dataset(
    table_name: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    """Get table schema and a preview of its records."""

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid table name.",
        )

    try:
        with get_connection() as connection:
            tables = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name = ?
            """, (table_name,)).fetchone()

            if not tables:
                raise HTTPException(
                    status_code=404,
                    detail="Dataset not found.",
                )

            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            records = connection.execute(
                f'SELECT * FROM "{table_name}" LIMIT ?',
                (limit,),
            ).fetchall()

            total = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            return {
                "name": table_name,
                "record_count": total,
                "columns": [
                    {
                        "name": column["name"],
                        "type": column["type"],
                        "nullable": not bool(column["notnull"]),
                        "primary_key": bool(column["pk"]),
                    }
                    for column in columns
                ],
                "records": [
                    dict(record) for record in records
                ],
            }

    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {exc}",
        ) from exc
