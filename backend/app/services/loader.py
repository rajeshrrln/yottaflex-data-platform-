
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


class LoadingError(Exception):
    """Raised when a database loading operation fails."""


class SQLiteDataLoader:
    MODES = {"append", "replace", "upsert"}

    def load(
        self,
        records: list[dict[str, Any]],
        db_path: str,
        table_name: str,
        mode: str = "append",
        primary_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(records, list):
            raise LoadingError("Records must be a list")

        if not isinstance(table_name, str) or not self._valid_identifier(table_name):
            raise LoadingError("Invalid table name")

        mode = mode.lower().strip()
        if mode not in self.MODES:
            raise LoadingError(f"Unsupported load mode: {mode}")

        primary_keys = primary_keys or []

        if mode == "upsert" and not primary_keys:
            raise LoadingError("Upsert requires at least one primary key")

        if not records:
            return {
                "table": table_name,
                "mode": mode,
                "input_count": 0,
                "loaded_count": 0,
            }

        if not all(isinstance(row, dict) and row for row in records):
            raise LoadingError("Every record must be a non-empty dictionary")

        columns = list(records[0].keys())

        if any(
            not isinstance(column, str) or not self._valid_identifier(column)
            for column in columns
        ):
            raise LoadingError("Invalid column name")

        if any(set(row.keys()) != set(columns) for row in records):
            raise LoadingError("All records must contain the same columns")

        if any(key not in columns for key in primary_keys):
            raise LoadingError("Primary key column is missing from records")

        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with sqlite3.connect(path) as connection:
                connection.execute("PRAGMA foreign_keys = ON")

                self._create_table(
                    connection, table_name, records, columns, primary_keys
                )

                existing_columns = {
                    row[1]
                    for row in connection.execute(
                        f'PRAGMA table_info("{table_name}")'
                    ).fetchall()
                }

                if set(columns) != existing_columns:
                    raise LoadingError(
                        "Source columns do not match the target table schema"
                    )

                if mode == "replace":
                    connection.execute(f'DELETE FROM "{table_name}"')

                placeholders = ", ".join("?" for _ in columns)
                quoted_columns = ", ".join(f'"{column}"' for column in columns)

                if mode == "upsert":
                    updates = [
                        column for column in columns
                        if column not in primary_keys
                    ]

                    conflict_keys = ", ".join(
                        f'"{key}"' for key in primary_keys
                    )

                    if updates:
                        update_clause = ", ".join(
                            f'"{column}" = excluded."{column}"'
                            for column in updates
                        )
                        sql = (
                            f'INSERT INTO "{table_name}" ({quoted_columns}) '
                            f'VALUES ({placeholders}) '
                            f'ON CONFLICT ({conflict_keys}) '
                            f'DO UPDATE SET {update_clause}'
                        )
                    else:
                        sql = (
                            f'INSERT INTO "{table_name}" ({quoted_columns}) '
                            f'VALUES ({placeholders}) '
                            f'ON CONFLICT ({conflict_keys}) DO NOTHING'
                        )
                else:
                    sql = (
                        f'INSERT INTO "{table_name}" ({quoted_columns}) '
                        f'VALUES ({placeholders})'
                    )

                values = [
                    tuple(self._serialize(row[column]) for column in columns)
                    for row in records
                ]

                cursor = connection.executemany(sql, values)

                return {
                    "table": table_name,
                    "mode": mode,
                    "input_count": len(records),
                    "loaded_count": cursor.rowcount,
                }

        except LoadingError:
            raise
        except sqlite3.Error as exc:
            raise LoadingError(f"Database loading failed: {exc}") from exc
        except OSError as exc:
            raise LoadingError(f"Database file error: {exc}") from exc

    def _create_table(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        records: list[dict[str, Any]],
        columns: list[str],
        primary_keys: list[str],
    ) -> None:
        column_definitions = []

        for column in columns:
            sql_type = self._infer_sql_type(
                [row[column] for row in records]
            )
            column_definitions.append(f'"{column}" {sql_type}')

        if primary_keys:
            keys = ", ".join(f'"{key}"' for key in primary_keys)
            column_definitions.append(f"PRIMARY KEY ({keys})")

        definitions = ", ".join(column_definitions)

        connection.execute(
            f'CREATE TABLE IF NOT EXISTS "{table_name}" ({definitions})'
        )

    @staticmethod
    def _infer_sql_type(values: list[Any]) -> str:
        non_null = [value for value in values if value is not None]

        if not non_null:
            return "TEXT"

        if all(isinstance(value, bool) for value in non_null):
            return "INTEGER"

        if all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in non_null
        ):
            return "INTEGER"

        if all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in non_null
        ):
            return "REAL"

        return "TEXT"

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)

        return value

    @staticmethod
    def _valid_identifier(value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value))
