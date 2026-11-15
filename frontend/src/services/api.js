
const API_BASE_URL = "http://127.0.0.1:8000";

// Execute a pipeline
export async function runPipeline(config) {
  const response = await fetch(
    `${API_BASE_URL}/api/pipelines/run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ config }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || `Request failed: ${response.status}`
    );
  }

  return result;
}

// Check backend health
export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Backend health check failed");
  }

  return response.json();
}

// Fetch pipeline execution history
export async function getPipelineHistory(limit = 50) {
  const response = await fetch(
    `${API_BASE_URL}/api/pipelines/history?limit=${limit}`
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.detail || `Request failed: ${response.status}`
    );
  }

  return result;
}
// Fetch available database tables
export async function getDatasets() {
  const response = await fetch(`${API_BASE_URL}/api/datasets`);

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.detail || "Failed to fetch datasets");
  }

  return result;
}

// Fetch table schema and records
export async function getDatasetDetails(tableName, limit = 10) {
  const response = await fetch(
    `${API_BASE_URL}/api/datasets/${encodeURIComponent(tableName)}?limit=${limit}`
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.detail || "Failed to fetch dataset details");
  }

  return result;
}
export const getQuarantinedRecords = async (limit = 100, runId = null) => {
  const params = new URLSearchParams({ limit: String(limit) });

  if (runId) {
    params.append("run_id", runId);
  }

  const response = await fetch(
    `http://127.0.0.1:8000/api/quarantine/?${params}`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch quarantined records");
  }

  return response.json();
};


export const getQuarantineSummary = async () => {
  const response = await fetch(
    "http://127.0.0.1:8000/api/quarantine/summary"
  );

  if (!response.ok) {
    throw new Error("Failed to fetch quarantine summary");
  }

  return response.json();
};