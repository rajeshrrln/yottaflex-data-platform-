
import { useState } from "react";
import { runPipeline } from "../services/api";

import {
  Database,
  FileJson,
  Settings2,
  KeyRound,
  Save,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

const initialConfig = {
  pipeline_name: "",
  dataset_name: "customers",
  source_path: "data/customers.csv",
  source_format: "csv",
  target_table: "customers",
  load_mode: "upsert",
  primary_keys: "customer_id",

  columns: [
    { name: "customer_id", type: "integer", nullable: false },
    { name: "name", type: "string", nullable: false },
    { name: "email", type: "string", nullable: false },
    { name: "age", type: "integer", nullable: true },
  ],
};

export default function PipelineConfiguration() {
  const [config, setConfig] = useState(initialConfig);
  const [errors, setErrors] = useState([]);
  const [generated, setGenerated] = useState(false);
  const [running, setRunning] = useState(false);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [pipelineError, setPipelineError] = useState("");

  // Update configuration fields
  const updateField = (field, value) => {
    setConfig((previous) => ({
      ...previous,
      [field]: value,
    }));

    setGenerated(false);
    setPipelineResult(null);
    setPipelineError("");
  };

  // Convert primary keys into an array
  const getPrimaryKeys = () =>
    config.primary_keys
      .split(",")
      .map((key) => key.trim())
      .filter(Boolean);

  // Generate backend configuration
  const buildBackendConfig = () => ({
    pipeline_name: config.pipeline_name.trim(),
    dataset_name: config.dataset_name.trim(),

    source: {
      path: config.source_path.trim(),
      format: config.source_format,
    },

    schema: {
      columns: config.columns,
      primary_keys: getPrimaryKeys(),
    },

    business_rules: [
      {
        field: "email",
        type: "email",
        nullable: false,
      },
      {
        field: "age",
        type: "range",
        min: 18,
        max: 100,
        nullable: true,
      },
    ],

    transformation: {
      strip_whitespace: true,
    },

    target: {
      db_path: "data/yottaflex.db",
      table_name: config.target_table.trim(),
      load_mode: config.load_mode,
      primary_keys: getPrimaryKeys(),
    },
  });

  // Validate configuration
  const validateConfig = () => {
    const validationErrors = [];

    if (!config.pipeline_name.trim()) {
      validationErrors.push("Pipeline name is required.");
    }

    if (!config.dataset_name.trim()) {
      validationErrors.push("Dataset name is required.");
    }

    if (
      !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(
        config.dataset_name.trim()
      )
    ) {
      validationErrors.push(
        "Dataset name must be a valid identifier."
      );
    }

    if (!config.source_path.trim()) {
      validationErrors.push("Source path is required.");
    }

    if (!config.target_table.trim()) {
      validationErrors.push("Target table is required.");
    }

    if (
      !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(
        config.target_table.trim()
      )
    ) {
      validationErrors.push(
        "Target table must use a valid SQL identifier."
      );
    }

    if (!["csv", "json"].includes(config.source_format)) {
      validationErrors.push("Select a valid source format.");
    }

    if (
      !["append", "replace", "upsert"].includes(
        config.load_mode
      )
    ) {
      validationErrors.push("Select a valid load mode.");
    }

    const primaryKeys = getPrimaryKeys();

    if (
      config.load_mode === "upsert" &&
      primaryKeys.length === 0
    ) {
      validationErrors.push(
        "Primary key is required for upsert mode."
      );
    }

    if (
      primaryKeys.some(
        (key) => !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(key)
      )
    ) {
      validationErrors.push(
        "Primary key must be a valid column identifier."
      );
    }

    setErrors(validationErrors);
    setGenerated(validationErrors.length === 0);

    return validationErrors.length === 0;
  };

  // Validate configuration button
  const generateConfig = () => {
    validateConfig();
  };

  // Execute pipeline
  const handleRunPipeline = async () => {
    if (!validateConfig()) return;

    setRunning(true);
    setPipelineResult(null);
    setPipelineError("");

    try {
      const result = await runPipeline(
        buildBackendConfig()
      );

      setPipelineResult(result);
    } catch (error) {
      setPipelineError(
        error.message || "Pipeline execution failed."
      );
    } finally {
      setRunning(false);
    }
  };

  // Reset configuration
  const resetConfig = () => {
    setConfig(initialConfig);
    setErrors([]);
    setGenerated(false);
    setPipelineResult(null);
    setPipelineError("");
  };

  return (
    <div className="pipeline-page">

      {/* Page Heading */}

      <div className="pipeline-page-heading">
        <div>
          <p className="eyebrow">
            DATA ENGINEERING / CONFIGURATION
          </p>

          <h1>Pipeline Configuration</h1>

          <p>
            Define source metadata, schema and target loading strategy.
          </p>
        </div>

        <span className="environment-badge">
          CONFIGURATION MODE
        </span>
      </div>

      <div className="configuration-layout">

        <section className="configuration-form">

          {/* General Information */}

          <div className="config-section">

            <div className="config-section-title">
              <div className="config-icon blue">
                <Settings2 size={19} />
              </div>

              <div>
                <h3>General Information</h3>
                <p>Identify your pipeline and dataset.</p>
              </div>
            </div>

            <div className="form-grid">

              <div className="form-group">
                <label>Pipeline Name *</label>

                <input
                  value={config.pipeline_name}
                  onChange={(e) =>
                    updateField(
                      "pipeline_name",
                      e.target.value
                    )
                  }
                  placeholder="customer_ingestion"
                />
              </div>

              <div className="form-group">
                <label>Dataset Name *</label>

                <input
                  value={config.dataset_name}
                  onChange={(e) =>
                    updateField(
                      "dataset_name",
                      e.target.value
                    )
                  }
                  placeholder="json_customers"
                />

                <span className="field-hint">
                  Enter a custom dataset name.
                </span>
              </div>

            </div>
          </div>

          {/* Source Configuration */}

          <div className="config-section">

            <div className="config-section-title">
              <div className="config-icon purple">
                <FileJson size={19} />
              </div>

              <div>
                <h3>Source Configuration</h3>
                <p>Specify where the data comes from.</p>
              </div>
            </div>

            <div className="form-grid">

              <div className="form-group full-width">
                <label>Source File Path *</label>

                <input
                  value={config.source_path}
                  onChange={(e) =>
                    updateField(
                      "source_path",
                      e.target.value
                    )
                  }
                  placeholder="data/json_customers.json"
                />

                <span className="field-hint">
                  Relative path from the backend project root.
                </span>
              </div>

              <div className="form-group">
                <label>Source Format</label>

                <select
                  value={config.source_format}
                  onChange={(e) =>
                    updateField(
                      "source_format",
                      e.target.value
                    )
                  }
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

            </div>
          </div>

          {/* Target Configuration */}

          <div className="config-section">

            <div className="config-section-title">
              <div className="config-icon orange">
                <Database size={19} />
              </div>

              <div>
                <h3>Target Configuration</h3>
                <p>Define how data is published.</p>
              </div>
            </div>

            <div className="form-grid">

              <div className="form-group">
                <label>Target Table *</label>

                <input
                  value={config.target_table}
                  onChange={(e) =>
                    updateField(
                      "target_table",
                      e.target.value
                    )
                  }
                  placeholder="json_customers"
                />
              </div>

              <div className="form-group">
                <label>Load Mode *</label>

                <select
                  value={config.load_mode}
                  onChange={(e) =>
                    updateField(
                      "load_mode",
                      e.target.value
                    )
                  }
                >
                  <option value="append">Append</option>
                  <option value="replace">Replace</option>
                  <option value="upsert">Upsert</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label>
                  <KeyRound size={14} />
                  Primary Key
                </label>

                <input
                  value={config.primary_keys}
                  onChange={(e) =>
                    updateField(
                      "primary_keys",
                      e.target.value
                    )
                  }
                  placeholder="customer_id"
                />

                <span className="field-hint">
                  Editable in all loading modes. Required for upsert.
                </span>
              </div>

            </div>
          </div>

          {/* Configuration Actions */}

          <div className="config-actions">

            <button
              className="secondary-action"
              onClick={resetConfig}
              type="button"
            >
              <RotateCcw size={16} />
              Reset
            </button>

            <button
              className="primary-action"
              onClick={generateConfig}
              type="button"
              disabled={running}
            >
              <Save size={16} />
              Validate Configuration
            </button>

            <button
              className="primary-action"
              onClick={handleRunPipeline}
              type="button"
              disabled={running}
            >
              {running
                ? "Running Pipeline..."
                : "Run Pipeline"}
            </button>

          </div>

          {/* Validation Errors */}

          {errors.length > 0 && (
            <div className="validation-message error-message">
              <AlertCircle size={18} />

              <div>
                <strong>
                  Configuration validation failed
                </strong>

                {errors.map((error) => (
                  <p key={error}>{error}</p>
                ))}
              </div>
            </div>
          )}

          {/* Validation Success */}

          {generated && (
            <div className="validation-message success-message">
              <CheckCircle2 size={18} />

              <div>
                <strong>Configuration is valid.</strong>
                <p>
                  Review the generated metadata on the right.
                </p>
              </div>
            </div>
          )}

          {/* Pipeline Error */}

          {pipelineError && (
            <div className="validation-message error-message">
              <AlertCircle size={18} />

              <div>
                <strong>Pipeline execution failed</strong>
                <p>{pipelineError}</p>
              </div>
            </div>
          )}

          {/* Pipeline Execution Results */}

          {pipelineResult && (
            <div className="config-section">
              <h3>Pipeline Execution Results</h3>

              <p>
                Status:{" "}
                <strong>{pipelineResult.status}</strong>
              </p>

              <div className="form-grid">
                {Object.entries(
                  pipelineResult.metrics || {}
                ).map(([key, value]) => (
                  <div className="form-group" key={key}>
                    <label>
                      {key.replaceAll("_", " ")}
                    </label>

                    <strong>{value}</strong>
                  </div>
                ))}
              </div>

              <p>
                Target table:{" "}
                <strong>{pipelineResult.target}</strong>
              </p>

              <p>
                Rejected records:{" "}
                {(pipelineResult.rejected_records || []).length}
              </p>
            </div>
          )}

        </section>

        {/* Configuration Preview */}

        <aside className="config-preview">

          <div className="preview-heading">
            <div>
              <h3>Configuration Preview</h3>
              <p>Generated pipeline metadata</p>
            </div>

            <FileJson size={21} />
          </div>

          <div className="preview-status">
            <span
              className={`preview-dot ${
                generated ? "valid" : ""
              }`}
            />

            {generated ? "Validated" : "Not validated"}
          </div>

          <pre className="json-preview">
            <code>
              {JSON.stringify(
                buildBackendConfig(),
                null,
                2
              )}
            </code>
          </pre>

          <p className="preview-note">
            Pipeline metadata is ready for backend execution.
          </p>

        </aside>

      </div>
    </div>
  );
}
