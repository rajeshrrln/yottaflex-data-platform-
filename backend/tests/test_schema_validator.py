
import pytest

from app.validators.schema_validator import (
    SchemaValidator,
    SchemaValidationError
)


@pytest.fixture
def validator():
    return SchemaValidator()


@pytest.fixture
def customer_schema():
    return {
        "columns": [
            {
                "name": "customer_id",
                "type": "integer",
                "nullable": False
            },
            {
                "name": "customer_name",
                "type": "string",
                "nullable": False
            },
            {
                "name": "email",
                "type": "string",
                "nullable": True
            },
            {
                "name": "age",
                "type": "integer",
                "nullable": False
            }
        ],
        "primary_keys": ["customer_id"]
    }


def test_valid_records(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "Rajesh",
            "email": "rajesh@example.com",
            "age": "21"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["total_records"] == 1
    assert result["valid_count"] == 1
    assert result["rejected_count"] == 0


def test_empty_input(validator, customer_schema):
    result = validator.validate([], customer_schema)

    assert result["total_records"] == 0
    assert result["valid_count"] == 0
    assert result["rejected_count"] == 0


def test_missing_required_field(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "",
            "email": "rajesh@example.com",
            "age": "21"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["rejected_count"] == 1
    assert any(
        "customer_name cannot be null" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_invalid_data_type(validator, customer_schema):
    records = [
        {
            "customer_id": "ABC",
            "customer_name": "Rajesh",
            "email": "rajesh@example.com",
            "age": "21"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["rejected_count"] == 1
    assert any(
        "customer_id must be of type integer" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_duplicate_primary_key(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "Rajesh",
            "email": "rajesh@example.com",
            "age": "21"
        },
        {
            "customer_id": "101",
            "customer_name": "Arun",
            "email": "arun@example.com",
            "age": "24"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["valid_count"] == 1
    assert result["rejected_count"] == 1
    assert any(
        "Duplicate primary key" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_missing_column(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "Rajesh",
            "age": "21"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["rejected_count"] == 1
    assert any(
        "Missing column: email" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_unexpected_column(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "Rajesh",
            "email": "rajesh@example.com",
            "age": "21",
            "city": "Hyderabad"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["rejected_count"] == 1
    assert any(
        "Unexpected column: city" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_nullable_field_accepts_null(validator, customer_schema):
    records = [
        {
            "customer_id": "101",
            "customer_name": "Rajesh",
            "email": None,
            "age": "21"
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["valid_count"] == 1
    assert result["rejected_count"] == 0


def test_invalid_schema_raises_error(validator):
    invalid_schema = {
        "columns": [
            {
                "name": "customer_id",
                "type": "datetime",
                "nullable": False
            }
        ],
        "primary_keys": ["customer_id"]
    }

    with pytest.raises(
        SchemaValidationError,
        match="Unsupported data type"
    ):
        validator.validate([], invalid_schema)


def test_boolean_is_not_accepted_as_integer(
    validator,
    customer_schema
):
    records = [
        {
            "customer_id": True,
            "customer_name": "Rajesh",
            "email": "rajesh@example.com",
            "age": 21
        }
    ]

    result = validator.validate(records, customer_schema)

    assert result["rejected_count"] == 1
