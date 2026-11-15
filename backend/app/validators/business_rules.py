
import re
from typing import Any


class BusinessRuleError(Exception):
    """Raised when business-rule configuration is invalid."""


class BusinessRuleValidator:
    """
    Reusable business-rule validation engine.

    Supported rules:
    - email
    - range
    - positive
    - allowed_values
    - reference

    Rules are supplied as metadata, not hardcoded per dataset.
    """

    SUPPORTED_RULES = {
        "email",
        "range",
        "positive",
        "allowed_values",
        "reference"
    }

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
    )

    def validate(
        self,
        records: list[dict[str, Any]],
        rules: list[dict[str, Any]],
        reference_data: dict[str, list[dict[str, Any]]] | None = None
    ) -> dict[str, Any]:

        if not isinstance(records, list):
            raise BusinessRuleError("Records must be a list")

        if not isinstance(rules, list):
            raise BusinessRuleError("Rules must be a list")

        reference_data = reference_data or {}

        self._validate_configuration(rules, reference_data)

        valid_records = []
        rejected_records = []

        for row_number, record in enumerate(records, start=1):

            if not isinstance(record, dict):
                rejected_records.append({
                    "source_row": row_number,
                    "source_record": record,
                    "issues": ["Record must be an object"]
                })
                continue

            issues = []

            for rule in rules:
                field = rule["field"]
                value = record.get(field)

                is_null = value is None or (
                    isinstance(value, str) and not value.strip()
                )

                if is_null:
                    if not rule.get("nullable", False):
                        issues.append(f"{field} is required")
                    continue

                rule_type = rule["type"]

                if rule_type == "email":
                    if not isinstance(value, str) or not self.EMAIL_PATTERN.fullmatch(value.strip()):
                        issues.append(f"{field} has an invalid email format")

                elif rule_type == "range":
                    number = self._to_number(value)

                    if number is None:
                        issues.append(f"{field} must be numeric")
                    else:
                        minimum = rule.get("min")
                        maximum = rule.get("max")

                        if minimum is not None and number < minimum:
                            issues.append(
                                f"{field} must be at least {minimum}"
                            )

                        if maximum is not None and number > maximum:
                            issues.append(
                                f"{field} must be at most {maximum}"
                            )

                elif rule_type == "positive":
                    number = self._to_number(value)

                    if number is None or number <= 0:
                        issues.append(
                            f"{field} must be greater than zero"
                        )

                elif rule_type == "allowed_values":
                    allowed = rule["values"]

                    if value not in allowed:
                        issues.append(
                            f"{field} must be one of {allowed}"
                        )

                elif rule_type == "reference":
                    dataset = rule["dataset"]
                    reference_field = rule["reference_field"]

                    reference_values = {
                        self._normalize(item.get(reference_field))
                        for item in reference_data[dataset]
                    }

                    if self._normalize(value) not in reference_values:
                        issues.append(
                            f"{field} references an unknown "
                            f"{dataset} record"
                        )

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

    def _validate_configuration(self, rules, reference_data):

        for rule in rules:
            if not isinstance(rule, dict):
                raise BusinessRuleError(
                    "Each business rule must be an object"
                )

            rule_type = rule.get("type")
            field = rule.get("field")

            if rule_type not in self.SUPPORTED_RULES:
                raise BusinessRuleError(
                    f"Unsupported business rule: {rule_type}"
                )

            if not isinstance(field, str) or not field.strip():
                raise BusinessRuleError(
                    "Every business rule must specify a field"
                )

            if rule_type == "range":
                minimum = rule.get("min")
                maximum = rule.get("max")

                if minimum is None and maximum is None:
                    raise BusinessRuleError(
                        "Range rule requires min or max"
                    )

                for bound in (minimum, maximum):
                    if bound is not None and (
                        isinstance(bound, bool)
                        or not isinstance(bound, (int, float))
                    ):
                        raise BusinessRuleError(
                            "Range boundaries must be numeric"
                        )

                if (
                    minimum is not None
                    and maximum is not None
                    and minimum > maximum
                ):
                    raise BusinessRuleError(
                        "Range minimum cannot exceed maximum"
                    )

            if rule_type == "allowed_values":
                if (
                    not isinstance(rule.get("values"), list)
                    or not rule["values"]
                ):
                    raise BusinessRuleError(
                        "Allowed-values rule requires a non-empty values list"
                    )

            if rule_type == "reference":
                dataset = rule.get("dataset")
                reference_field = rule.get("reference_field")

                if not dataset or not reference_field:
                    raise BusinessRuleError(
                        "Reference rule requires dataset and reference_field"
                    )

                if dataset not in reference_data:
                    raise BusinessRuleError(
                        f"Reference dataset not provided: {dataset}"
                    )

                if not isinstance(reference_data[dataset], list):
                    raise BusinessRuleError(
                        f"Reference data for {dataset} must be a list"
                    )

                if any(
                    not isinstance(item, dict)
                    or reference_field not in item
                    or item[reference_field] is None
                    for item in reference_data[dataset]
                ):
                    raise BusinessRuleError(
                        f"Invalid reference records in {dataset}"
                    )

    @staticmethod
    def _to_number(value):

        if isinstance(value, bool):
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize(value):

        if isinstance(value, str):
            return value.strip()

        return value
