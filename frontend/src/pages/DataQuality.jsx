
import { useEffect, useMemo, useState } from "react";

import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Database,
  RefreshCw,
  Archive,
  FileWarning,
} from "lucide-react";

import {
  getPipelineHistory,
  getQuarantinedRecords,
  getQuarantineSummary,
} from "../services/api";

export default function DataQuality() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("All");
  const [quarantineRecords, setQuarantineRecords] = useState([]);
  const [quarantineSummary, setQuarantineSummary] = useState({
    total: 0,
    by_stage: {},
});

  // ------------------------------------------
  // Fetch real pipeline quality information
  // ------------------------------------------

  const fetchQualityData = async () => {
  try {
    setLoading(true);
    setError("");

    const [historyResult, recordsResult, summaryResult] =
      await Promise.all([
        getPipelineHistory(200),
        getQuarantinedRecords(100),
        getQuarantineSummary(),
      ]);

    setRuns(historyResult.runs || []);
    setQuarantineRecords(recordsResult.records || []);
    setQuarantineSummary(summaryResult || {
      total: 0,
      by_stage: {},
    });

  } catch (err) {
    setError(err.message || "Unable to load quality data.");
  } finally {
    setLoading(false);
  }
};
// Fetch quality data when the page loads
useEffect(() => {
  fetchQualityData();
}, []);
  // ------------------------------------------
  // Aggregate real execution metrics
  // ------------------------------------------

  const summary = useMemo(() => {
    return runs.reduce(
      (total, run) => {
        const metrics = run.metrics || {};

        total.processed += Number(metrics.extracted_count || 0);
        total.schemaValid += Number(metrics.schema_valid_count || 0);
        total.businessValid += Number(metrics.business_valid_count || 0);
        total.transformed += Number(metrics.transformed_count || 0);
        total.loaded += Number(metrics.loaded_count || 0);
        total.rejected += Number(metrics.rejected_count || 0);

        return total;
      },
      {
        processed: 0,
        schemaValid: 0,
        businessValid: 0,
        transformed: 0,
        loaded: 0,
        rejected: 0,
      }
    );
  }, [runs]);

  const successfulRuns = runs.filter(
    (run) => run.status === "success"
  );

  const failedRuns = runs.filter(
    (run) => run.status !== "success"
  );

  // ------------------------------------------
  // Filter execution records
  // ------------------------------------------

  const displayedRuns = runs.filter((run) => {
    if (filter === "Valid") {
      return (
        run.status === "success" &&
        Number(run.metrics?.rejected_count || 0) === 0
      );
    }

    if (filter === "Rejected") {
      return (
        Number(run.metrics?.rejected_count || 0) > 0 ||
        run.status !== "success"
      );
    }

    return true;
  });

  const formatDate = (date) => {
    if (!date) return "—";

    return new Date(date).toLocaleString();
  };

  const formatDuration = (duration) => {
    if (duration == null) return "—";

    return `${Number(duration).toFixed(2)} ms`;
  };

  // ==========================================
  // UI
  // ==========================================

  return (
    <div className="quality-page">

      {/* Page Heading */}

      <div className="quality-heading">
        <div>
          <p className="eyebrow">
            DATA ENGINEERING / QUALITY CONTROL
          </p>

          <h1>Data Quality</h1>

          <p>
            Monitor schema validation, business rules and
            rejected records from actual pipeline executions.
          </p>
        </div>

        <button
          className="primary-action"
          type="button"
          onClick={fetchQualityData}
          disabled={loading}
        >
          <RefreshCw size={16} />
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Dataset Information */}

      <section className="quality-dataset-banner">
        <div className="quality-dataset-icon">
          <Database size={22} />
        </div>

        <div className="quality-dataset-info">
          <strong>Pipeline Execution Quality</strong>

          <span>
            Aggregated from {runs.length} recorded pipeline executions.
          </span>
        </div>

        <span className="quality-valid-badge">
          LIVE DATA
        </span>
      </section>

      {/* Loading and Error */}

      {error && (
        <div className="dataset-message dataset-error">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {loading && (
        <section className="quality-empty-state">
          <RefreshCw size={28} />
          <h3>Loading quality metrics...</h3>
          <p>Retrieving execution history from the backend.</p>
        </section>
      )}

      {!loading && !error && (
        <>

          {/* Quality Metrics */}

          <section className="quality-metrics">

            <article className="quality-metric">
              <div className="quality-metric-icon blue">
                <Database size={19} />
              </div>

              <span>Records Processed</span>

              <h2>
                {summary.processed.toLocaleString()}
              </h2>
            </article>

            <article className="quality-metric">
              <div className="quality-metric-icon green">
                <CheckCircle2 size={19} />
              </div>

              <span>Business Valid</span>

              <h2>
                {summary.businessValid.toLocaleString()}
              </h2>
            </article>

            <article className="quality-metric">
              <div className="quality-metric-icon red">
                <XCircle size={19} />
              </div>

              <span>Rejected Records</span>

              <h2>
                {summary.rejected.toLocaleString()}
              </h2>
            </article>

            <article className="quality-metric">
              <div className="quality-metric-icon orange">
                <AlertTriangle size={19} />
              </div>

              <span>Failed Runs</span>

              <h2>{failedRuns.length}</h2>
            </article>

          </section>

          {/* Validation Rules */}

          <section className="quality-card">

            <div className="quality-section-heading">
              <div>
                <h3>Validation Pipeline Stages</h3>
                <p>
                  Actual record counts at each processing stage.
                </p>
              </div>

              <ShieldCheck size={22} />
            </div>

            <div className="quality-rules-grid">

              <div className="quality-rule">
                <CheckCircle2 size={18} />

                <div>
                  <strong>Schema Validation</strong>
                  <span>
                    {summary.schemaValid} records passed schema validation.
                  </span>
                </div>
              </div>

              <div className="quality-rule">
                <CheckCircle2 size={18} />

                <div>
                  <strong>Business Rule Validation</strong>
                  <span>
                    {summary.businessValid} records passed business rules.
                  </span>
                </div>
              </div>

              <div className="quality-rule">
                <CheckCircle2 size={18} />

                <div>
                  <strong>Transformation</strong>
                  <span>
                    {summary.transformed} records transformed.
                  </span>
                </div>
              </div>

              <div className="quality-rule">
                <CheckCircle2 size={18} />

                <div>
                  <strong>Database Loading</strong>
                  <span>
                    {summary.loaded} records loaded into the target.
                  </span>
                </div>
              </div>

            </div>

          </section>

          {/* Validation Results */}

          <section className="quality-card">

            <div className="quality-section-heading">
              <div>
                <h3>Execution Quality Results</h3>
                <p>
                  Inspect quality metrics for each pipeline run.
                </p>
              </div>

              <Archive size={21} />
            </div>

            <div className="quality-filters">
              {["All", "Valid", "Rejected"].map((item) => (
                <button
                  key={item}
                  type="button"
                  className={
                    filter === item
                      ? "quality-filter active"
                      : "quality-filter"
                  }
                  onClick={() => setFilter(item)}
                >
                  {item}

                  {item === "All" && ` (${runs.length})`}

                  {item === "Valid" &&
                    ` (${successfulRuns.filter(
                      (run) =>
                        Number(run.metrics?.rejected_count || 0) === 0
                    ).length})`}

                  {item === "Rejected" &&
                    ` (${runs.length - successfulRuns.filter(
                      (run) =>
                        Number(run.metrics?.rejected_count || 0) === 0
                    ).length})`}
                </button>
              ))}
            </div>

            <div className="quality-table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Pipeline</th>
                    <th>Status</th>
                    <th>Processed</th>
                    <th>Schema Valid</th>
                    <th>Business Valid</th>
                    <th>Loaded</th>
                    <th>Rejected</th>
                    <th>Duration</th>
                  </tr>
                </thead>

                <tbody>
                  {displayedRuns.map((run) => {
                    const metrics = run.metrics || {};

                    return (
                      <tr key={run.run_id}>
                        <td>
                          <strong>{run.pipeline_name || "Untitled"}</strong>
                          <br />
                          <small>{run.run_id}</small>
                        </td>

                        <td>
                          <span
                            className={
                              run.status === "success"
                                ? "quality-status valid"
                                : "quality-status rejected"
                            }
                          >
                            {run.status}
                          </span>
                        </td>

                        <td>{metrics.extracted_count ?? 0}</td>

                        <td>{metrics.schema_valid_count ?? 0}</td>

                        <td>{metrics.business_valid_count ?? 0}</td>

                        <td>{metrics.loaded_count ?? 0}</td>

                        <td>{metrics.rejected_count ?? 0}</td>

                        <td>
                          {formatDuration(run.duration_ms)}
                        </td>
                      </tr>
                    );
                  })}

                  {displayedRuns.length === 0 && (
                    <tr>
                      <td colSpan="8">
                        No matching execution records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

          </section>

          {/* Quarantine Information */}

          {/* Quarantine Information */}

<section className="quality-card quarantine-card">

  <div className="quality-section-heading">
    <div>
      <h3>Rejected Records and Quarantine</h3>
      <p>
        Individual rejected records retrieved from persistent SQLite storage.
      </p>
    </div>

    <Archive size={22} />
  </div>

  <div className="dataset-info-row">
    <span>Total quarantined records</span>
    <strong>{quarantineSummary.total}</strong>
  </div>

  <div className="quality-rules-grid">
    {Object.entries(quarantineSummary.by_stage || {}).map(
      ([stage, count]) => (
        <div className="quality-rule" key={stage}>
          <AlertTriangle size={18} />
          <div>
            <strong>{stage.replaceAll("_", " ")}</strong>
            <span>{count} rejected records</span>
          </div>
        </div>
      )
    )}
  </div>

  <div className="quality-section-heading">
    <div>
      <h3>Quarantined Record Details</h3>
      <p>Inspect individual records and their rejection reasons.</p>
    </div>
  </div>

  <div className="quality-table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Source Row</th>
          <th>Source</th>
          <th>Validation Stage</th>
          <th>Rejected Record</th>
          <th>Issues</th>
          <th>Created At</th>
        </tr>
      </thead>

      <tbody>
        {quarantineRecords.map((record) => (
          <tr key={record.quarantine_id}>
            <td>{record.source_row ?? "—"}</td>

            <td>
              <small>{record.source_path || "—"}</small>
            </td>

            <td>
              <span className="quality-status rejected">
                {record.stage}
              </span>
            </td>

            <td>
              <pre className="quarantine-json">
                {JSON.stringify(record.source_record || {}, null, 2)}
              </pre>
            </td>

            <td>
              <pre className="quarantine-json">
                {JSON.stringify(record.issues || [], null, 2)}
              </pre>
            </td>

            <td>{formatDate(record.created_at)}</td>
          </tr>
        ))}

        {quarantineRecords.length === 0 && (
          <tr>
            <td colSpan="6">
              No individual quarantined records found.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  </div>

  <p className="quality-disclaimer">
    Rejected records and validation issues are retrieved from the
    backend quarantine table.
  </p>

</section>
          {/* Execution Summary */}

          <section className="quality-card">

            <div className="quality-section-heading">
              <div>
                <h3>Execution Summary</h3>
                <p>Pipeline execution overview.</p>
              </div>

              <FileWarning size={21} />
            </div>

            <div className="dataset-info-row">
              <span>Total executions</span>
              <strong>{runs.length}</strong>
            </div>

            <div className="dataset-info-row">
              <span>Successful executions</span>
              <strong>{successfulRuns.length}</strong>
            </div>

            <div className="dataset-info-row">
              <span>Failed executions</span>
              <strong>{failedRuns.length}</strong>
            </div>

            <div className="dataset-info-row">
              <span>Records loaded</span>
              <strong>{summary.loaded}</strong>
            </div>

          </section>

        </>
      )}

    </div>
  );
}
