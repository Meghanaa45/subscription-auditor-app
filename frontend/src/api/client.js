const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON, keep statusText
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/api/health`);
  return handleResponse(response);
}

export async function runSampleAudit() {
  const response = await fetch(`${API_BASE}/api/audit/sample`);
  return handleResponse(response);
}

export async function runAudit(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const response = await fetch(`${API_BASE}/api/audit`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

export async function askAuditor(auditId, question, history) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audit_id: auditId, question, history }),
  });
  return handleResponse(response);
}
