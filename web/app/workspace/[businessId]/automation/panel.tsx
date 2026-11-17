"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { automationCommand, readAutomation } from "./actions";
type Job = {
  job_id: string;
  kind: string;
  status: string;
  attempts: number;
  error?: string;
  result?: unknown;
};
type Doc = {
  document_id: string;
  key: string;
  title: string;
  version: number;
  status: string;
  departments: string[];
  dense_status?: string;
};
type Task = {
  id: string;
  action_type: string;
  status: string;
  deadline_version: number;
  due_at?: string;
};
type Grant = {
  grant_id: string;
  expires_ts: number;
  departments: string[];
  scopes: string[];
  revoked: boolean;
};
type Note = {
  notification_id: string;
  task_id: string;
  kind: string;
  read: boolean;
};
type Overview = {
  enabled: boolean;
  durable: boolean;
  worker_heartbeat?: number;
  worker_error?: string;
  jobs: Job[];
  documents: Doc[];
  tasks: Task[];
  grants: Grant[];
  notifications: Note[];
};
function Json({ value }: { value: unknown }) {
  return <pre>{JSON.stringify(value, null, 2)}</pre>;
}
function Scopes({ departments }: { departments: string[] }) {
  return (
    <fieldset>
      <legend>Allowed departments</legend>
      {departments.map((d) => (
        <label key={d} className="inline-label">
          <input
            type="checkbox"
            name="departments"
            value={d}
            defaultChecked={d === "ceo"}
          />
          {d}
        </label>
      ))}
    </fieldset>
  );
}
export default function Automation({
  businessId,
  departments,
  initial,
}: {
  businessId: string;
  departments: string[];
  initial: Awaited<ReturnType<typeof readAutomation>>;
}) {
  const [data, setData] = useState<Overview | null>(
    initial.ok ? initial.data : null,
  );
  const [error, setError] = useState(initial.ok ? "" : initial.error),
    [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false),
    [text, setText] = useState("");
  const [result, setResult] = useState<unknown>(null),
    [token, setToken] = useState("");
  const flight = useRef(false),
    mutation = useRef(false),
    mounted = useRef(true);
  async function refresh() {
    if (flight.current || mutation.current) return;
    flight.current = true;
    try {
      const r = await readAutomation(businessId);
      if (mounted.current && !mutation.current) {
        if (r.ok) {
          setData(r.data);
          setError("");
        } else setError(r.error);
      }
    } finally {
      flight.current = false;
    }
  }
  useEffect(() => {
    mounted.current = true;
    const timer = setInterval(() => void refresh(), 4000);
    return () => {
      mounted.current = false;
      clearInterval(timer);
    };
  }, [businessId]);
  async function run(
    command: string,
    payload: Record<string, unknown> = {},
    target = "",
    version = 0,
  ) {
    if (mutation.current) return;
    mutation.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const r = await automationCommand(
        businessId,
        command,
        payload,
        target,
        version,
      );
      if (!r.ok) {
        setError(r.error);
        return;
      }
      if (command === "grant") setToken(r.data.token);
      if (command === "answer" || command === "search") setResult(r.data);
      setMessage(
        ["job", "document", "reindex"].includes(command)
          ? "Queued. Follow the saved job status below."
          : "Saved.",
      );
    } catch {
      setError(
        "Request failed. Refresh before retrying; work may still be processing.",
      );
    } finally {
      mutation.current = false;
      setBusy(false);
      await refresh();
    }
  }
  function form(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    return new FormData(e.currentTarget);
  }
  function roles(f: FormData) {
    return f.getAll("departments").map(String);
  }

  return (
    <div className="command-center">
      <a href={`/workspace/${encodeURIComponent(businessId)}`}>
        ← Command Center
      </a>
      <h1>Automation &amp; knowledge</h1>
      <p>
        Jobs, deadlines, authorized document evidence and private MCP access for
        this business.
      </p>
      <button type="button" disabled={busy} onClick={() => void refresh()}>
        Refresh status
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {message && <p role="status">{message}</p>}
      <p>
        Worker: {data?.enabled ? "enabled" : "disabled"} · Storage:{" "}
        {data?.durable ? "MongoDB" : "unavailable"} · Last heartbeat:{" "}
        {data?.worker_heartbeat
          ? new Date(data.worker_heartbeat * 1000).toLocaleTimeString()
          : "not received"}
      </p>
      {data?.worker_error && <p className="error">{data.worker_error}</p>}
      {!data?.enabled && (
        <p>
          Set BACKGROUND_JOBS_ENABLED=True in backend/.env and restart the
          backend.
        </p>
      )}
      <fieldset disabled={busy} className="automation-controls">
        <section className="card wide">
          <h2>Background work</h2>
          <form
            onSubmit={(e) => {
              const f = form(e);
              void run("job", {
                kind: "ceo_plan",
                goal: String(f.get("goal")),
                idempotency_key: crypto.randomUUID(),
              });
            }}
          >
            <label>
              CEO plan goal
              <textarea name="goal" required minLength={5} maxLength={2000} />
            </label>
            <button disabled={!data?.enabled || !data?.durable}>
              Queue draft plan
            </button>
          </form>
          <p>Review and activate the resulting draft in the Command Center.</p>
          <button
            type="button"
            disabled={!data?.enabled || !data?.durable}
            onClick={() =>
              void run("job", {
                kind: "daily_brief",
                idempotency_key: crypto.randomUUID(),
              })
            }
          >
            Queue task-status brief
          </button>
          <ul>
            {data?.jobs.map((j) => (
              <li key={j.job_id}>
                <strong>{j.kind}</strong> — {j.status}, attempt {j.attempts}{" "}
                {j.error && <p>{j.error}</p>}
                {["queued", "retry_scheduled"].includes(j.status) && (
                  <button
                    type="button"
                    onClick={() => void run("cancel", {}, j.job_id)}
                  >
                    Cancel job
                  </button>
                )}
                {j.status === "failed" && j.kind !== "execute_task" && (
                  <button
                    type="button"
                    onClick={() => void run("retry", {}, j.job_id)}
                  >
                    Retry job
                  </button>
                )}
                {j.result != null && (
                  <details>
                    <summary>Job result</summary>
                    <Json value={j.result} />
                  </details>
                )}
              </li>
            ))}
          </ul>
        </section>
        <section className="card wide">
          <h2>Task deadlines</h2>
          <p>
            Your device timezone is converted to UTC. Reminders and CEO
            escalation appear here; no email is sent.
          </p>
          <form
            onSubmit={(e) => {
              const f = form(e),
                id = String(f.get("task")),
                task = data?.tasks.find((t) => t.id === id),
                date = new Date(String(f.get("due")));
              if (!Number.isFinite(date.getTime())) {
                setError("Choose a valid due date.");
                return;
              }
              void run(
                "deadline",
                {
                  due_at: date.toISOString(),
                  expected_version: task?.deadline_version || 0,
                  reason: String(f.get("reason")),
                  reminder_minutes: Number(f.get("reminder")),
                  escalation_minutes: Number(f.get("escalation")),
                },
                id,
              );
            }}
          >
            <label htmlFor="deadline-task">Task</label>
            <select id="deadline-task" name="task" required>
              <option value="">Choose pending task</option>
              {data?.tasks
                .filter((t) =>
                  [
                    "pending_approval",
                    "needs_changes",
                    "pending_ceo_review",
                    "needs_revision",
                    "awaiting_asset",
                  ].includes(t.status),
                )
                .map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.action_type} · {t.id.slice(0, 8)}
                    {t.due_at
                      ? ` · due ${new Date(t.due_at).toLocaleString()}`
                      : ""}
                  </option>
                ))}
            </select>
            <label>
              Due date &amp; time
              <input name="due" type="datetime-local" required />
            </label>
            <label>
              Reminder minutes before
              <input
                name="reminder"
                type="number"
                min={0}
                max={10080}
                defaultValue={60}
                required
              />
            </label>
            <label>
              Escalate minutes after
              <input
                name="escalation"
                type="number"
                min={1}
                max={10080}
                defaultValue={60}
                required
              />
            </label>
            <label>
              Reason
              <input name="reason" maxLength={500} required />
            </label>
            <button>Save deadline</button>
          </form>
          <ul>
            {data?.notifications.map((n) => (
              <li key={n.notification_id}>
                {n.kind}: {n.task_id.slice(0, 8)}{" "}
                {n.read ? (
                  "(read)"
                ) : (
                  <button
                    type="button"
                    onClick={() => void run("read", {}, n.notification_id)}
                  >
                    Mark read
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
        <section className="card wide">
          <h2>Business knowledge</h2>
          <p>
            Plain text or Markdown. Reuse a document key to replace its current
            version. Department permissions apply before retrieval.
          </p>
          <form
            onSubmit={(e) => {
              const f = form(e),
                key = String(f.get("key")),
                old = data?.documents.find((d) => d.key === key);
              void run("document", {
                key,
                title: String(f.get("title")),
                text,
                departments: roles(f),
                expected_version: old?.version || 0,
              });
            }}
          >
            <label>
              Document key
              <input
                name="key"
                pattern="[A-Za-z0-9_-]+"
                maxLength={100}
                required
              />
            </label>
            <label>
              Title
              <input name="title" maxLength={200} required />
            </label>
            <label>
              Text file
              <input
                type="file"
                accept=".txt,.md,text/plain,text/markdown"
                onChange={async (e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  if (f.size > 262144) {
                    setError("Choose a file below 256 KB.");
                    return;
                  }
                  try {
                    setText(await f.text());
                  } catch {
                    setError("File could not be read.");
                  }
                }}
              />
            </label>
            <label>
              Document text
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={7}
                maxLength={262144}
                required
              />
            </label>
            <Scopes departments={departments} />
            <button disabled={!data?.enabled || !data?.durable}>
              Queue document indexing
            </button>
          </form>
          <ul>
            {data?.documents.map((d) => (
              <li key={d.document_id}>
                {d.title} v{d.version} — {d.status} · {d.departments.join(", ")}{" "}
                · dense {d.dense_status || "pending"}
                <button
                  type="button"
                  onClick={() =>
                    void run("reindex", {}, d.document_id, d.version)
                  }
                >
                  Reindex
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm(`Delete ${d.title}?`))
                      void run("delete", {}, d.document_id, d.version);
                  }}
                >
                  Delete document
                </button>
              </li>
            ))}
          </ul>
          <form
            onSubmit={(e) => {
              const f = form(e);
              void run("answer", {
                query: String(f.get("query")),
                department: String(f.get("department")),
              });
            }}
          >
            <label>
              Ask the documents
              <input name="query" minLength={2} maxLength={1000} required />
            </label>
            <label htmlFor="knowledge-department">Department</label>
            <select id="knowledge-department" name="department">
              {departments.map((d) => (
                <option key={d}>{d}</option>
              ))}
            </select>
            <button>Answer with evidence</button>
          </form>
          {result != null && (
            <details open>
              <summary>Answer, source versions &amp; retrieval mode</summary>
              <Json value={result} />
            </details>
          )}
        </section>
        <section className="card wide">
          <h2>Private MCP access</h2>
          <p>
            15-minute access to this business and selected departments.
            Proposals still require CEO and owner review.
          </p>
          <form
            onSubmit={(e) => {
              const f = form(e);
              void run("grant", {
                departments: roles(f),
                allow_proposals: f.has("allow_proposals"),
              });
            }}
          >
            <Scopes departments={departments} />
            <label className="inline-label">
              <input name="allow_proposals" type="checkbox" />
              Allow internal task proposals
            </label>
            <button disabled={!data?.durable}>Create access token</button>
          </form>
          {token && (
            <div>
              <p>
                Keep this private. Copy it into a trusted client's bearer
                header; it is shown only in this tab.
              </p>
              <textarea
                aria-label="MCP access token"
                readOnly
                value={token}
                rows={4}
              />
              <button type="button" onClick={() => setToken("")}>
                Hide token
              </button>
            </div>
          )}
          <ul>
            {data?.grants.map((g) => (
              <li key={g.grant_id}>
                {g.departments.join(", ")} · expires{" "}
                {new Date(g.expires_ts * 1000).toLocaleString()} ·{" "}
                {g.revoked
                  ? "revoked"
                  : g.expires_ts * 1000 < Date.now()
                    ? "expired"
                    : "active"}
                {!g.revoked && (
                  <button
                    type="button"
                    onClick={() => void run("revoke", {}, g.grant_id)}
                  >
                    Revoke access
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>
      </fieldset>
    </div>
  );
}
