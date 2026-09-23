export type Status =
  | "RECEIVED"
  | "PROCESSED"
  | "ROUTED"
  | "ACKNOWLEDGED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "AWAITING_CONFIRMATION"
  | "CONFIRMED"
  | "CLOSED";

export type Feedback = {
  id: number;
  reporter_id: number;
  channel: string;
  content: string;
  context: string | null;
  submitted_at: string;
  status: string;
};
export type Issue = {
  id: number;
  feedback_id: number;
  reference: string;
  title: string;
  summary: string;
  category: string;
  issue_type: string;
  priority: string;
  department: string;
  handler_id: number | null;
  status: string;
  resolution: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};
export type Event = {
  id: number;
  issue_id: number;
  event_type: string;
  actor: string | null;
  description: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
};
export type Notification = {
  id: number;
  issue_id: number;
  reporter_id: number;
  channel: string;
  event_type: string;
  message: string;
  status: string;
  created_at: string;
};
export type QAIssueSummary = {
  id: number;
  reference: string;
  status: string;
  priority: string;
  department: string;
  handler_id: number | null;
  next_action: string;
};
export type Dashboard = {
  total_issues: number;
  by_status: Record<string, number>;
  issues: QAIssueSummary[];
};
export type IssueDetail = {
  issue: QAIssueSummary;
  events: Event[];
  notification_count: number;
};
