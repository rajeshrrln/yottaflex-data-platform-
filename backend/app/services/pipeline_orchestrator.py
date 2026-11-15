from app.services.quarantine import save_quarantined_records
from typing import Any
from app.services.quarantine import save_quarantined_records
from app.services.extraction import DataExtractor, ExtractionError
from app.validators.schema_validator import (
    SchemaValidator,
    SchemaValidationError,
)
from app.validators.business_rules import (
    BusinessRuleValidator,
    BusinessRuleError,
)
from app.services.transformation import (
    DataTransformer,
    TransformationError,
)
from app.services.loader import SQLiteDataLoader, LoadingError


class PipelineExecutionError(Exception):
    """Raised when a pipeline stage fails."""


class PipelineOrchestrator:
    """
    Coordinates extraction, validation, transformation and loading.

    Configuration is supplied as metadata so the same orchestrator
    can run different datasets.
    """

    def __init__(self):
        self.extractor = DataExtractor()
        self.schema_validator = SchemaValidator()
        self.business_validator = BusinessRuleValidator()
        self.transformer = DataTransformer()
        self.loader = SQLiteDataLoader()

    def run(
    self,
    config: dict[str, Any],
    run_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(config, dict):
            raise PipelineExecutionError("Pipeline config must be a dictionary")

        required_sections = [
            "source",
            "schema",
            "target",
        ]

        for section in required_sections:
            if not isinstance(config.get(section), dict):
                raise PipelineExecutionError(
                    f"Missing or invalid pipeline section: {section}"
                )

        source = config["source"]
        target = config["target"]

        if not source.get("path") or not source.get("format"):
            raise PipelineExecutionError(
                "Source requires path and format"
            )

        if not target.get("db_path") or not target.get("table_name"):
            raise PipelineExecutionError(
                "Target requires db_path and table_name"
            )

        stage = "extraction"

        try:
            # 1. Extract source records.
            records = self.extractor.extract(
                source["path"],
                source["format"],
            )

            extracted_count = len(records)

            # 2. Validate source schema.
            stage = "schema_validation"

            schema_result = self.schema_validator.validate(
                records,
                config["schema"],
            )

            schema_valid_records = schema_result["valid_records"]

            rejected_records = [
                {
                    "stage": "schema_validation",
                    **item,
                }
                for item in schema_result["rejected_records"]
            ]

            # 3. Apply business rules to schema-valid records.
            stage = "business_rule_validation"

            business_rules = config.get("business_rules", [])
            reference_data = config.get("reference_data", {})

            business_result = self.business_validator.validate(
                schema_valid_records,
                business_rules,
                reference_data,
            )

            business_valid_records = business_result["valid_records"]

            for item in business_result["rejected_records"]:
                source_record = item.get("source_record", {})
                original_row = (
                    source_record.get("_source_row", item["source_row"])
                    if isinstance(source_record, dict)
                    else item["source_row"]
                )

                rejected_records.append({
                    "stage": "business_rule_validation",
                    "source_row": original_row,
                    "source_record": source_record,
                    "issues": item["issues"],
                })

            # 4. Transform records that passed both validation stages.
            stage = "transformation"

            transformation_config = config.get("transformation", {})

            transformed_records = self.transformer.transform(
                business_valid_records,
                transformation_config,
            )

            # 5. Remove internal metadata before database loading.
            stage = "loading"

            target_records = [
                {
                    key: value
                    for key, value in record.items()
                    if key != "_source_row"
                }
                for record in transformed_records
            ]

            load_mode = target.get("load_mode", "append")
            primary_keys = target.get(
                "primary_keys",
                config["schema"].get("primary_keys", []),
            )

            if target_records:
                load_result = self.loader.load(
                    records=target_records,
                    db_path=target["db_path"],
                    table_name=target["table_name"],
                    mode=load_mode,
                    primary_keys=primary_keys,
                )
            else:
                load_result = {
                    "table": target["table_name"],
                    "mode": load_mode,
                    "input_count": 0,
                    "loaded_count": 0,
                }

            rejected_count = len(rejected_records)
            loaded_count = load_result["loaded_count"]
            # Save rejected records into SQLite quarantine table
            if run_id and rejected_records:
                save_quarantined_records(
                    run_id=run_id,
                    source_path=source["path"],
                    rejected_records=rejected_records,
                )

            return {
                "status": "success",
                "source": source["path"],
                "target": target["table_name"],
                "metrics": {
                    "extracted_count": extracted_count,
                    "schema_valid_count": schema_result["valid_count"],
                    "business_valid_count": business_result["valid_count"],
                    "transformed_count": len(transformed_records),
                    "loaded_count": loaded_count,
                    "rejected_count": rejected_count,
                },
                "load_result": load_result,
                "rejected_records": rejected_records,
            }

        except (
            ExtractionError,
            SchemaValidationError,
            BusinessRuleError,
            TransformationError,
            LoadingError,
        ) as exc:
            raise PipelineExecutionError(
                f"Pipeline failed during {stage}: {exc}"
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineExecutionError(
                f"Invalid configuration or data during {stage}: {exc}"
            ) from exc
