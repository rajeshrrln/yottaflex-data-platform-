
import { useEffect, useState } from "react";

import {
  Workflow,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
} from "lucide-react";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import MetricCard from "../components/MetricCard";

import {
  getPipelineHistory,
  checkBackendHealth,
} from "../services/api";

export default function Dashboard() {
  const [runs, setRuns] = useState([]);
  const [backendStatus, setBackendStatus] = useState("Checking");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const [historyResult] = await Promise.all([
        getPipelineHistory(200),
        checkBackendHealth(),
      ]);

      setRuns(historyResult.runs || []);
      setBackendStatus("Connected");
    } catch (err) {
      setBackendStatus("Disconnected");
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const successfulRuns = runs.filter(
    (run) => run.status === "success"
  );

  const failedRuns = runs.filter(
    (run) => run.status === "failed"
  );

  const totalPipelines = new Set(
    runs
      .map((run) => run.pipeline_name)
      .filter((name) => name && name !== "Untitled Pipeline")
  ).size;

  const rejectedRecords = runs.reduce(
    (total, run) =>
      total + Number(run.metrics?.rejected_count || 0),
    0
  );

  const averageDuration = runs.length
    ? runs.reduce(
        (total, run) => total + Number(run.duration_ms || 0),
        0
      ) / runs.length
    : 0;

  // Build chart data from actual execution dates.
  const chartData = [];

  for (let i = 6; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    const dayRuns = runs.filter((run) => {
      if (!run.started_at) return false;

      const runDate = new Date(run.started_at);

      return (
        runDate.getFullYear() === date.getFullYear() &&
        runDate.getMonth() === date.getMonth() &&
        runDate.getDate() === date.getDate()
      );
    });

    chartData.push({
      day: date.toLocaleDateString("en-IN", {
        weekday: "short",
      }),
      runs: dayRuns.length,
    });
  }

  const formatDate = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleString();
  };

  const formatDuration = (duration) => {
    if (duration == null) return "—";
    return `${Number(duration).toFixed(2)} ms`;
  };

  return (
    <div className="dashboard">

      <div className="welcome-section">
        <div>
          <p className="eyebrow">DATA OPERATIONS</p>
          <h1>Pipeline Overview</h1>
          <p>
            Monitor ingestion, data quality and pipeline performance.
          </p>
        </div>

        <button
          className="primary-action"
          onClick={fetchDashboardData}
          disabled={loading}
        >
          <RefreshCw size={16} />
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="validation-message error-message">
          <AlertTriangle size={18} />
          <p>{error}</p>
        </div>
      )}

      <section className="metrics-grid">

        <MetricCard
          title="Total Pipelines"
          value={loading ? "..." : String(totalPipelines).padStart(2, "0")}
          description="Distinct named pipelines"
          icon={Workflow}
          color="blue"
        />

        <MetricCard
          title="Successful Runs"
          value={loading ? "..." : String(successfulRuns.length)}
          description="Completed successfully"
          icon={CheckCircle2}
          color="green"
        />

        <MetricCard
          title="Rejected Records"
          value={loading ? "..." : String(rejectedRecords)}
          description="Across recorded runs"
          icon={AlertTriangle}
          color="orange"
        />

        <MetricCard
          title="Avg. Processing"
          value={loading ? "..." : `${averageDuration.toFixed(2)} ms`}
          description="Average execution duration"
          icon={Clock}
          color="purple"
        />

      </section>

      <section className="content-grid">

        <article className="content-card chart-card">
          <div className="section-heading">
            <div>
              <h3>Pipeline Activity</h3>
              <p>Actual executions over the last 7 days</p>
            </div>

            <span className="chart-period">
              Last 7 days
            </span>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient
                    id="runGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#6689f5"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="#6689f5"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#edf0f5"
                />

                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                />

                <YAxis
                  allowDecimals={false}
                  axisLine={false}
                  tickLine={false}
                />

                <Tooltip />

                <Area
                  type="monotone"
                  dataKey="runs"
                  name="Pipeline Runs"
                  stroke="#6689f5"
                  fill="url(#runGradient)"
                  strokeWidth={2.5}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="content-card health-card">
          <h3>Platform Components</h3>
          <p>Application architecture</p>

          {[
            ["Frontend", "React", "Connected"],
            ["Backend", "FastAPI", backendStatus],
            [
              "Database",
              "SQLite",
              backendStatus === "Connected"
                ? "Accessible via backend"
                : "Unknown",
            ],
          ].map(([name, technology, status]) => (
            <div className="health-row" key={name}>
              <div>
                <strong>{name}</strong>
                <span>{technology}</span>
              </div>

              <span
                className={`health-status ${
                  status === "Connected" ||
                  status === "Accessible via backend"
                    ? "connected"
                    : "pending"
                }`}
              >
                {status}
              </span>
            </div>
          ))}
        </article>

      </section>

      <section className="content-card runs-card">

        <div className="section-heading">
          <div>
            <h3>Recent Pipeline Runs</h3>
            <p>Live execution records from the backend</p>
          </div>

          <button
            className="text-button"
            onClick={fetchDashboardData}
          >
            Refresh runs →
          </button>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Pipeline</th>
                <th>Source</th>
                <th>Records</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6">Loading execution records...</td>
                </tr>
              ) : runs.length === 0 ? (
                <tr>
                  <td colSpan="6">No pipeline executions found.</td>
                </tr>
              ) : (
                runs.slice(0, 5).map((run) => (
                  <tr key={run.run_id}>
                    <td className="run-id">
                      {run.run_id.slice(0, 8)}
                    </td>

                    <td>{run.pipeline_name}</td>

                    <td>{run.source || "—"}</td>

                    <td>
                      {run.metrics?.loaded_count ?? 0}
                    </td>

                    <td>
                      <span
                        className={`status-badge ${
                          run.status.toLowerCase()
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>

                    <td>{formatDate(run.started_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </section>

    </div>
  );
}
