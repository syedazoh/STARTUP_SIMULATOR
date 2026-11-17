import type { Task as WorkspaceTask } from "../../lib/workspace-contracts";

export type Task = WorkspaceTask & {
  updated_at?: string;
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
  decisions?: (StudioEvent & {_id?: string; id?: string})[];
  decisionsReady?: boolean;
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
