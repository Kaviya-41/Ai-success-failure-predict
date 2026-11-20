"use client";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("token") ||
        localStorage.getItem("access_token")
      : null;

  const headers = new Headers(options.headers);
  const selectedWorkspaceId =
    typeof window !== "undefined"
      ? localStorage.getItem("selected_workspace_id")
      : null;

  headers.set("Content-Type", "application/json");
  if (selectedWorkspaceId) {
    headers.set("X-Workspace-ID", selectedWorkspaceId);
  }

  // Only attach a token header when it's a non-empty, valid string
  if (token && token !== "undefined" && token !== "null") {
    headers.set("Authorization", `Bearer ${token}`);
  } else {
    // Clean up any invalid token values left in localStorage
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `Request failed: ${response.status}`;

    try {
      const errorData = await response.json();

      if (typeof errorData?.detail === "string") {
        errorMessage = errorData.detail;
      } else if (typeof errorData?.message === "string") {
        errorMessage = errorData.message;
      }
    } catch {
      // Ignore invalid JSON response
    }

    // Only an authentication failure invalidates the session. A workspace or
    // role authorization failure must not log the user out.
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }

      throw new Error("Not authenticated. Please sign in again.");
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

// Convenience helper for running a prediction
export async function runPrediction(payload: Record<string, any>) {
  return apiFetch("/predictions/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}