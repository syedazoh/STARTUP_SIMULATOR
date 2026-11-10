"use client";
import { useState } from "react";
import { demoRead, demoImport, demoCommand, demoDecision } from "./actions";

type Metrics = {
  currency: string;
  revenue_minor: number;
  contribution_minor: number;
  ending_cash_minor: number;
  fulfilled_units: number;
  remaining_inventory: number;
  goal_met: boolean;
  baseline?: Metrics;
  baseline_blocker?: string | null;
  ceo_report?: { summary: string };
};
type Source = {
  citation: { document_id: string; version: number; title: string };
  text: string;
};
type Task = {
  id: string;
  status: string;
  payload: { budget_minor: number };
  proposal_digest: string;
  approval_expires_at: string;
  result?: Metrics;
  ceo_review?: {
    reason: string;
    basis: string;
    forecast?: Metrics;
    departments?: Record<
      string,
      { sources: Source[]; analysis: Record<string, unknown> }
    >;
  };
};
type Import = {
  import_id: string;
  digest: string;
  data: {
    dataset_id: string;
    currency: string;
    company: { name: string };
    campaigns: { id: string; name: string; budget_minor: number }[];
  };
  tasks: Task[];
};
type Dashboard = { imports: Import[] };
async function checked<T>(
  promise: Promise<{ ok: true; data: unknown } | { ok: false; error: string }>,
): Promise<T> {
  const result = await promise;
  if (!result.ok) throw new Error(result.error);
  return result.data as T;
}
type Preview = {
  digest: string;
  dataset_id: string;
  counts: Record<string, number>;
  duplicate: boolean;
  conflict: boolean;
  preview: unknown;
};
type Reset = {
  import_id: string;
  digest: string;
  records: number;
  tasks: number;
  effect: string;
};
const money = (value: number, currency: string) =>
  new Intl.NumberFormat("en", { style: "currency", currency }).format(
    value / 100,
  );

function Results({ result, label }: { result: Metrics; label: string }) {
  return (
    <section aria-label={label}>
      <h3>{label}</h3>
      <dl className="demo-metrics">
        <div>
          <dt>New units fulfilled</dt>
          <dd>{result.fulfilled_units}</dd>
        </div>
        <div>
          <dt>Simulated revenue</dt>
          <dd>{money(result.revenue_minor, result.currency)}</dd>
        </div>
        <div>
          <dt>Contribution after campaign</dt>
          <dd>{money(result.contribution_minor, result.currency)}</dd>
        </div>
        <div>
          <dt>Ending cash</dt>
          <dd>{money(result.ending_cash_minor, result.currency)}</dd>
        </div>
        <div>
          <dt>Remaining inventory</dt>
          <dd>{result.remaining_inventory}</dd>
        </div>
        <div>
          <dt>Goal met</dt>
          <dd>{result.goal_met ? "Yes" : "No"}</dd>
        </div>
      </dl>
    </section>
  );
}
export default function Demo({
  businessId,
  initial,
}: {
  businessId: string;
  initial: Dashboard;
}) {
  const [dashboard, setDashboard] = useState(initial);
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState("json");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [reset, setReset] = useState<Reset | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setDashboard(await checked<Dashboard>(demoRead(businessId)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed; retry.");
    } finally {
      setBusy(false);
    }
  }
  async function upload(commit: boolean) {
    if (!file) throw new Error("Choose a dataset file.");
    const form = new FormData();
    form.set("file", file);
    form.set("format", format);
    form.set("action", commit ? "commit" : "preview");
    form.set("expected_digest", preview?.digest || "");
    const result = await checked<Preview & { duplicate: boolean }>(
      demoImport(businessId, form),
    );
    if (commit) {
      setPreview(null);
      setNotice(
        result.duplicate
          ? "Already imported. No duplicate records created."
          : "Synthetic dataset imported.",
      );
    } else setPreview(result);
  }
  return (
    <div className="demo-workspace" aria-busy={busy}>
      <p className="demo-label">
        SIMULATION ONLY · Fictional records · No real transactions
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <p role="status" aria-live="polite">
        {busy ? "Working…" : notice}
      </p>
      <section className="card">
        <h2>1. Import a dataset</h2>
        <p>
          Use the sample in <code>datasets/product-launch-v1</code>. Preview the
          full snapshot before importing. Maximum 1 MiB.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(() => upload(false));
          }}
        >
          <label htmlFor="dataset-file">Synthetic dataset file</label>
          <input
            id="dataset-file"
            type="file"
            accept=".json,.csv"
            required
            disabled={busy}
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setPreview(null);
            }}
          />
          <label htmlFor="dataset-format">File format</label>
          <select
            id="dataset-format"
            value={format}
            disabled={busy}
            onChange={(e) => {
              setFormat(e.target.value);
              setPreview(null);
            }}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
          <button disabled={busy || !file}>Preview import</button>
        </form>
        {preview && (
          <div>
            <h3>{preview.dataset_id}</h3>
            <ul>
              {Object.entries(preview.counts).map(([key, n]) => (
                <li key={key}>
                  {key}: {n}
                </li>
              ))}
            </ul>
            <p>
              {preview.conflict
                ? "Dataset ID conflicts with existing content. Choose a new ID."
                : preview.duplicate
                  ? "Identical dataset already exists."
                  : "Ready to import."}
            </p>
            <details>
              <summary>Inspect all synthetic records</summary>
              <pre>{JSON.stringify(preview.preview, null, 2)}</pre>
            </details>
            <button
              disabled={busy || preview.conflict}
              onClick={() => void run(() => upload(true))}
            >
              Confirm synthetic import
            </button>
          </div>
        )}
      </section>
      {dashboard.imports.length === 0 && (
        <p>No active demo dataset. Import a sample to begin.</p>
      )}
      {dashboard.imports.map((item) => (
        <section className="card" key={item.import_id}>
          <h2>{item.data.company.name}</h2>
          <p>Dataset: {item.data.dataset_id}</p>
          <h3>2. Request a launch</h3>
          <p>
            Marketing proposes a budget; Finance checks cash, Operations checks
            stock and HR supplies existing staff capacity. Reviews use
            deterministic simulation rules.
          </p>
          {item.data.campaigns.map((c) => (
            <form
              key={c.id}
              onSubmit={(e) => {
                e.preventDefault();
                const form = new FormData(e.currentTarget);
                void run(async () => {
                  await checked(
                    demoCommand(businessId, item.import_id, "launch", {
                      campaign_id: c.id,
                      budget_minor: Number(form.get("budget")),
                    }),
                  );
                  setNotice(
                    "Proposal reviewed. Inspect the forecast before deciding.",
                  );
                });
              }}
            >
              <label htmlFor={`budget-${item.import_id}-${c.id}`}>
                {c.name} budget (USD cents)
              </label>
              <input
                id={`budget-${item.import_id}-${c.id}`}
                name="budget"
                type="number"
                min="0"
                max="1000000000000"
                step="1"
                required
                defaultValue={c.budget_minor}
              />
              <button disabled={busy}>Propose simulated launch</button>
            </form>
          ))}
          <h3>3. Review and decide</h3>
          {item.tasks.length === 0 && <p>No launch proposals yet.</p>}
          {item.tasks.map((task) => (
            <article key={task.id} className="demo-task">
              <h4>Launch · {task.status.replaceAll("_", " ")}</h4>
              <p>
                Task: <code>{task.id}</code>
              </p>
              <p>
                Budget: {money(task.payload.budget_minor, item.data.currency)}
              </p>
              <p>{task.ceo_review?.reason}</p>
              {task.ceo_review?.forecast && task.status !== "executed" && (
                <Results
                  result={task.ceo_review.forecast}
                  label="Forecast — synthetic, not executed"
                />
              )}
              {task.status === "pending_approval" && (
                <>
                  <p>
                    Approval expires: {task.approval_expires_at}. Approving runs
                    only this immutable simulated proposal.
                  </p>
                  <div className="demo-actions">
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(async () => {
                          await checked(demoDecision(task.id, "approve"));
                          setNotice(
                            "Simulated launch executed. Results saved.",
                          );
                        })
                      }
                    >
                      Approve simulation
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(async () => {
                          await checked(demoDecision(task.id, "reject"));
                          setNotice("Proposal rejected.");
                        })
                      }
                    >
                      Reject
                    </button>
                  </div>
                </>
              )}
              {task.result && (
                <>
                  <Results
                    result={task.result}
                    label="Recorded synthetic results"
                  />
                  {task.result.baseline && (
                    <Results
                      result={task.result.baseline}
                      label="Fixed smaller-budget baseline"
                    />
                  )}
                  {task.result.baseline_blocker && (
                    <p>Baseline unavailable: {task.result.baseline_blocker}</p>
                  )}
                  <h4>CEO report</h4>
                  <p>{task.result.ceo_report?.summary}</p>
                </>
              )}
              <details>
                <summary>Department evidence and policy citations</summary>
                <p>
                  Dataset SHA-256: <code>{item.digest}</code>
                </p>
                <p>
                  Proposal SHA-256: <code>{task.proposal_digest}</code>
                </p>
                {Object.entries(task.ceo_review?.departments || {}).map(
                  ([role, view]) => (
                    <section key={role}>
                      <h4>{role}</h4>
                      <pre>{JSON.stringify(view.analysis, null, 2)}</pre>
                      {view.sources.length ? (
                        view.sources.map((s) => (
                          <blockquote key={s.citation.document_id}>
                            {s.text}
                            <footer>
                              {s.citation.title} · {s.citation.document_id} ·
                              version {s.citation.version}
                            </footer>
                          </blockquote>
                        ))
                      ) : (
                        <p>No matching authorized reference.</p>
                      )}
                    </section>
                  ),
                )}
              </details>
            </article>
          ))}
          <button
            disabled={busy}
            onClick={() =>
              void run(async () => {
                setReset(
                  await checked<Reset>(
                    demoCommand(businessId, item.import_id, "reset-preview"),
                  ),
                );
                setConfirmation("");
              })
            }
          >
            Preview demo reset
          </button>
          {reset?.import_id === item.import_id && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  await checked(
                    demoCommand(businessId, item.import_id, "reset", {
                      digest: reset.digest,
                      confirmation,
                    }),
                  );
                  setReset(null);
                  setNotice(
                    "Demo archived. Reimport the sample to start fresh.",
                  );
                });
              }}
            >
              <p>
                {reset.records} demo records and {reset.tasks} tasks will leave
                the active demo. {reset.effect}
              </p>
              <label htmlFor="reset-confirm">Type RESET SYNTHETIC DEMO</label>
              <input
                id="reset-confirm"
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
              />
              <button
                disabled={busy || confirmation !== "RESET SYNTHETIC DEMO"}
              >
                Confirm demo reset
              </button>
            </form>
          )}
        </section>
      ))}
      <button
        disabled={busy}
        onClick={() =>
          void run(async () => {
            setNotice("Results refreshed.");
          })
        }
      >
        Refresh results
      </button>
    </div>
  );
}
