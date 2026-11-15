
from datetime import datetime, timezone
from typing import Any


class TransformationError(Exception):
    """Raised when a data transformation fails."""


class DataTransformer:
    """
    Reusable, configuration-driven transformation engine.

    Supported operations:
    - Column renaming
    - Whitespace cleaning
    - Data type conversion
    - Timestamp normalization
    - Derived columns
    """

    SUPPORTED_TYPES = {
        "string",
        "integer",
        "float",
        "boolean"
    }

    def transform(
        self,
        records: list[dict[str, Any]],
        config: dict[str, Any]
    ) -> list[dict[str, Any]]:

        if not isinstance(records, list):
            raise TransformationError("Records must be a list")

        if not isinstance(config, dict):
            raise TransformationError("Configuration must be an object")

        transformed = []

        for row_number, record in enumerate(records, start=1):

            if not isinstance(record, dict):
                raise TransformationError(
                    f"Record at row {row_number} must be an object"
                )

            row = record.copy()

            try:
                row = self._rename_columns(
                    row, config.get("rename_columns", {})
                )

                row = self._clean_strings(
                    row, config.get("strip_whitespace", False)
                )

                row = self._convert_types(
                    row, config.get("type_conversions", {})
                )

                row = self._normalize_timestamps(
                    row, config.get("timestamps", [])
                )

                row = self._derive_columns(
                    row, config.get("derived_fields", [])
                )

            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                raise TransformationError(
                    f"Transformation failed at source row {row_number}: {exc}"
                ) from exc

            transformed.append(row)

        return transformed

    def _rename_columns(self, record, mappings):

        if not isinstance(mappings, dict):
            raise TransformationError(
                "rename_columns must be an object"
            )

        for old_name, new_name in mappings.items():

            if old_name in record:
                if new_name in record and old_name != new_name:
                    raise TransformationError(
                        f"Cannot rename {old_name}: {new_name} already exists"
                    )

                record[new_name] = record.pop(old_name)

        return record

    def _clean_strings(self, record, enabled):

        if not isinstance(enabled, bool):
            raise TransformationError(
                "strip_whitespace must be a boolean"
            )

        if enabled:
            for key, value in record.items():
                if isinstance(value, str):
                    record[key] = value.strip()

        return record

    def _convert_types(self, record, conversions):

        if not isinstance(conversions, dict):
            raise TransformationError(
                "type_conversions must be an object"
            )

        for field, target_type in conversions.items():

            if target_type not in self.SUPPORTED_TYPES:
                raise TransformationError(
                    f"Unsupported conversion type: {target_type}"
                )

            if field not in record or record[field] is None:
                continue

            value = record[field]

            if isinstance(value, str) and not value.strip():
                continue

            if target_type == "string":
                record[field] = str(value)

            elif target_type == "integer":
                if isinstance(value, bool):
                    raise ValueError(
                        f"{field} cannot convert boolean to integer"
                    )
                record[field] = int(value)

            elif target_type == "float":
                if isinstance(value, bool):
                    raise ValueError(
                        f"{field} cannot convert boolean to float"
                    )
                record[field] = float(value)

            elif target_type == "boolean":
                if isinstance(value, bool):
                    record[field] = value

                elif isinstance(value, str):
                    normalized = value.strip().lower()

                    if normalized in {"true", "1"}:
                        record[field] = True
                    elif normalized in {"false", "0"}:
                        record[field] = False
                    else:
                        raise ValueError(
                            f"Invalid boolean value for {field}"
                        )

                elif value in (0, 1):
                    record[field] = bool(value)

                else:
                    raise ValueError(
                        f"Invalid boolean value for {field}"
                    )

        return record

    def _normalize_timestamps(self, record, fields):

        if not isinstance(fields, list):
            raise TransformationError(
                "timestamps must be a list"
            )

        for field in fields:

            if field not in record or record[field] is None:
                continue

            value = record[field]

            if not isinstance(value, str):
                raise ValueError(
                    f"Timestamp field {field} must be a string"
                )

            parsed = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            else:
                parsed = parsed.astimezone(timezone.utc)

            record[field] = (
                parsed.isoformat().replace("+00:00", "Z")
            )

        return record

    def _derive_columns(self, record, definitions):

        if not isinstance(definitions, list):
            raise TransformationError(
                "derived_fields must be a list"
            )

        for definition in definitions:

            if not isinstance(definition, dict):
                raise TransformationError(
                    "Each derived field must be an object"
                )

            name = definition.get("name")
            operation = definition.get("operation")

            if not isinstance(name, str) or not name.strip():
                raise TransformationError(
                    "Derived field requires a valid name"
                )

            if name in record:
                raise TransformationError(
                    f"Derived field already exists: {name}"
                )

            if operation == "copy":
                source = definition["source"]
                record[name] = record[source]

            elif operation == "constant":
                record[name] = definition["value"]

            elif operation == "concat":
                fields = definition["fields"]
                separator = definition.get("separator", " ")

                if not isinstance(fields, list) or not fields:
                    raise TransformationError(
                        "Concat requires a non-empty fields list"
                    )

                record[name] = separator.join(
                    str(record[field]) for field in fields
                )

            elif operation == "sum":
                fields = definition["fields"]

                if not isinstance(fields, list) or not fields:
                    raise TransformationError(
                        "Sum requires a non-empty fields list"
                    )

                values = [record[field] for field in fields]

                if any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    for value in values
                ):
                    raise TransformationError(
                        "Sum fields must contain numeric values"
                    )

                record[name] = sum(values)

            else:
                raise TransformationError(
                    f"Unsupported derived operation: {operation}"
                )

        return record
