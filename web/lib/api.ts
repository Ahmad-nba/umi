const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "The Watch Tower backend is unavailable. Start FastAPI and try again.",
    );
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : body?.detail?.error?.message;
    throw new Error(detail || "The request could not be completed.");
  }
  return body as T;
}

export const getFeedback = (id: number) =>
  api<import("@/types").Feedback>(`/feedback/${id}`);
export const createFeedback = (payload: object) =>
  api<import("@/types").Feedback>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
export const routeFeedback = (id: number) =>
  api<{ issue: import("@/types").Issue }>(`/feedback/${id}/route`, {
    method: "POST",
  });
export const getIssue = (id: number) =>
  api<import("@/types").Issue>(`/issues/${id}`);
export const listIssues = () => api<import("@/types").Issue[]>("/issues");
export const getIssueDetail = (id: number) =>
  api<import("@/types").IssueDetail>(`/qa/issues/${id}`);
export const getNotifications = (id: number) =>
  api<import("@/types").Notification[]>(`/issues/${id}/notifications`);
export const getDashboard = () =>
  api<import("@/types").Dashboard>("/qa/dashboard");
export const workflow = (id: number, action: string, body?: object) =>
  api<{ issue: import("@/types").Issue; message: string }>(
    `/issues/${id}/${action}`,
    { method: "POST", body: body ? JSON.stringify(body) : undefined },
  );
