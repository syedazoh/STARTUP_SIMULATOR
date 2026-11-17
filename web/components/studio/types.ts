export type Task = {
  id: string;
  agent: string;
  status: string;
  source?: string;
  plan_id?: string;
  objective?: string;
  action_type: string;
  payload: Record<string, unknown>;
  created_at?: string;
  ceo_authorized?: boolean;
  ceo_review?: Record<string, unknown> | null;
  result?: Record<string, unknown> | null;
  mode?: string;
  revision?: number;
  proposal_digest?: string;
  approval_expires_at?: string;
};
export type StudioEvent = {
  event_id: string;
  event_type: string;
  source?: string;
  timestamp?: string;
  sender?: string;
  receiver?: string;
  data?: Record<string, unknown>;
};
export type Snapshot = {
  tasks: Task[];
  statuses: Record<string, Record<string, unknown>>;
  events: StudioEvent[];
  errors: string[];
  updatedAt: string;
  tasksReady: boolean;
};
export type Transfer = {
  id: string;
  sender: string;
  receiver: string;
  label: string;
  title: string;
  status: string;
  source: string;
  taskId?: string;
};
