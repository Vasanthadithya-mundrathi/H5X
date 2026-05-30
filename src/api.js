const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function uploadTelemetry(files) {
  const body = new FormData();
  appendFiles(body, "gateway_logs", files.gatewayLogs);
  appendFiles(body, "traces", files.traces);
  appendFiles(body, "pod_metrics", files.podMetrics);
  appendFiles(body, "application_logs", files.applicationLogs);

  const response = await fetch(`${API_BASE_URL}/api/datasets/upload`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    throw await readError(response, "Upload failed");
  }

  return response.json();
}

function appendFiles(body, fieldName, files) {
  const list = Array.isArray(files) ? files : files ? [files] : [];
  for (const file of list) {
    body.append(fieldName, file);
  }
}

export async function generateScenario(datasetName, testMode, targetUrl, duration, rateLimit) {
  const response = await fetch(`${API_BASE_URL}/api/scenarios/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      datasetName,
      testMode,
      targetUrl,
      duration,
      rateLimit: normalizeRateLimit(rateLimit),
    }),
  });

  if (!response.ok) {
    throw await readError(response, "Scenario generation failed");
  }

  return response.json();
}

export async function startRun(datasetName, testMode, targetUrl, duration, rateLimit) {
  const response = await fetch(`${API_BASE_URL}/api/runs/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      datasetName,
      testMode,
      targetUrl,
      duration,
      rateLimit: normalizeRateLimit(rateLimit),
    }),
  });

  if (!response.ok) {
    throw await readError(response, "Starting test run failed");
  }

  return response.json();
}

function normalizeRateLimit(rateLimit) {
  const parsed = Number.parseInt(rateLimit, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 24;
}

export async function getRunStatus(runId) {
  const response = await fetch(`${API_BASE_URL}/api/runs/${runId}/status`);
  if (!response.ok) {
    throw await readError(response, "Fetching run status failed");
  }
  return response.json();
}

export async function getRunResults(runId) {
  const response = await fetch(`${API_BASE_URL}/api/runs/${runId}/results`);
  if (!response.ok) {
    throw await readError(response, "Fetching run results failed");
  }
  return response.json();
}

async function readError(response, fallback) {
  const error = new Error(`${fallback}: ${response.status}`);
  try {
    const body = await response.json();
    const detail = body.detail;
    if (typeof detail === "string") {
      error.message = detail;
    } else if (detail?.message) {
      error.message = detail.message;
      error.dataQuality = detail.dataQuality;
    }
  } catch {
    // Keep the status-based message if the server did not return JSON.
  }
  return error;
}
