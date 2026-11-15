
import csv
import json

from pathlib import Path
from typing import Any


class ExtractionError(Exception):
    """Raised when source data extraction fails."""


class DataExtractor:
    """
    Reusable extraction component.

    Supports CSV and JSON input files.
    Returns records in a consistent list-of-dictionaries format.
    """

    SUPPORTED_FORMATS = {"csv", "json"}

    def extract(self, file_path: str, file_format: str) -> list[dict[str, Any]]:
        path = Path(file_path)

        file_format = file_format.lower().strip()

        if file_format not in self.SUPPORTED_FORMATS:
            raise ExtractionError(
                f"Unsupported format: {file_format}"
            )

        if not path.exists():
            raise ExtractionError(
                f"Source file not found: {file_path}"
            )

        if not path.is_file():
            raise ExtractionError(
                f"Source path is not a file: {file_path}"
            )

        try:
            if file_format == "csv":
                return self._extract_csv(path)

            if file_format == "json":
                return self._extract_json(path)

        except (OSError, UnicodeError, csv.Error, json.JSONDecodeError) as exc:
            raise ExtractionError(
                f"Failed to extract source data: {exc}"
            ) from exc

        raise ExtractionError("Unexpected extraction failure")

    def _extract_csv(self, path: Path) -> list[dict[str, Any]]:
        with path.open(
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ExtractionError(
                    "CSV file is empty or missing headers"
                )

            headers = reader.fieldnames

            if any(not header.strip() for header in headers):
                raise ExtractionError(
                    "CSV contains an empty column name"
                )

            if len(set(headers)) != len(headers):
                raise ExtractionError(
                    "CSV contains duplicate column names"
                )

            records = []

            for row in reader:
                if None in row:
                    raise ExtractionError(
                        "CSV row contains unexpected extra columns"
                    )

                records.append(dict(row))

            return records

    def _extract_json(self, path: Path) -> list[dict[str, Any]]:
        with path.open(
            mode="r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ExtractionError(
                "JSON root must be an array of objects"
            )

        if not all(isinstance(row, dict) for row in data):
            raise ExtractionError(
                "Every JSON array element must be an object"
            )

        return data
