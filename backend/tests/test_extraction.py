
import json

import pytest

from app.services.extraction import DataExtractor, ExtractionError


@pytest.fixture
def extractor():
    return DataExtractor()


def test_extract_valid_csv(tmp_path, extractor):
    file = tmp_path / "customers.csv"
    file.write_text(
        "customer_id,customer_name\n"
        "101,Rajesh\n"
        "102,Arun\n",
        encoding="utf-8"
    )

    result = extractor.extract(str(file), "csv")

    assert len(result) == 2
    assert result[0]["customer_id"] == "101"
    assert result[1]["customer_name"] == "Arun"


def test_extract_valid_json(tmp_path, extractor):
    file = tmp_path / "customers.json"
    data = [
        {"customer_id": 101, "customer_name": "Rajesh"},
        {"customer_id": 102, "customer_name": "Arun"}
    ]

    file.write_text(json.dumps(data), encoding="utf-8")

    result = extractor.extract(str(file), "json")

    assert len(result) == 2
    assert result[0]["customer_id"] == 101


def test_missing_file_raises_error(extractor):
    with pytest.raises(ExtractionError, match="Source file not found"):
        extractor.extract("missing.csv", "csv")


def test_unsupported_format_raises_error(tmp_path, extractor):
    file = tmp_path / "data.txt"
    file.write_text("sample", encoding="utf-8")

    with pytest.raises(ExtractionError, match="Unsupported format"):
        extractor.extract(str(file), "txt")


def test_empty_csv_raises_error(tmp_path, extractor):
    file = tmp_path / "empty.csv"
    file.write_text("", encoding="utf-8")

    with pytest.raises(ExtractionError, match="empty or missing headers"):
        extractor.extract(str(file), "csv")


def test_malformed_json_raises_error(tmp_path, extractor):
    file = tmp_path / "invalid.json"
    file.write_text("{invalid json}", encoding="utf-8")

    with pytest.raises(ExtractionError, match="Failed to extract"):
        extractor.extract(str(file), "json")


def test_json_root_must_be_array(tmp_path, extractor):
    file = tmp_path / "object.json"
    file.write_text('{"customer_id": 101}', encoding="utf-8")

    with pytest.raises(ExtractionError, match="root must be an array"):
        extractor.extract(str(file), "json")


def test_json_array_elements_must_be_objects(tmp_path, extractor):
    file = tmp_path / "invalid_structure.json"
    file.write_text('[{"customer_id": 101}, "invalid"]', encoding="utf-8")

    with pytest.raises(ExtractionError, match="Every JSON array element"):
        extractor.extract(str(file), "json")
