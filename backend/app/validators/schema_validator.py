
from typing import Any


class SchemaValidationError(Exception):
    """Raised when the schema configuration is invalid."""


class SchemaValidator:
    """
    Reusable metadata-driven schema validator.

    Supports:
    - Required and nullable fields
    - Data type validation
    - Unexpected and missing columns
    - Primary key validation
    - Duplicate detection
    """

    SUPPORTED_TYPES = {
        "string",
        "integer",
        "float",
        "number",
        "boolean"
    }

    def validate(
        self,
        records: list[dict[str, Any]],
        schema: dict[str, Any]
    ) -> dict[str, Any]:

        columns = schema.get("columns")
        primary_keys = schema.get("primary_keys", [])

        if not isinstance(columns, list) or not columns:
            raise SchemaValidationError(
                "Schema must contain a non-empty columns list"
            )

        column_names = []

        for column in columns:
            if not isinstance(column, dict):
                raise SchemaValidationError(
                    "Each column definition must be an object"
                )

            name = column.get("name")
            data_type = column.get("type")

            if not isinstance(name, str) or not name.strip():
                raise SchemaValidationError(
                    "Every column must have a valid name"
                )

            if name in column_names:
                raise SchemaValidationError(
                    f"Duplicate schema column: {name}"
                )

            if data_type not in self.SUPPORTED_TYPES:
                raise SchemaValidationError(
                    f"Unsupported data type: {data_type}"
                )

            column_names.append(name)

        if not isinstance(primary_keys, list):
            raise SchemaValidationError(
                "primary_keys must be a list"
            )

        if not all(key in column_names for key in primary_keys):
            raise SchemaValidationError(
                "Primary key references an undefined column"
            )

        if not isinstance(records, list):
            raise SchemaValidationError(
                "Records must be provided as a list"
            )

        expected_columns = set(column_names)
        valid_records = []
        rejected_records = []
        seen_keys = set()

        for row_number, record in enumerate(records, start=1):

            issues = []

            if not isinstance(record, dict):
                rejected_records.append({
                    "source_row": row_number,
                    "source_record": record,
                    "issues": ["Record must be an object"]
                })
                continue

            actual_columns = set(record.keys())

            missing_columns = expected_columns - actual_columns
            unexpected_columns = actual_columns - expected_columns

            for column in sorted(missing_columns):
                issues.append(f"Missing column: {column}")

            for column in sorted(unexpected_columns):
                issues.append(f"Unexpected column: {column}")

            for column in columns:

                name = column["name"]
                value = record.get(name)
                nullable = column.get("nullable", True)
                data_type = column["type"]

                is_null = value is None or (
                    isinstance(value, str) and not value.strip()
                )

                if is_null:
                    if not nullable:
                        issues.append(
                            f"{name} cannot be null"
                        )
                    continue

                if not self._is_valid_type(value, data_type):
                    issues.append(
                        f"{name} must be of type {data_type}"
                    )

            if not issues and primary_keys:

                key_values = tuple(
                    self._normalize_key(record[key])
                    for key in primary_keys
                )

                if any(value is None for value in key_values):
                    issues.append("Primary key cannot be null")

                elif key_values in seen_keys:
                    issues.append(
                        f"Duplicate primary key: {key_values}"
                    )

                else:
                    seen_keys.add(key_values)

            if issues:
                rejected_records.append({
                    "source_row": row_number,
                    "source_record": record,
                    "issues": issues
                })
            else:
                valid_records.append({
                    **record,
                    "_source_row": row_number
                })

        return {
            "total_records": len(records),
            "valid_count": len(valid_records),
            "rejected_count": len(rejected_records),
            "valid_records": valid_records,
            "rejected_records": rejected_records
        }

    @staticmethod
    def _normalize_key(value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()

        return value

    @staticmethod
    def _is_valid_type(value: Any, data_type: str) -> bool:

        if data_type == "string":
            return isinstance(value, str)

        if data_type == "integer":
            if isinstance(value, bool):
                return False

            if isinstance(value, int):
                return True

            if isinstance(value, str):
                try:
                    int(value.strip())
                    return True
                except ValueError:
                    return False

            return False

        if data_type in {"float", "number"}:
            if isinstance(value, bool):
                return False

            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False

        if data_type == "boolean":
            return isinstance(value, bool) or (
                isinstance(value, str)
                and value.strip().lower() in {
                    "true", "false", "1", "0"
                }
            )

        return False
