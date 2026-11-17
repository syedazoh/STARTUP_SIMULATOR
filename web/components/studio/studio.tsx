"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  AGENTS,
  humanize,
  isPending,
  taskPhase,
  observedChanges,
  previewTransfers,
  agentId,
} from "../../../frontend/src/studio/model.mjs";
import { decisionAllowed } from "../../lib/workspace-contracts";
import { resolveMessage } from "../../../frontend/src/components/boardroom/eventRoutes";
import {
  loadStudio,
  decideStudioTask,
} from "../../app/workspace/[businessId]/boardroom/actions";
import Scene from "./scene";
import Icon from "./icon";
import type { Snapshot, Task, Transfer } from "./types";

const time = (value?: string) => {
  if (!value || Number.isNaN(Date.parse(value))) return "Recorded";
  return new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
};
const initials: Record<string, string> = {
  ceo: "CX",
  finance: "FN",
  marketing: "MK",
  hr: "HR",
  operations: "OP",
};
export default function Studio({
  businessId,
  name,
  initial,
}: {
  businessId: string;
  name: string;
  initial: Snapshot;
}) {
  const [snapshot, setSnapshot] = useState(initial),
    [selected, setSelected] = useState("ceo"),
    [preview, setPreview] = useState(false),
    [transfer, setTransfer] = useState<Transfer | null>(null),
    [previewTransfer, setPreviewTransfer] = useState<Transfer | null>(null);
  const [busy, setBusy] = useState(""),
    [feedback, setFeedback] = useState(""),
    [refreshing, setRefreshing] = useState(false);
  const previous = useRef<Map<string, Task> | null>(
    initial.tasksReady ? new Map(initial.tasks.map((t) => [t.id, t])) : null,
  );
  const seenEvents = useRef(new Set(initial.events.map((e) => e.event_id))),
    eventsInitialized = useRef(
      !initial.errors.some((e) => e.startsWith("Activity")),
    );
  const queue = useRef<Transfer[]>([]),
    mounted = useRef(true),
    requesting = useRef(false),
    latest = useRef(initial);
  const refresh = useCallback(async () => {
    if (requesting.current) return;
    requesting.current = true;
    setRefreshing(true);
    try {
      const next = await loadStudio(businessId);
      if (!mounted.current) return;
      if (next.tasksReady) {
        queue.current.push(...observedChanges(previous.current, next.tasks));
        previous.current = new Map(next.tasks.map((t) => [t.id, t]));
      }
      if (!next.errors.some((e) => e.startsWith("Activity"))) {
        if (eventsInitialized.current) {
          for (const event of next.events) {
            if (seenEvents.current.has(event.event_id)) continue;
            const route = resolveMessage(event);
            if (route?.sender && route.receiver)
              queue.current.push({
                ...route,
                sender: route.sender,
                receiver: route.receiver,
                label: humanize(event.event_type),
                title:
                  typeof event.data?.message === "string"
                    ? event.data.message
                    : humanize(event.event_type),
                status: event.event_type,
                source: "backend",
              });
          }
        }
        seenEvents.current = new Set(next.events.map((e) => e.event_id));
        eventsInitialized.current = true;
      }
      queue.current = queue.current.slice(-32);
      const merged = {
        ...next,
        tasks: next.tasksReady ? next.tasks : latest.current.tasks,
        statuses: next.errors.some((e) => e.startsWith("Agent"))
          ? latest.current.statuses
          : next.statuses,
        events: next.errors.some((e) => e.startsWith("Activity"))
          ? latest.current.events
          : next.events,
      };
      latest.current = merged;
      setSnapshot(merged);
    } catch {
      if (mounted.current)
        setSnapshot({
          ...latest.current,
          errors: [
            "The workspace could not refresh. Check your connection and retry.",
          ],
        });
    } finally {
      requesting.current = false;
      if (mounted.current) setRefreshing(false);
    }
  }, [businessId]);
  useEffect(() => {
    mounted.current = true;
    const interval = setInterval(() => {
      if (!document.hidden) void refresh();
    }, 5000);
    return () => {
      mounted.current = false;
      clearInterval(interval);
    };
  }, [refresh]);
  useEffect(() => {
    const interval = setInterval(() => {
      const next = queue.current.shift();
      if (next) setTransfer(next);
    }, 4200);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    if (!preview) {
      setPreviewTransfer(null);
      return;
    }
    let index = 0;
    const transfers = previewTransfers();
    setPreviewTransfer(transfers[index] as Transfer);
    const interval = setInterval(() => {
      index = (index + 1) % transfers.length;
      setPreviewTransfer(transfers[index] as Transfer);
    }, 4200);
    return () => clearInterval(interval);
  }, [preview]);
  async function decide(task: Task, decision: "approve" | "reject") {
    setBusy(task.id);
    setFeedback("");
    try {
      const result = await decideStudioTask(
        businessId,
        task.id,
        decision,
        task.approval_fingerprint || "",
      );
      if (!result.ok) {
        setFeedback(result.error);
        return;
      }
      setFeedback(
        decision === "approve"
          ? "Decision saved. The backend result is shown below."
          : "Task rejected.",
      );
      await refresh();
    } finally {
      setBusy("");
    }
  }
  const agent = AGENTS.find((a) => a.id === selected) || AGENTS[0];
  const approvals = snapshot.tasks.filter(
      (task) => isPending(task) && decisionAllowed(task),
    ),
    working = snapshot.tasks.filter((t) =>
      ["queued", "executing", "approved"].includes(t.status),
    );
  const completed = snapshot.tasks.filter((t) =>
    ["executed", "verified_complete"].includes(t.status),
  );
  const selectedTasks = snapshot.tasks.filter(
    (t) => agentId(t.agent) === selected,
  );
  const activeTransfer = preview ? previewTransfer : transfer;
  const activity = preview
    ? previewTransfers()
        .slice(0, 3)
        .map((t) => ({
          id: t.id,
          title: t.title,
          route: `${humanize(t.sender)} → ${humanize(t.receiver)}`,
          time: "Visual preview",
        }))
    : snapshot.events
        .slice(-4)
        .reverse()
        .map((e) => {
          const route = resolveMessage(e);
          return {
            id: e.event_id,
            title: humanize(e.event_type),
            route: route
              ? `${humanize(route.sender)} → ${humanize(route.receiver)}`
              : humanize(e.source || "System"),
            time: time(e.timestamp),
          };
        });
  return (
    <div className="studio-root">
      <aside className="studio-sidebar" aria-label="Workspace navigation">
        <a className="studio-wordmark" href="/workspace">
          <span>
            <Icon name="studio" size={23} />
          </span>
          <strong>
            Startup<span>simulator</span>
          </strong>
        </a>
        <a className="studio-business" href="/workspace">
          <span>{name.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{name}</strong>
            <small>Business workspace</small>
          </div>
          <Icon name="chevron" size={15} />
        </a>
        <nav className="studio-primary-nav">
          <a
            className="active"
            href={`/workspace/${businessId}/boardroom`}
            aria-current="page"
          >
            <Icon name="cube" />
            Executive studio
          </a>
          <a href={`/workspace/${businessId}`}>
            <Icon name="grid" />
            Command center
          </a>
          <a href={`/workspace/${businessId}/automation`}>
            <Icon name="signal" />
            Automation &amp; knowledge
          </a>
          <a href={`/workspace/${businessId}/demo`}>
            <Icon name="grid" />
            Launch laboratory
          </a>
          <a href="/workspace">
            <Icon name="back" />
            All businesses
          </a>
        </nav>
        <div className="studio-team-heading">
          <h2>Your executive team</h2>
          <span>5 roles</span>
        </div>
        <nav className="studio-team-nav" aria-label="Select department">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              aria-pressed={selected === a.id}
              onClick={() => setSelected(a.id)}
            >
              <span
                className="studio-avatar-small"
                style={{ "--agent-color": a.color } as React.CSSProperties}
              >
                {initials[a.id]}
              </span>
              <span>
                <strong>{a.label}</strong>
                <small>{a.role}</small>
              </span>
              <i
                className={
                  snapshot.statuses[a.id] ? "status-dot" : "status-dot offline"
                }
              />
            </button>
          ))}
        </nav>
        <div className="studio-sidebar-footer">
          <Icon name="signal" size={17} />
          <div>
            <strong>
              {snapshot.errors.length
                ? "Connection needs attention"
                : "Business-scoped workspace"}
            </strong>
            <small>Approvals stay in your hands.</small>
          </div>
        </div>
      </aside>
      <div className="studio-content">
        <header className="studio-header">
          <div>
            <a href="/workspace">Workspace</a>
            <Icon name="chevron" size={13} />
            <span>Executive studio</span>
          </div>
          <a className="studio-owner" href="/workspace">
            <span>Y</span>Owner workspace
          </a>
        </header>
        <main className="studio-main">
          <div className="studio-page-title">
            <div>
              <h1>
                Your team. <span>In motion.</span>
              </h1>
              <p>
                A shared floor for ideas, decisions and the work between them.
              </p>
            </div>
            <a
              className="studio-primary-button"
              href={`/workspace/${businessId}/demo`}
            >
              <Icon name="play" size={16} />
              New launch scenario
              <Icon name="arrow" size={17} />
            </a>
          </div>
          <div className="studio-status-strip">
            <span
              className={`studio-live-label ${preview ? "is-preview" : ""}`}
            >
              <i className="status-dot" />
              {preview
                ? "Visual preview · synthetic"
                : snapshot.errors.length
                  ? "Connection interrupted"
                  : "Backend connected"}
            </span>
            <span>
              {preview
                ? "Illustrative handoffs. No tasks or approvals are created."
                : "Task and event snapshots refresh every 5 seconds."}
            </span>
            <button
              onClick={() => void refresh()}
              disabled={refreshing}
              aria-label="Refresh workspace"
            >
              <Icon name="refresh" size={14} />
              {refreshing ? "Refreshing" : "Refresh"}
            </button>
          </div>
          {snapshot.errors.length > 0 && (
            <p className="studio-error" role="alert">
              {snapshot.errors.join(" ")} Last available records remain visible.{" "}
              <button onClick={() => void refresh()}>Retry connection</button>
            </p>
          )}
          <div className="studio-workspace-grid">
            <div className="studio-floor-column">
              <div className="studio-floor-heading">
                <h2>The executive floor</h2>
                <button
                  className={
                    preview ? "preview-button active" : "preview-button"
                  }
                  onClick={() => setPreview(!preview)}
                >
                  <Icon name={preview ? "pause" : "play"} size={14} />
                  {preview ? "Exit visual preview" : "Preview a task handoff"}
                </button>
              </div>
              <Scene
                selected={selected}
                onSelect={setSelected}
                transfer={activeTransfer}
              />
              <div className="studio-roster">
                {AGENTS.map((a) => (
                  <button
                    key={a.id}
                    aria-pressed={selected === a.id}
                    onClick={() => setSelected(a.id)}
                  >
                    <span className="roster-mark" style={{ color: a.color }}>
                      <Icon name="cube" size={19} />
                    </span>
                    <strong>{a.label}</strong>
                    <small>
                      {snapshot.statuses[a.id]
                        ? "State available"
                        : "No snapshot"}
                    </small>
                  </button>
                ))}
              </div>
              <section className="studio-selected">
                <div
                  className="selected-avatar"
                  style={
                    { "--agent-color": agent.color } as React.CSSProperties
                  }
                >
                  {initials[selected]}
                </div>
                <div>
                  <h2>
                    {agent.label}
                    <span>{agent.role}</span>
                  </h2>
                  <p>
                    {selectedTasks.length
                      ? `${selectedTasks.length} task${selectedTasks.length === 1 ? "" : "s"} in the loaded snapshot`
                      : "No tasks in the loaded snapshot"}
                  </p>
                </div>
                <span className="selected-state">
                  {snapshot.statuses[selected]
                    ? "State available"
                    : "Awaiting backend"}
                </span>
              </section>
              <div className="studio-state-details">
                <details>
                  <summary>
                    Inspect {agent.label} tasks and state{" "}
                    <Icon name="chevron" size={14} />
                  </summary>
                  <div className="studio-inspection">
                    {selectedTasks.slice(0, 8).map((t) => (
                      <p key={t.id}>
                        <strong>
                          {t.objective || humanize(t.action_type)}
                        </strong>
                        <span>{taskPhase(t)}</span>
                      </p>
                    ))}
                    <dl>
                      {Object.entries(snapshot.statuses[selected] || {})
                        .filter(([, v]) =>
                          ["string", "number", "boolean"].includes(typeof v),
                        )
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <div key={key}>
                            <dt>{humanize(key)}</dt>
                            <dd>{String(value)}</dd>
                          </div>
                        ))}
                    </dl>
                    {!snapshot.statuses[selected] && (
                      <p>
                        Agent state is not available. Refresh after checking the
                        backend.
                      </p>
                    )}
                  </div>
                </details>
              </div>
            </div>
            <aside className="studio-work-column">
              <section className="studio-attention">
                <div>
                  <Icon name="clock" size={20} />
                  <span>Your attention</span>
                  <strong>{approvals.length}</strong>
                </div>
                <h2>You have the final say.</h2>
                <p>
                  {approvals.length
                    ? `${approvals.length} loaded task${approvals.length === 1 ? " is" : "s are"} waiting for your decision.`
                    : "Nothing waiting for approval in this snapshot."}
                </p>
                <span>Inspect the exact action before approving.</span>
              </section>
              <section className="studio-task-section">
                <div className="studio-section-title">
                  <h2>{preview ? "Illustrative handoff" : "Approval inbox"}</h2>
                  <span>
                    {preview ? "Preview" : `${approvals.length} pending`}
                  </span>
                </div>
                {preview ? (
                  <div className="studio-preview-task">
                    <span className="task-badge">Synthetic visual preview</span>
                    <h3>{previewTransfer?.title || "Preparing handoff"}</h3>
                    <p>
                      {humanize(previewTransfer?.sender || "ceo")}
                      <Icon name="arrow" size={14} />
                      {humanize(previewTransfer?.receiver || "marketing")}
                    </p>
                    <strong>{previewTransfer?.label}</strong>
                    <small>
                      This animation never sends, accepts or executes a real
                      task.
                    </small>
                  </div>
                ) : approvals.length === 0 ? (
                  <div className="studio-inbox-empty">
                    <Icon name="check" size={27} />
                    <strong>All clear for now.</strong>
                    <p>
                      Tasks needing a decision will appear here. You can explore
                      the handoff preview while your team is idle.
                    </p>
                  </div>
                ) : (
                  <div className="studio-approval-list">
                    {approvals.slice(0, 8).map((task) => (
                      <article key={task.id} className="studio-task">
                        <div>
                          <span className="task-badge">
                            {task.mode === "simulation"
                              ? "Simulation"
                              : "Approval required"}
                          </span>
                          <small>{humanize(task.agent)}</small>
                        </div>
                        <h3>{task.objective || humanize(task.action_type)}</h3>
                        <p>{taskPhase(task)}</p>
                        <details>
                          <summary>
                            Review exact action{" "}
                            <Icon name="chevron" size={14} />
                          </summary>
                          <dl>
                            <div>
                              <dt>Action</dt>
                              <dd>{humanize(task.action_type)}</dd>
                            </div>
                            <div>
                              <dt>Task</dt>
                              <dd>{task.id}</dd>
                            </div>
                            {task.approval_expires_at && (
                              <div>
                                <dt>Expires</dt>
                                <dd>
                                  {new Date(
                                    task.approval_expires_at,
                                  ).toLocaleString()}
                                </dd>
                              </div>
                            )}
                          </dl>
                          <pre>{JSON.stringify(task.payload, null, 2)}</pre>
                          <p className="studio-action-warning">
                            {task.mode === "simulation"
                              ? "This is a synthetic simulation."
                              : "Approval may execute this action immediately through the existing task pipeline."}
                          </p>
                          <div className="studio-task-actions">
                            <button
                              disabled={!!busy}
                              onClick={() => void decide(task, "reject")}
                            >
                              Reject
                            </button>
                            <button
                              disabled={!!busy}
                              onClick={() => void decide(task, "approve")}
                            >
                              <Icon name="check" size={15} />
                              {busy === task.id ? "Saving…" : "Approve action"}
                            </button>
                          </div>
                        </details>
                      </article>
                    ))}
                  </div>
                )}
                {feedback && (
                  <p role="status" className="studio-feedback">
                    {feedback}
                  </p>
                )}
              </section>
              <div className="studio-task-totals">
                <div>
                  <span>Working / queued</span>
                  <strong>{working.length}</strong>
                </div>
                <div>
                  <span>Executed / verified</span>
                  <strong>{completed.length}</strong>
                </div>
                <small>Counts reflect the latest 200 loaded tasks.</small>
              </div>
            </aside>
          </div>
          <section className="studio-activity">
            <div className="studio-section-title">
              <h2>Across the floor</h2>
              <span>{preview ? "Synthetic preview" : "Recorded activity"}</span>
            </div>
            {activity.length ? (
              <div className="studio-activity-list">
                {activity.map((a) => (
                  <article key={a.id}>
                    <span className="activity-icon">
                      <Icon name="arrow" size={16} />
                    </span>
                    <div>
                      <strong>{a.title}</strong>
                      <p>{a.route}</p>
                    </div>
                    <time>{a.time}</time>
                  </article>
                ))}
              </div>
            ) : (
              <p className="studio-no-events">
                No events recorded yet. Task state and approvals are shown
                above; activity will appear when the backend records it.
              </p>
            )}
          </section>
          <footer className="studio-footer">
            <span>Five departments. One shared direction.</span>
            <span>Last refresh {time(snapshot.updatedAt)}</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
