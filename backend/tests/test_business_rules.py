
import pytest

from app.validators.business_rules import (
    BusinessRuleValidator,
    BusinessRuleError
)


@pytest.fixture
def validator():
    return BusinessRuleValidator()


@pytest.fixture
def customer_rules():
    return [
        {
            "type": "email",
            "field": "email",
            "nullable": False
        },
        {
            "type": "range",
            "field": "age",
            "min": 0,
            "max": 120
        }
    ]


def test_valid_customer(validator, customer_rules):
    records = [
        {
            "customer_id": 101,
            "email": "rajesh@example.com",
            "age": 21
        }
    ]

    result = validator.validate(records, customer_rules)

    assert result["valid_count"] == 1
    assert result["rejected_count"] == 0


def test_invalid_email(validator, customer_rules):
    records = [
        {
            "customer_id": 101,
            "email": "invalid-email",
            "age": 21
        }
    ]

    result = validator.validate(records, customer_rules)

    assert result["rejected_count"] == 1
    assert any(
        "invalid email format" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


@pytest.mark.parametrize("age", [0, 120])
def test_age_boundary_values(validator, customer_rules, age):
    records = [
        {
            "customer_id": 101,
            "email": "rajesh@example.com",
            "age": age
        }
    ]

    result = validator.validate(records, customer_rules)

    assert result["valid_count"] == 1


def test_negative_age(validator, customer_rules):
    records = [
        {
            "customer_id": 101,
            "email": "rajesh@example.com",
            "age": -5
        }
    ]

    result = validator.validate(records, customer_rules)

    assert result["rejected_count"] == 1
    assert any(
        "at least 0" in issue
        for issue in result["rejected_records"][0]["issues"]
    )


def test_positive_order_amount(validator):
    rules = [
        {
            "type": "positive",
            "field": "amount"
        }
    ]

    records = [{"amount": 250.50}]

    result = validator.validate(records, rules)

    assert result["valid_count"] == 1


def test_invalid_order_amount(validator):
    rules = [
        {
            "type": "positive",
            "field": "amount"
        }
    ]

    records = [{"amount": -100}]

    result = validator.validate(records, rules)

    assert result["rejected_count"] == 1


def test_invalid_order_status(validator):
    rules = [
        {
            "type": "allowed_values",
            "field": "status",
            "values": ["pending", "completed", "cancelled"]
        }
    ]

    records = [{"status": "unknown"}]

    result = validator.validate(records, rules)

    assert result["rejected_count"] == 1


def test_valid_customer_reference(validator):
    rules = [
        {
            "type": "reference",
            "field": "customer_id",
            "dataset": "customers",
            "reference_field": "customer_id"
        }
    ]

    records = [{"customer_id": 101}]

    reference_data = {
        "customers": [
            {"customer_id": 101},
            {"customer_id": 102}
        ]
    }

    result = validator.validate(
        records,
        rules,
        reference_data
    )

    assert result["valid_count"] == 1


def test_invalid_customer_reference(validator):
    rules = [
        {
            "type": "reference",
            "field": "customer_id",
            "dataset": "customers",
            "reference_field": "customer_id"
        }
    ]

    records = [{"customer_id": 999}]

    reference_data = {
        "customers": [
            {"customer_id": 101}
        ]
    }

    result = validator.validate(
        records,
        rules,
        reference_data
    )

    assert result["rejected_count"] == 1


def test_empty_input(validator, customer_rules):
    result = validator.validate([], customer_rules)

    assert result["total_records"] == 0
    assert result["valid_count"] == 0
    assert result["rejected_count"] == 0


def test_invalid_rule_configuration(validator):
    rules = [
        {
            "type": "unknown_rule",
            "field": "age"
        }
    ]

    with pytest.raises(
        BusinessRuleError,
        match="Unsupported business rule"
    ):
        validator.validate([], rules)


def test_missing_required_field(validator):
    rules = [
        {
            "type": "email",
            "field": "email",
            "nullable": False
        }
    ]

    records = [{"customer_id": 101}]

    result = validator.validate(records, rules)

    assert result["rejected_count"] == 1
    assert "email is required" in result["rejected_records"][0]["issues"]
