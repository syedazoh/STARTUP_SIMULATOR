/** Commands exposed by the Next workspace. Live publishing is deliberately absent. */
export const departments = [
  "ceo",
  "finance",
  "marketing",
  "hr",
  "operations",
] as const;
export type Department = (typeof departments)[number];
export type Operator = Exclude<Department, "ceo">;
export const labels: Record<Department, string> = {
  ceo: "CEO",
  finance: "Finance",
  marketing: "Marketing",
  hr: "HR",
  operations: "Operations",
};
export type Task = {
  id: string;
  business_id: string;
  agent: string;
  action_type: string;
  status: string;
  source: string;
  plan_id?: string | null;
  objective?: string | null;
  success_criteria?: string | null;
  payload: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  ceo_review?: Record<string, unknown> | null;
  approval_fingerprint?: string | null;
  ceo_authorized: boolean;
  owner_feedback?: string | null;
  revision_error?: string | null;
  previous_payload?: Record<string, unknown> | null;
  mode?: string | null;
  created_at: string;
  decided_at?: string | null;
  executed_at?: string | null;
};
export type Workforce = {total_headcount:number;positions:{department:string;role:string;count:number;employment_type:string}[]};
export type Business = {
  workforce?:Workforce|null;
  starting_headcount?:number;
  id: string;
  company_name: string;
  industry: string;
  starting_budget: number;
  enabled_agents: string[];
};
export type Plan = {
  plan_id: string;
  goal: string;
  strategy: string;
  status: string;
  created_at: string;
  assignments: {
    department: string;
    objective: string;
    action_type: string;
    payload: Record<string, unknown>;
    success_criteria: string;
  }[];
};
export type Report = {
  report_id: string;
  task_id: string;
  department: string;
  status: string;
  objective: string;
  result?: Record<string, unknown>;
  review_status: string;
  ceo_review?: Record<string, unknown>;
  created_at: string;
};
export type Finances = {
  available: number;
  revenue: number;
  expenses: number;
  monthly_payroll_commitment: number;
};
export type Panel<T> = { data: T; error?: string };
export type Workspace = {
  tasks: Panel<Task[]>;
  agents: Panel<Record<string, Record<string, unknown>>>;
  plans: Panel<Plan[]>;
  reports: Panel<Report[]>;
  finances: Panel<Finances | null>;
};
export const safeActions = new Set([
  "budget_request",
  "campaign_launch",
  "recruitment_request",
  "resource_request",
  "dataset_launch",
]);
export function decisionAllowed(task: Task) {
  return (
    safeActions.has(task.action_type) && task.status === "pending_approval"
  );
}
export function requireDecision(
  task: Task,
  businessId: string,
  decision: string,
) {
  if (task.business_id !== businessId)
    throw new Error("Task belongs to a different workspace.");
  if (!["approve", "reject"].includes(decision))
    throw new Error("Unknown decision.");
  if (!decisionAllowed(task))
    throw new Error(
      "This action is unavailable here. Refresh the task or use its dedicated workflow.",
    );
}
function text(form: FormData, key: string, max: number) {
  const value = form.get(key);
  if (typeof value !== "string" || !value.trim() || value.trim().length > max)
    throw new Error(
      `Enter a valid ${key.replaceAll("_", " ")} (up to ${max} characters).`,
    );
  return value.trim();
}
function number(
  form: FormData,
  key: string,
  min: number,
  max: number,
  integer = false,
) {
  const raw = form.get(key);
  if (typeof raw !== "string" || !raw.trim())
    throw new Error(`Enter ${key.replaceAll("_", " ")}.`);
  const value = Number(raw);
  if (
    !Number.isFinite(value) ||
    value < min ||
    value > max ||
    (integer && !Number.isSafeInteger(value))
  )
    throw new Error(`Enter a valid ${key.replaceAll("_", " ")}.`);
  return value;
}
export function businessPayload(form: FormData) {
  return {
    company_name: text(form, "company_name", 200),
    industry: text(form, "industry", 100),
    starting_budget: number(form, "starting_budget", 0, 1e9),
    starting_customer_base: number(
      form,
      "starting_customer_base",
      0,
      1e9,
      true,
    ),
    starting_headcount: number(form, "starting_headcount", 0, 1e6, true),
    starting_resources: number(form, "starting_resources", 0, 1e9, true),
    ...(form.has("workforce")?{workforce:workforcePayload(form)}:{}),
    enabled_agents: [...departments],
  };
}
export function departmentCommand(agent: string, form: FormData) {
  switch (agent) {
    case "finance":
      return {
        path: "finance/actions/budget-request",
        payload: {
          amount: number(form, "amount", 0.01, 1e9),
          department: text(form, "department", 100),
        },
      };
    case "marketing":
      return {
        path: "marketing/actions/campaign-launch",
        payload: {
          campaign_name: text(form, "campaign_name", 200),
          requested_budget: number(form, "requested_budget", 0.01, 1e9),
        },
      };
    case "hr":
      return {
        path: "hr/actions/recruitment-request",
        payload: {
          role: text(form, "role", 200),
          headcount: number(form, "headcount", 1, 1000, true),
          monthly_salary: number(form, "monthly_salary", 0, 1e9),
        },
      };
    case "operations":
      return {
        path: "operations/actions/resource-request",
        payload: {
          resource_type: text(form, "resource_type", 200),
          quantity: number(form, "quantity", 1, 1e9, true),
          unit_cost: number(form, "unit_cost", 0, 1e9),
        },
      };
    default:
      throw new Error("Unknown department action.");
  }
}
export function goalPayload(form: FormData) {
  const goal = text(form, "goal", 2000);
  if (goal.length < 5)
    throw new Error("Describe the goal in at least 5 characters.");
  return { goal };
}

// Motor can serialize UTC database dates without an offset. Do not interpret
// these server timestamps as the viewer's local timezone.
export function utcInstant(value: string) {
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value)
    ? value
    : `${value}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.valueOf()) ? null : date;
}

export function workforcePayload(form:FormData):Workforce {
 const raw=form.get('workforce');if(typeof raw!=='string'||raw.length>30000)throw new Error('Team data is missing or too large.');
 let data:Workforce;try{data=JSON.parse(raw)}catch{throw new Error('Invalid team data.');}
 if(!data||!Number.isInteger(data.total_headcount)||data.total_headcount<0||data.total_headcount>1e6||!Array.isArray(data.positions)||data.positions.length>50)throw new Error('Enter a valid headcount and up to 50 team groups.');
 const seen=new Set<string>();let total=0;
 const positions=data.positions.map(row=>{if(!row||typeof row.department!=='string'||typeof row.role!=='string'||!row.department.trim()||!row.role.trim()||row.department.trim().length>100||row.role.trim().length>100||!Number.isInteger(row.count)||row.count<1||row.count>1e6||!['unspecified','full_time','part_time','contract','intern'].includes(row.employment_type))throw new Error('Each team group needs a department, role, whole-number count and employment type.');const key=JSON.stringify([row.department.trim().toLowerCase(),row.role.trim().toLowerCase(),row.employment_type]);if(seen.has(key))throw new Error('Combine duplicate department, role and employment groups.');seen.add(key);total+=row.count;return {department:row.department.trim(),role:row.role.trim(),count:row.count,employment_type:row.employment_type}});
 if(total>data.total_headcount)throw new Error('Department counts exceed total headcount.');return {total_headcount:data.total_headcount,positions};
}
