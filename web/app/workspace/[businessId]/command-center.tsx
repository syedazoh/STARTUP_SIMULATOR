"use client";
import Avatar from "../../../components/agent-avatar";
import Icon from "../../../components/studio/icon";
import OverviewCharts from "./overview-charts";
import "./command-center.css";
import { useEffect, useRef, useState } from "react";
import {
  activatePlan,
  decideTask,
  proposePlan,
  proposeWork,
  readWorkspace,
} from "./actions";
import {
  departments,
  labels,
  decisionAllowed,
  safeActions,
  utcInstant,
  type Business,
  type Department,
  type Operator,
  type Task,
  type Workspace,
} from "../../../lib/workspace-contracts";
const display = (v: string) => v.replaceAll("_", " ");
const timestamp = (value: string) => {
  const date = utcInstant(value);
  return date
    ? date.toLocaleString("en-GB", { timeZone: "UTC" }) + " UTC"
    : "Not recorded";
};
const numeric = (value: number) =>
  new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
function Evidence({ value }: { value: unknown }) {
  return <pre>{JSON.stringify(value, null, 2)}</pre>;
}
function DepartmentFields({ department }: { department: Operator }) {
  switch (department) {
    case "finance":
      return (
        <>
          <label>
            Requested amount
            <input
              name="amount"
              type="number"
              min="0.01"
              max="1000000000"
              step="0.01"
              defaultValue="250"
              required
            />
          </label>
          <label>
            Receiving department
            <input
              name="department"
              maxLength={100}
              defaultValue="Marketing"
              required
            />
          </label>
        </>
      );
    case "marketing":
      return (
        <>
          <label>
            Campaign name
            <input
              name="campaign_name"
              maxLength={200}
              defaultValue="Product launch"
              required
            />
          </label>
          <label>
            Requested budget
            <input
              name="requested_budget"
              type="number"
              min="0.01"
              max="1000000000"
              step="0.01"
              defaultValue="250"
              required
            />
          </label>
        </>
      );
    case "hr":
      return (
        <>
          <label>
            Role
            <input
              name="role"
              maxLength={200}
              defaultValue="Designer"
              required
            />
          </label>
          <label>
            Headcount
            <input
              name="headcount"
              type="number"
              min="1"
              max="1000"
              step="1"
              defaultValue="1"
              required
            />
          </label>
          <label>
            Monthly salary per person
            <input
              name="monthly_salary"
              type="number"
              min="0"
              max="1000000000"
              step="0.01"
              defaultValue="500"
              required
            />
          </label>
        </>
      );
    case "operations":
      return (
        <>
          <label>
            Resource type
            <input
              name="resource_type"
              maxLength={200}
              defaultValue="Launch supplies"
              required
            />
          </label>
          <label>
            Quantity
            <input
              name="quantity"
              type="number"
              min="1"
              max="1000000000"
              step="1"
              defaultValue="5"
              required
            />
          </label>
          <label>
            Unit cost
            <input
              name="unit_cost"
              type="number"
              min="0"
              max="1000000000"
              step="0.01"
              defaultValue="20"
              required
            />
          </label>
        </>
      );
  }
}
export default function CommandCenter({
  business,
  initial,
  initialDepartment,
  agentTools,
}: {
  business: Business;
  initial: Workspace;
  initialDepartment?: Department;
  agentTools?: React.ReactNode;
}) {
  const [data, setData] = useState(initial),
    [department, setDepartment] = useState<Department | "all">(initialDepartment || "all");
  const [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState("");
  const [live, setLive] = useState(false),
    [selected, setSelected] = useState<Task | null>(null),
    [feedback, setFeedback] = useState("");
  const [activation, setActivation] = useState<string | null>(null),
    [lastRead, setLastRead] = useState("");
  const inFlight = useRef(false);
  async function refresh() {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      setData(await readWorkspace(business.id));
      setLastRead(new Date().toISOString());
    } catch {
      setError("Could not refresh. Your last loaded records remain visible.");
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  useEffect(() => {
    if (!live) return;
    const timer = setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 15000);
    return () => clearInterval(timer);
    // Business pages are keyed by their route; timer never retries writes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [live, business.id]);
  async function run(
    action: () => Promise<
      { ok: true; data: unknown } | { ok: false; error: string }
    >,
    message: string,
  ) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await action();
      if (result.ok) {
        setNotice(message);
        setSelected(null);
        setActivation(null);
        setFeedback("");
      } else setError(result.error);
      setData(await readWorkspace(business.id));
      setLastRead(new Date().toISOString());
    } catch {
      setError(
        "The request could not finish. Refresh before retrying; the backend may still be processing it.",
      );
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  const tasks = initialDepartment ? data.tasks.data.filter(t=>t.agent===initialDepartment) : data.tasks.data;
  const visible = tasks.filter(
    (t) => department === "all" || t.agent === department,
  );
  const pending = tasks.filter((t) => decisionAllowed(t));
  const active = tasks.filter((t) =>
    ["approved", "executing", "ceo_reviewing", "pending_ceo_review"].includes(
      t.status,
    ),
  );
  return (
    <div className="command-layout">
      <aside className="command-sidebar">
        <a className="command-wordmark" href="/workspace">
          <Icon name="studio" />
          <span>
            Startup<strong>simulator</strong>
          </span>
        </a>
        <div className="command-business">
          <span>Business workspace</span>
          <strong>{business.company_name}</strong>
          <small>{business.industry}</small>
        </div>
        <nav aria-label="Command center navigation">
          <a href="#overview" aria-current={initialDepartment?undefined:"page"}>
            <Icon name="signal" />
            Overview
          </a>
          <a href="#departments">
            <Icon name="cube" />
            Departments
          </a>
          <a href={initialDepartment?`/workspace/${encodeURIComponent(business.id)}#ceo-plans`:"#ceo-plans"}>
            <Icon name="list" />
            Goals & plans
          </a>
          <a href="#tasks">
            <Icon name="check" />
            Tasks & approvals
          </a>
          <a href={`/workspace/${encodeURIComponent(business.id)}/boardroom`}>
            <Icon name="studio" />
            3D Boardroom
          </a>
          <a href={`/workspace/${encodeURIComponent(business.id)}/automation`}>
            <Icon name="clock" />
            Automation & knowledge
          </a>
          <a href={`/workspace/${encodeURIComponent(business.id)}/distributed`}>
            <Icon name="signal" />
            Seven-role analysis
          </a>
          <a href={`/workspace/${encodeURIComponent(business.id)}/demo`}>
            <Icon name="play" />
            Launch laboratory
          </a>
          <div className="command-agent-heading">Agent workspaces</div>{departments.map(role=><a key={role} aria-current={initialDepartment===role?'page':undefined} href={`/workspace/${encodeURIComponent(business.id)}/agents/${role}`}><Icon name="cube"/>{labels[role]}</a>)}
        </nav>
        <div className="command-sidebar-bottom">
          <a href="/getting-started">Product demo & guide</a>
          <a href="/workspace">All businesses</a>
          <p>
            Owner-led decisions.
            <br />
            Five connected departments.
          </p>
        </div>
      </aside>
      <div className="command-center" aria-busy={busy} id="overview">
        <section className="hero compact">
          <div className="command-breadcrumb">
            Workspace <span>/</span> Overview
          </div>
          <h1>{initialDepartment?`${labels[initialDepartment]} workspace`:business.company_name}</h1>
          <p>
            {initialDepartment?`${business.company_name} · Department tasks, proposals, settings and saved conversations.`:"Your business, in focus. Review the work, the resources and the next decision."}
          </p>
          <a
            className="command-boardroom-link"
            href={`/workspace/${encodeURIComponent(business.id)}/boardroom`}
          >
            Open 3D Boardroom <Icon name="chevron" />
          </a>
        </section>
        {initialDepartment&&<div className="agent-workspace-intro"><Avatar agent={initialDepartment} caption={`${labels[initialDepartment]} avatar`}/><div><h2>Your {labels[initialDepartment]} working space</h2><p>{initialDepartment==="ceo"?"Use the planning form below to review goals and assignments. CEO review is separate from your final owner approval.":"Use the proposal form below for simulated work. Review execution mode and reasoning policy before sending requests."} Open Automation & knowledge for jobs, deadlines and documents.</p><a href={`/workspace/${encodeURIComponent(business.id)}/automation`}>Open automation & knowledge</a></div></div>}
        <p className="demo-label">
          Simulation workspace · Department actions change simulated business
          state. Real email, hiring, purchasing and social publication are not
          performed by these forms.
        </p>
        <div className="workspace-toolbar">
          <button
            className="secondary"
            disabled={busy}
            onClick={() => void refresh()}
          >
            {busy ? "Working…" : "Refresh workspace"}
          </button>
          <label className="inline-label">
            <input
              type="checkbox"
              checked={live}
              onChange={(e) => setLive(e.target.checked)}
            />{" "}
            Refresh every 15 seconds
          </label>
          <small>
            {lastRead
              ? `Last refreshed ${timestamp(lastRead)}`
              : "Loaded from saved backend records"}
          </small>
        </div>
        <div aria-live="polite">
          {notice && <p className="notice">{notice}</p>}
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <section aria-label="Workspace overview" className="workspace-metrics">
          {[
            ["Awaiting owner", data.tasks.error ? null : pending.length],
            ["In review / execution", data.tasks.error ? null : active.length],
            [
              "Recorded executions",
              data.tasks.error
                ? null
                : tasks.filter((t) => t.status === "executed").length,
            ],
            [
              "Available simulated funds",
              data.finances.error || !data.finances.data
                ? null
                : numeric(data.finances.data.available),
            ],
          ].map(([label, value], index) => (
            <div className="metric" key={label}>
              <div className="command-metric-heading">
                <span>{label}</span>
                <Icon name={["check", "clock", "list", "signal"][index]} />
              </div>
              <strong>{value ?? "Unavailable"}</strong>
              <small>Saved workspace snapshot</small>
            </div>
          ))}
        </section>
        <small>
          Task counts cover the latest 200 tasks, not lifetime totals. Executed
          means an execution was recorded; inspect its result for the business
          outcome.
        </small>
        <div className="overview-bottom">
          <OverviewCharts data={data} />
          <aside className="overview-attention">
            <div>
              <span>Needs your attention</span>
              <strong>{data.tasks.error ? "—" : pending.length}</strong>
            </div>
            <h2>You have the final say.</h2>
            <p>
              {data.tasks.error
                ? "Task snapshot unavailable. Refresh before reviewing actions."
                : pending.length
                  ? "Review the exact proposal before authorizing an action."
                  : "No owner decisions in the loaded task snapshot."}
            </p>
            <a href="#tasks" onClick={() => setDepartment(initialDepartment || "all")}>
              Open approval inbox <Icon name="chevron" />
            </a>
            <small>Approval can execute an eligible action.</small>
          </aside>
        </div>
        {agentTools}
        <section className="card wide" id="departments">
          <h2>{initialDepartment?`${labels[initialDepartment]} tasks and proposals`:"Your five departments"}</h2>
          <p>
{initialDepartment?"This page shows the selected department. Use Agent workspaces in the sidebar to open another role.":"Select a department to see its tasks and proposal form. CEO planning remains separate from owner authorization."}
          </p>
          {!initialDepartment&&<div className="department-nav" aria-label="Department filters">
            <button
              aria-pressed={department === "all"}
              className="secondary"
              onClick={() => setDepartment("all")}
            >
              All departments
            </button>
            {departments.map((key) => (
              <button
                key={key}
                aria-pressed={department === key}
                className="secondary"
                onClick={() => setDepartment(key)}
              >
                {labels[key]}{" "}
                {business.enabled_agents.includes(key) ? "" : "· disabled"}
              </button>
            ))}
          </div>}
          {data.agents.error ? (
            <p role="alert" className="error">
              Agent status: {data.agents.error}
            </p>
          ) : (
            <div className="department-grid">
              {departments
                .filter((key) => department === "all" || department === key)
                .map((key) => (
                  <article key={key} className="department-card">
                    <h3>{labels[key]}</h3>
                    <p>
                      {business.enabled_agents.includes(key)
                        ? "Enabled"
                        : "Disabled"}{" "}
                      ·{" "}
                      {data.tasks.error
                        ? "Task count unavailable"
                        : `${tasks.filter((t) => t.agent === key).length} recent tasks`}
                    </p>
                    <details>
                      <summary>Recorded agent state</summary>
                      <Evidence
                        value={
                          data.agents.data[key] ?? {
                            status: "No status returned",
                          }
                        }
                      />
                    </details>
                  </article>
                ))}
            </div>
          )}
          {department !== "all" &&
            department !== "ceo" &&
            business.enabled_agents.includes(department) && (
              <form
                key={department}
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = new FormData(e.currentTarget);
                  void run(
                    () => proposeWork(business.id, department, form),
                    "Proposal processed. Its saved status below shows whether it is awaiting approval or already handled by your existing agent policy.",
                  );
                }}
              >
                <h3>Propose {labels[department]} work</h3>
                <DepartmentFields department={department} />
                <p>
                  <small>
                    Values use the existing simulator ledger units. Your
                    configured agent policy may auto-approve eligible simulated
                    work.
                  </small>
                </p>
                <button disabled={busy}>Submit proposal</button>
              </form>
            )}
        </section>
        {(!initialDepartment||initialDepartment==="ceo")&&<section className="card wide" id="ceo-plans">
          <h2>CEO plans and delegation</h2>
          <p>
            Generate a draft, review every assignment, then activate it.
            Activation creates departmental tasks; existing policies can
            auto-execute eligible simulated assignments.
          </p>
          {business.enabled_agents.includes("ceo") && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const form = new FormData(e.currentTarget);
                void run(
                  () => proposePlan(business.id, form),
                  "CEO plan saved. Review its assignments before activation.",
                );
              }}
            >
              <label htmlFor="goal">Business goal</label>
              <textarea
                id="goal"
                name="goal"
                minLength={5}
                maxLength={2000}
                rows={3}
                placeholder="Prepare a product launch within our available budget."
                required
              />
              <button disabled={busy}>Generate draft plan</button>
              <small>
                Uses the configured AI provider. Failure remains visible; no
                fallback plan is presented as an AI result.
              </small>
            </form>
          )}
          {data.plans.error ? (
            <p role="alert" className="error">
              {data.plans.error}
            </p>
          ) : data.plans.data.length ? (
            data.plans.data.map((plan) => (
              <article className="work-item" key={plan.plan_id}>
                <h3>{plan.goal}</h3>
                <span className="status">{display(plan.status)}</span>
                <p>{plan.strategy}</p>
                <details>
                  <summary>
                    Review {plan.assignments.length} assignments
                  </summary>
                  {plan.assignments.map((assignment, i) => (
                    <div className="assignment" key={i}>
                      <h4>
                        {display(assignment.department)} ·{" "}
                        {assignment.objective}
                      </h4>
                      <p>Success criteria: {assignment.success_criteria}</p>
                      <p>Action: {display(assignment.action_type)}</p>
                      <Evidence value={assignment.payload} />
                    </div>
                  ))}
                </details>
                <small>
                  Plan {plan.plan_id} · {timestamp(plan.created_at)}
                </small>
                {plan.status === "draft" &&
                  (activation === plan.plan_id ? (
                    <div className="notice">
                      <p>
                        Activate these assignments? Eligible work may execute
                        under existing automatic policies.
                      </p>
                      <div className="demo-actions">
                        <button
                          disabled={busy}
                          onClick={() =>
                            void run(
                              () => activatePlan(business.id, plan.plan_id),
                              "Plan activation processed. Check individual task statuses for progress and blockers.",
                            )
                          }
                        >
                          Confirm activation
                        </button>
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => setActivation(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p>
                      <button
                        disabled={busy}
                        onClick={() => setActivation(plan.plan_id)}
                      >
                        Review activation
                      </button>
                    </p>
                  ))}
              </article>
            ))
          ) : (
            <p>No CEO plans yet.</p>
          )}
          <small>Latest 100 saved plans.</small>
        </section>}
        <section className="card wide" id="tasks">
          <h2>
            {department === "all"
              ? "Tasks and approvals"
              : `${labels[department]} tasks and approvals`}
          </h2>
          <p>
            Open the exact proposal before deciding. Owner approval can execute
            the action immediately; a new proposal is not proof of completion.
          </p>
          {data.tasks.error ? (
            <p role="alert" className="error">
              {data.tasks.error}
            </p>
          ) : visible.length ? (
            visible.map((task) => (
              <article className="work-item" key={task.id}>
                <div className="work-heading">
                  <h3>{task.objective || display(task.action_type)}</h3>
                  <span className="status">{display(task.status)}</span>
                </div>
                <p>
                  {display(task.agent)} · Requested through{" "}
                  {display(task.source)} ·{" "}
                  {task.mode ||
                    (safeActions.has(task.action_type)
                      ? "Simulated internal action"
                      : "External/media action · dedicated review")}
                </p>
                <dl className="task-meta">
                  <dt>Task</dt>
                  <dd>{task.id}</dd>
                  <dt>CEO review</dt>
                  <dd>
                    {task.ceo_authorized ? "Authorized" : "Not authorized"}
                  </dd>
                  <dt>Created</dt>
                  <dd>{timestamp(task.created_at)}</dd>
                  {task.plan_id && (
                    <>
                      <dt>Parent plan</dt>
                      <dd>{task.plan_id}</dd>
                    </>
                  )}
                  <dt>Success criteria</dt>
                  <dd>{task.success_criteria || "Not recorded"}</dd>
                  <dt>Deadline</dt>
                  <dd>No deadline recorded</dd>
                </dl>
                <details>
                  <summary>Proposal, review and recorded result</summary>
                  <h4>Exact action · {display(task.action_type)}</h4>
                  <Evidence value={task.payload} />
                  {task.revision_error && (
                    <p role="alert" className="error">
                      {task.revision_error}
                    </p>
                  )}
                  {task.previous_payload && (
                    <>
                      <h4>Before the last revision</h4>
                      <Evidence value={task.previous_payload} />
                    </>
                  )}
                  <h4>CEO review</h4>
                  <Evidence
                    value={task.ceo_review ?? { status: "No review recorded" }}
                  />
                  <h4>Execution result</h4>
                  <Evidence
                    value={
                      task.result ?? { status: "No execution result recorded" }
                    }
                  />
                  {task.owner_feedback && (
                    <p>Owner feedback: {task.owner_feedback}</p>
                  )}
                  {task.executed_at && (
                    <p>Execution recorded {timestamp(task.executed_at)}</p>
                  )}
                </details>
                {decisionAllowed(task) &&
                  (selected?.id === task.id ? (
                    <div className="approval-preview">
                      <h4>Owner decision · {display(selected.action_type)}</h4>
                      <Evidence value={selected.payload} />
                      <p>
                        Approve authorizes this exact displayed request through
                        the existing backend pipeline. Refresh first if another
                        session has changed it.
                      </p>
                      <label htmlFor={`feedback-${task.id}`}>
                        Feedback for rejection (optional)
                      </label>
                      <textarea
                        id={`feedback-${task.id}`}
                        value={feedback}
                        maxLength={2000}
                        onChange={(e) => setFeedback(e.target.value)}
                        rows={2}
                      />
                      <div className="demo-actions">
                        <button
                          disabled={busy}
                          onClick={() =>
                            void run(
                              () =>
                                decideTask(
                                  business.id,
                                  task.id,
                                  "approve",
                                  "",
                                  selected.approval_fingerprint || "",
                                ),
                              "Approval processed. Read the saved result; approval does not guarantee a successful outcome.",
                            )
                          }
                        >
                          Approve and execute
                        </button>
                        {[
                          "budget_request",
                          "campaign_launch",
                          "recruitment_request",
                          "resource_request",
                          "dataset_launch",
                        ].includes(task.action_type) && (
                          <button
                            disabled={busy}
                            onClick={() =>
                              void run(
                                () =>
                                  decideTask(
                                    business.id,
                                    task.id,
                                    "approve",
                                    "",
                                    selected.approval_fingerprint || "",
                                    true,
                                  ),
                                "Approved and queued. Follow progress in Jobs, deadlines, knowledge & MCP.",
                              )
                            }
                          >
                            Approve and queue
                          </button>
                        )}

                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() =>
                            void run(
                              () =>
                                decideTask(
                                  business.id,
                                  task.id,
                                  "reject",
                                  feedback,
                                  selected.approval_fingerprint || "",
                                ),
                              "Rejection recorded.",
                            )
                          }
                        >
                          Reject proposal
                        </button>
                        <button
                          className="secondary"
                          disabled={busy}
                          onClick={() => setSelected(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p>
                      <button
                        disabled={busy}
                        onClick={() => {
                          setSelected(task);
                          setFeedback("");
                        }}
                      >
                        Review owner decision
                      </button>
                    </p>
                  ))}
                {!decisionAllowed(task) &&
                  [
                    "pending_approval",
                    "awaiting_asset",
                    "needs_changes",
                  ].includes(task.status) && (
                    <p className="notice">
                      Resolve requested revisions before approval. External
                      publication and media actions require their dedicated
                      workflow.
                    </p>
                  )}
              </article>
            ))
          ) : (
            <p>
              No tasks in this department yet. Propose work or activate a CEO
              plan.
            </p>
          )}
        </section>
        <section className="card wide" id="reports">
          <h2>Department reports to the CEO</h2>
          <p>
            These are saved execution reports. Failed and denied outcomes remain
            visible alongside successful ones.
          </p>
          {data.reports.error ? (
            <p role="alert" className="error">
              {data.reports.error}
            </p>
          ) : (initialDepartment?data.reports.data.filter(r=>r.department===initialDepartment):data.reports.data).length ? (
            (initialDepartment?data.reports.data.filter(r=>r.department===initialDepartment):data.reports.data).map((report) => (
              <article className="work-item" key={report.report_id}>
                <h3>{report.objective}</h3>
                <p>
                  {display(report.department)} · {display(report.status)} · CEO
                  review {display(report.review_status)}
                </p>
                <small>
                  Task {report.task_id} · {timestamp(report.created_at)}
                </small>
                <details>
                  <summary>Recorded evidence and CEO assessment</summary>
                  <Evidence
                    value={{
                      result: report.result,
                      ceo_review: report.ceo_review,
                    }}
                  />
                </details>
              </article>
            ))
          ) : (
            <p>
              No department reports yet. The dataset laboratory shows its own
              five-department report inside the launch result.
            </p>
          )}
          <small>Latest 100 reports.</small>
        </section>
      </div>
    </div>
  );
}
