
import { useEffect, useState } from "react";
import { getPipelineHistory } from "../services/api";
import {
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Database,
  AlertCircle,
} from "lucide-react";

function PipelineRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError("");

      const result = await getPipelineHistory(50);
      setRuns(result.runs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const formatDate = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleString();
  };

  const formatDuration = (duration) => {
    if (duration == null) return "—";
    return `${Number(duration).toFixed(2)} ms`;
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Pipeline Runs</h1>
          <p>Monitor and review pipeline executions.</p>
        </div>

        <button
          className="primary-action"
          onClick={fetchHistory}
          disabled={loading}
        >
          <RefreshCw size={16} />
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <Database size={22} />
          <p>Total Runs</p>
          <h2>{runs.length}</h2>
        </div>

        <div className="stat-card">
          <CheckCircle2 size={22} />
          <p>Successful Runs</p>
          <h2>
            {runs.filter((run) => run.status === "success").length}
          </h2>
        </div>

        <div className="stat-card">
          <XCircle size={22} />
          <p>Failed Runs</p>
          <h2>
            {runs.filter((run) => run.status === "failed").length}
          </h2>
        </div>
      </div>

      {error && (
        <div className="validation-message error-message">
          <AlertCircle size={18} />
          <p>{error}</p>
        </div>
      )}

      <div className="config-section">
        <h3>Execution History</h3>

        {loading ? (
          <p>Loading pipeline history...</p>
        ) : runs.length === 0 ? (
          <p>No pipeline executions found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Pipeline</th>
                  <th>Source</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Records Loaded</th>
                  <th>Duration</th>
                  <th>Started At</th>
                </tr>
              </thead>

              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td>
                      <strong>{run.pipeline_name}</strong>
                      <br />
                      <small>{run.run_id}</small>
                    </td>

                    <td>{run.source || "—"}</td>
                    <td>{run.target || "—"}</td>

                    <td>
                      <span
                        className={`status-badge ${run.status}`}
                      >
                        {run.status}
                      </span>
                    </td>

                    <td>
                      {run.metrics?.loaded_count ?? 0}
                    </td>

                    <td>
                      <Clock size={14} />
                      {" "}
                      {formatDuration(run.duration_ms)}
                    </td>

                    <td>{formatDate(run.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default PipelineRuns;
