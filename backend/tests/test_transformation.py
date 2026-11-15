
import pytest

from app.services.transformation import (
    DataTransformer,
    TransformationError
)


@pytest.fixture
def transformer():
    return DataTransformer()


def test_rename_columns(transformer):
    result = transformer.transform(
        [{"CustomerID": "101"}],
        {"rename_columns": {"CustomerID": "customer_id"}}
    )

    assert result[0]["customer_id"] == "101"
    assert "CustomerID" not in result[0]


def test_strip_whitespace(transformer):
    result = transformer.transform(
        [{"name": " Rajesh "}],
        {"strip_whitespace": True}
    )

    assert result[0]["name"] == "Rajesh"


def test_integer_conversion(transformer):
    result = transformer.transform(
        [{"age": "21"}],
        {"type_conversions": {"age": "integer"}}
    )

    assert result[0]["age"] == 21
    assert isinstance(result[0]["age"], int)


def test_float_conversion(transformer):
    result = transformer.transform(
        [{"amount": "125.50"}],
        {"type_conversions": {"amount": "float"}}
    )

    assert result[0]["amount"] == 125.50


def test_boolean_conversion(transformer):
    result = transformer.transform(
        [{"active": "true"}],
        {"type_conversions": {"active": "boolean"}}
    )

    assert result[0]["active"] is True


def test_invalid_integer_conversion(transformer):
    with pytest.raises(TransformationError):
        transformer.transform(
            [{"age": "invalid"}],
            {"type_conversions": {"age": "integer"}}
        )


def test_timestamp_normalization(transformer):
    result = transformer.transform(
        [{"created_at": "2026-11-15T10:00:00+05:30"}],
        {"timestamps": ["created_at"]}
    )

    assert result[0]["created_at"] == "2026-11-15T04:30:00Z"


def test_derived_constant(transformer):
    result = transformer.transform(
        [{"customer_id": 101}],
        {
            "derived_fields": [
                {
                    "name": "source",
                    "operation": "constant",
                    "value": "customer_import"
                }
            ]
        }
    )

    assert result[0]["source"] == "customer_import"


def test_derived_concat(transformer):
    result = transformer.transform(
        [{"first": "Rajesh", "last": "Kumar"}],
        {
            "derived_fields": [
                {
                    "name": "full_name",
                    "operation": "concat",
                    "fields": ["first", "last"]
                }
            ]
        }
    )

    assert result[0]["full_name"] == "Rajesh Kumar"


def test_derived_sum(transformer):
    result = transformer.transform(
        [{"price": 100, "tax": 18}],
        {
            "derived_fields": [
                {
                    "name": "total",
                    "operation": "sum",
                    "fields": ["price", "tax"]
                }
            ]
        }
    )

    assert result[0]["total"] == 118


def test_empty_input(transformer):
    result = transformer.transform([], {})

    assert result == []


def test_source_records_are_not_modified(transformer):
    original = [{"name": " Rajesh "}]

    transformer.transform(
        original,
        {"strip_whitespace": True}
    )

    assert original[0]["name"] == " Rajesh "


def test_duplicate_target_column(transformer):
    with pytest.raises(TransformationError):
        transformer.transform(
            [{"name": "Rajesh", "full_name": "Existing"}],
            {
                "derived_fields": [
                    {
                        "name": "full_name",
                        "operation": "copy",
                        "source": "name"
                    }
                ]
            }
        )
