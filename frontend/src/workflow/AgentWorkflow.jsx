"use client";
import { useEffect, useId, useRef, useState } from "react";
import useAgentVoice from "./useAgentVoice";

export const WORKFLOW_ROLES = [
  "ceo",
  "finance",
  "marketing",
  "operations",
  "strategy",
];
const names = {
  ceo: "CEO",
  finance: "Finance",
  marketing: "Marketing",
  operations: "Operations",
  strategy: "Strategy",
  hr: "HR (legacy)",
};
const sourceName = {
  model: "Model response",
  structured_records: "Structured records / definition",
  structured_fallback: "Record-based fallback · model unavailable",
  owner_draft: "Owner-edited draft",
};
const empty = {
  conversation: { turns: [], artifacts: [] },
  launch: { plans: [], tasks: [], submissions: [] },
  images: [],
};
export default function AgentWorkflow({
  businessId,
  role = "ceo",
  boardroom = false,
  read,
  command,
  readImage,
  workspaceBase = "",
}) {
  const [data, setData] = useState(empty),
    [text, setText] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [reference, setReference] = useState(""),
    [assignment, setAssignment] = useState(""),
    [speakReplies, setSpeakReplies] = useState(true),
    [edit, setEdit] = useState(null),
    [goal, setGoal] = useState(""),
    [due, setDue] = useState(""),
    [feedback, setFeedback] = useState({}),
    [imageBrief, setImageBrief] = useState(""),
    [previews, setPreviews] = useState({}),
    [imageSelection, setImageSelection] = useState([]);
  const id = useId(),
    live = useRef(false),
    sequence = useRef(0),
    lock = useRef(false),
    keys = useRef({}),
    urls = useRef({});
  const voice = useAgentVoice(
    setText,
    role === "finance" || role === "operations" ? "en-GB" : "en-US",
  );
  async function refresh() {
    const seq = ++sequence.current;
    try {
      const result = await read(businessId, role);
      if (live.current && seq === sequence.current) {
        if (!result.ok) setError(result.error);
        else setData(result.data);
      }
    } catch {
      if (live.current)
        setError("Could not load saved work. Check the backend and refresh.");
    }
  }
  useEffect(() => {
    live.current = true;
    void refresh();
    const timer = setInterval(() => {
      if (document.visibilityState === "visible" && !lock.current)
        void refresh();
    }, 5000);
    return () => {
      live.current = false;
      sequence.current++;
      clearInterval(timer);
      for (const url of Object.values(urls.current)) URL.revokeObjectURL(url);
    };
  }, [businessId, role, read]);
  async function act(action, payload = {}, target = "") {
    if (lock.current) return null;
    lock.current = true;
    voice.stop();
    setBusy(true);
    setError("");
    setNotice("");
    const requestActions = ["turn", "draft", "plan", "image"];
    let body = payload;
    if (requestActions.includes(action)) {
      const fingerprint = JSON.stringify(payload),
        old = keys.current[action];
      const key =
        old?.fingerprint === fingerprint ? old.key : crypto.randomUUID();
      keys.current[action] = { fingerprint, key };
      body = { ...payload, request_id: key };
    }
    try {
      const result = await command(businessId, role, action, body, target);
      if (!live.current) return null;
      if (!result.ok) {
        setError(result.error);
        return null;
      }
      delete keys.current[action];
      setNotice("Saved. Your existing approval rules still apply.");
      await refresh();
      return result.data;
    } catch {
      if (live.current)
        setError(
          "The request could not finish. Refresh saved work before retrying; the same request key will be reused.",
        );
      return null;
    } finally {
      lock.current = false;
      if (live.current) setBusy(false);
    }
  }
  const artifacts = data.conversation.artifacts || [],
    turns = data.conversation.turns || [],
    tasks = (data.launch.tasks || []).filter(
      (task) => boardroom || role === "ceo" || task.agent === role,
    ),
    ownTasks = tasks.filter((task) => task.agent === role);
  async function submitText(event) {
    event.preventDefault();
    voice.stop();
    const pending = act("turn", {
      content: text,
      reference_id: reference || null,
      task_id: assignment || null,
    });
    const version = voice.version();
    const result = await pending;
    // A new edit, reference, Stop, or microphone action means the owner moved on.
    // Keep that newer input and suppress playback from this older request.
    if (result && live.current && voice.version() === version) {
      setText("");
      if (result.artifact_id) setReference(result.artifact_id);
      if (speakReplies) voice.speak(result.reply.spoken_response);
    }
  }
  async function preview(artifactId, download = false, artifactRole = role) {
    try {
      let url = urls.current[artifactId];
      if (!url) {
        const blob = await readImage(businessId, artifactRole, artifactId);
        if (!live.current) return;
        url = URL.createObjectURL(blob);
        urls.current[artifactId] = url;
        setPreviews((old) => ({ ...old, [artifactId]: url }));
      }
      if (download) {
        const a = document.createElement("a");
        a.href = url;
        a.download = `draft-${artifactId}.png`;
        a.click();
      }
    } catch {
      if (live.current)
        setError(
          "Could not load this authorized image. Check your connection and retry.",
        );
    }
  }
  function editDraft(artifact) {
    voice.stop();
    setReference(artifact.artifact_id);
    setAssignment(artifact.task_id || "");
    setEdit({ ...artifact.recommendation });
    setNotice("Edit the visible draft. Saving a revision does not approve it.");
  }
  return (
    <section
      className="agent-workflow"
      aria-label={`${names[role]} shared workflow`}
      data-speaking={voice.phase === "speaking"}
      aria-busy={busy}
    >
      <header className="workflow-heading">
        <div>
          <h2>
            {boardroom
              ? "Discuss, compare, decide."
              : `Work with ${names[role]}.`}
          </h2>
          <p>
            Saved business context. Reviewable recommendations. Your decision.
          </p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={busy}>
          Refresh saved work
        </button>
      </header>
      <nav className="workflow-role-nav" aria-label="Five agent workspaces">
        {WORKFLOW_ROLES.map((agent) => (
          <a
            key={agent}
            aria-current={agent === role ? "page" : undefined}
            href={`${workspaceBase || `/workspace/${encodeURIComponent(businessId)}/agents`}/${agent}`}
          >
            {names[agent]}
          </a>
        ))}
      </nav>
      {error && (
        <p role="alert" className="workflow-alert">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <div className="workflow-layout">
        <div className="workflow-dialogue">
          <div
            className="workflow-conversation"
            aria-label="Saved shared conversation"
          >
            {!turns.length && (
              <p>
                Ask about your selected business, compare options, or describe
                the launch you want to plan. Missing evidence stays unknown.
              </p>
            )}
            {turns.map((turn) => (
              <article key={turn.turn_id}>
                <p className="workflow-owner">
                  <strong>You</strong> {turn.request}
                </p>
                <div>
                  <strong>{names[role]}</strong>
                  <p>{turn.reply.spoken_response}</p>
                  <small>{sourceName[turn.source] || turn.source}</small>
                  <button
                    type="button"
                    onClick={() => voice.speak(turn.reply.spoken_response)}
                  >
                    Hear response
                  </button>
                </div>
              </article>
            ))}
          </div>
          <form onSubmit={submitText} className="workflow-composer">
            <label htmlFor={id + "message"}>Message {names[role]}</label>
            <textarea
              id={id + "message"}
              maxLength={4000}
              rows={4}
              value={text}
              onChange={(event) => {
                voice.stop();
                setText(event.target.value);
              }}
              required
              placeholder="Ask, clarify, or describe a recommendation…"
            />
            <div className="workflow-context-fields">
              <label>
                Assignment
                <select
                  value={assignment}
                  onChange={(event) => {
                    voice.stop();
                    setAssignment(event.target.value);
                  }}
                >
                  <option value="">General conversation</option>
                  {ownTasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.objective}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Follow-up reference
                <select
                  value={reference}
                  onChange={(event) => {
                    voice.stop();
                    setReference(event.target.value);
                  }}
                >
                  <option value="">No explicit reference</option>
                  {artifacts.map((artifact, index) => (
                    <option
                      key={artifact.artifact_id}
                      value={artifact.artifact_id}
                    >
                      {artifact.kind === "image"
                        ? "Image"
                        : artifact.recommendation?.what?.slice(0, 65) ||
                          "Draft"}{" "}
                      · {index + 1}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="workflow-actions">
              <button
                disabled={busy || !text.trim() || voice.phase === "listening"}
              >
                {busy ? "Saving…" : "Send message"}
              </button>
              {voice.phase === "listening" ? (
                <button type="button" onClick={voice.finish}>
                  Finish dictation
                </button>
              ) : (
                <button type="button" onClick={() => voice.dictate(text)}>
                  Use microphone
                </button>
              )}
              <button type="button" onClick={voice.stop}>
                Stop audio
              </button>
              <label className="workflow-check">
                <input
                  type="checkbox"
                  checked={speakReplies}
                  onChange={(event) => {
                    setSpeakReplies(event.target.checked);
                    voice.stop();
                  }}
                />
                Speak replies
              </label>
            </div>
            <p className="workflow-voice-state" role="status">
              {voice.notice ||
                (!voice.microphone
                  ? "Voice input may be unavailable; typed input always works."
                  : "Dictation uses your browser’s speech service. Review the transcript before Send.")}
            </p>
          </form>
          {edit && (
            <form
              className="workflow-editor"
              onSubmit={async (event) => {
                event.preventDefault();
                const result = await act("draft", {
                  content: "Owner-edited recommendation revision.",
                  reference_id: reference || null,
                  task_id: assignment || null,
                  recommendation: edit,
                });
                if (result) {
                  setEdit(null);
                  setReference(result.artifact_id);
                }
              }}
            >
              <h3>Edit a reviewable draft</h3>
              {[
                ["what", "Recommendation", 600],
                ["why_now", "Why now", 1200],
                ["decision_needed", "Decision needed", 600],
              ].map(([field, label, max]) => (
                <label key={field}>
                  {label}
                  <textarea
                    value={edit[field]}
                    maxLength={max}
                    onChange={(event) =>
                      setEdit({ ...edit, [field]: event.target.value })
                    }
                    required
                  />
                </label>
              ))}
              <div className="workflow-actions">
                <button disabled={busy}>Save draft revision</button>
                <button type="button" onClick={() => setEdit(null)}>
                  Cancel edit
                </button>
              </div>
            </form>
          )}
          <section className="workflow-artifacts">
            <h3>Recommendations & artifacts</h3>
            {!artifacts.length && (
              <p>No saved drafts in this conversation yet.</p>
            )}
            {artifacts.map((artifact, index) => (
              <article
                key={artifact.artifact_id}
                data-artifact={artifact.artifact_id}
              >
                <header>
                  <strong>
                    {artifact.kind === "image"
                      ? "Draft visual"
                      : artifact.recommendation?.what}
                  </strong>
                  <small>
                    {sourceName[artifact.source] || artifact.source} · saved{" "}
                    {new Date(artifact.created_at).toLocaleString()}
                  </small>
                </header>
                {artifact.kind === "recommendation" ? (
                  <>
                    <p>
                      <strong>Why now:</strong>{" "}
                      {artifact.recommendation.why_now}
                    </p>
                    <p>
                      <strong>Decision needed:</strong>{" "}
                      {artifact.recommendation.decision_needed}
                    </p>
                    {artifact.recommendation.options?.length > 0 && (
                      <div className="workflow-options">
                        {artifact.recommendation.options.map((option, i) => (
                          <div key={i}>
                            <h4>{option.title}</h4>
                            <p>{option.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {artifact.recommendation.proposed_steps?.length > 0 && (
                      <ol>
                        {artifact.recommendation.proposed_steps.map(
                          (step, i) => (
                            <li key={i}>{step}</li>
                          ),
                        )}
                      </ol>
                    )}
                    {artifact.recommendation.assumptions?.map(
                      (assumption, i) => (
                        <p key={i}>
                          <strong>Assumption:</strong> {assumption}
                        </p>
                      ),
                    )}
                    <details>
                      <summary>Supporting evidence</summary>
                      {artifact.evidence?.map((fact) => (
                        <div key={fact.id}>
                          <strong>{fact.label}</strong>
                          <p>{fact.basis}</p>
                          <pre>
                            {JSON.stringify(
                              fact.value ?? {
                                amount_minor: fact.value_minor,
                                currency: fact.currency,
                              },
                              null,
                              2,
                            )}
                          </pre>
                          <small>Source: {fact.id}</small>
                        </div>
                      ))}
                    </details>
                    <div className="workflow-actions">
                      <button
                        type="button"
                        onClick={() => {
                          voice.stop();
                          setReference(artifact.artifact_id);
                          setAssignment(artifact.task_id || "");
                          setText("Revise that: ");
                        }}
                      >
                        Follow up on this draft
                      </button>
                      <button type="button" onClick={() => editDraft(artifact)}>
                        Edit draft
                      </button>
                      {artifact.recommendation.image_brief && (
                        <button
                          type="button"
                          onClick={() => {
                            setReference(
                              artifact.parent_artifact_id ||
                                artifact.artifact_id,
                            );
                            setAssignment(artifact.task_id || "");
                            setImageBrief(artifact.recommendation.image_brief);
                          }}
                        >
                          Use image brief
                        </button>
                      )}
                      {artifact.task_id && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => {
                            const task = tasks.find(
                              (t) => t.id === artifact.task_id,
                            );
                            if (task)
                              void act(
                                "submit",
                                {
                                  artifact_id: artifact.artifact_id,
                                  image_artifact_ids: imageSelection.filter(
                                    (id) =>
                                      artifacts.some(
                                        (a) =>
                                          a.artifact_id === id &&
                                          a.task_id === artifact.task_id,
                                      ),
                                  ),
                                  expected_fingerprint:
                                    task.approval_fingerprint,
                                },
                                task.id,
                              );
                          }}
                        >
                          Submit this version to CEO
                        </button>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <p>{artifact.brief}</p>
                    {previews[artifact.artifact_id] && (
                      <img
                        src={previews[artifact.artifact_id]}
                        alt={`${names[role]} draft illustration: ${artifact.brief.slice(0, 150)}`}
                      />
                    )}
                    <div className="workflow-actions">
                      <button
                        type="button"
                        onClick={() => void preview(artifact.artifact_id)}
                      >
                        Preview image
                      </button>
                      <button
                        type="button"
                        onClick={() => void preview(artifact.artifact_id, true)}
                      >
                        Download image
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          voice.stop();
                          setReference(artifact.artifact_id);
                          setAssignment(artifact.task_id || "");
                          setImageBrief("Revise this image: ");
                        }}
                      >
                        Revise image
                      </button>
                      {artifact.task_id && (
                        <label className="workflow-check">
                          <input
                            type="checkbox"
                            checked={imageSelection.includes(
                              artifact.artifact_id,
                            )}
                            onChange={(event) =>
                              setImageSelection((old) =>
                                event.target.checked
                                  ? [...old, artifact.artifact_id]
                                  : old.filter(
                                      (id) => id !== artifact.artifact_id,
                                    ),
                              )
                            }
                          />
                          Include in next submission
                        </label>
                      )}
                    </div>
                  </>
                )}
                {artifact.parent_artifact_id && (
                  <small>
                    Prior version retained · reference{" "}
                    {artifact.parent_artifact_id.slice(0, 12)}
                  </small>
                )}
                <span className="workflow-record-index">
                  Saved version {artifacts.length - index}
                </span>
              </article>
            ))}
          </section>
        </div>
        <aside className="workflow-workbench">
          <section>
            <h3>Draft a visual</h3>
            <p>
              Illustrations only. Data charts come from saved records. No social
              account or publishing.
            </p>
            <form
              onSubmit={async (event) => {
                event.preventDefault();
                const result = await act("image", {
                  brief: imageBrief,
                  parent_artifact_id: reference || null,
                  task_id: assignment || null,
                });
                if (result) setImageBrief("");
              }}
            >
              <label htmlFor={id + "image"}>
                Image brief for {names[role]}
              </label>
              <textarea
                id={id + "image"}
                minLength={5}
                maxLength={3000}
                value={imageBrief}
                onChange={(event) => {
                  voice.stop();
                  setImageBrief(event.target.value);
                }}
                required
                rows={4}
              />
              <button disabled={busy || imageBrief.trim().length < 5}>
                Generate draft visual
              </button>
            </form>
            {data.images.map((job) => (
              <div className="workflow-job" key={job.job_id}>
                <strong>{job.status.replaceAll("_", " ")}</strong>
                <p>{job.payload.brief}</p>
                {job.error && <p role="alert">{job.error}</p>}
                {job.status === "failed" && (
                  <button
                    disabled={busy}
                    type="button"
                    onClick={() => void act("retry", {}, job.job_id)}
                  >
                    Retry same image job
                  </button>
                )}
                {job.status === "reconciliation_required" && (
                  <p>
                    Outcome uncertain. Inspect the provider outcome before
                    generating again.
                  </p>
                )}
              </div>
            ))}
          </section>
          {(boardroom || role === "ceo") && (
            <section>
              <h3>Coordinate a launch</h3>
              <p>
                Draft first. Assigning work and approving submissions are
                separate owner decisions.
              </p>
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  await act("plan", {
                    goal,
                    due_at: new Date(due).toISOString(),
                  });
                }}
              >
                <label>
                  Launch goal
                  <textarea
                    value={goal}
                    onChange={(event) => setGoal(event.target.value)}
                    minLength={5}
                    maxLength={2000}
                    required
                  />
                </label>
                <label>
                  Proposed deadline
                  <input
                    type="datetime-local"
                    value={due}
                    onChange={(event) => setDue(event.target.value)}
                    required
                  />
                </label>
                <button disabled={busy}>Save launch plan</button>
              </form>
              {data.launch.plans.map((plan) => (
                <details key={plan.plan_id}>
                  <summary>
                    {plan.goal} · {plan.status}
                  </summary>
                  <ul>
                    {plan.assignments.map((item) => (
                      <li key={item.department}>
                        {names[item.department]}: {item.objective} ·{" "}
                        {item.payload.due_at}
                      </li>
                    ))}
                  </ul>
                  {["draft", "assignment_failed"].includes(plan.status) && (
                    <button
                      disabled={busy}
                      type="button"
                      onClick={() =>
                        void act(
                          "activate",
                          { expected_revision: plan.revision },
                          plan.plan_id,
                        )
                      }
                    >
                      Authorize & assign four follow-ups
                    </button>
                  )}
                </details>
              ))}
            </section>
          )}
          <section className="workflow-assignment-list">
            <h3>
              {boardroom || role === "ceo"
                ? "Launch submissions"
                : "Your launch assignments"}
            </h3>
            {!tasks.length && <p>No shared launch assignments yet.</p>}
            {tasks.map((task) => (
              <article key={task.id} data-workflow-task={task.id}>
                <header>
                  <strong>{names[task.agent]}</strong>
                  <span>{task.status.replaceAll("_", " ")}</span>
                </header>
                <p>{task.objective}</p>
                <small>Saved deadline: {task.payload.due_at}</small>
                {task.owner_feedback && (
                  <p className="workflow-feedback">
                    Requested changes: {task.owner_feedback}
                  </p>
                )}
                {task.agent === role && (
                  <button
                    type="button"
                    onClick={() => {
                      voice.stop();
                      setAssignment(task.id);
                      setReference("");
                      setText(
                        task.owner_feedback
                          ? `Revise my submission: ${task.owner_feedback}`
                          : task.objective,
                      );
                    }}
                  >
                    Discuss this assignment
                  </button>
                )}
                {task.payload.submission_id ? (
                  <details>
                    <summary>Review exact saved submission</summary>
                    {data.launch.submissions
                      .filter(
                        (a) => a.artifact_id === task.payload.submission_id,
                      )
                      .map((a) => (
                        <div key={a.artifact_id}>
                          <h4>{a.recommendation.what}</h4>
                          <p>{a.recommendation.why_now}</p>
                          <p>{a.recommendation.decision_needed}</p>
                        </div>
                      ))}
                    {data.launch.submissions
                      .filter(
                        (a) =>
                          a.kind === "image" &&
                          task.payload.image_artifact_ids?.includes(
                            a.artifact_id,
                          ),
                      )
                      .map((a) => (
                        <div key={a.artifact_id}>
                          {previews[a.artifact_id] && (
                            <img
                              className="workflow-review-image"
                              src={previews[a.artifact_id]}
                              alt="Exact submitted draft visual"
                            />
                          )}
                          <button
                            type="button"
                            onClick={() =>
                              void preview(a.artifact_id, false, task.agent)
                            }
                          >
                            Preview submitted image
                          </button>
                        </div>
                      ))}
                    <p>
                      Included image versions:{" "}
                      {task.payload.image_artifact_ids?.length || 0}. Approving
                      saves this internal brief and spends nothing.
                    </p>
                    <pre>{JSON.stringify(task.payload, null, 2)}</pre>
                    {(boardroom || role === "ceo") &&
                      task.status === "pending_approval" && (
                        <>
                          <label>
                            Review feedback
                            <textarea
                              maxLength={2000}
                              value={feedback[task.id] || ""}
                              onChange={(event) =>
                                setFeedback({
                                  ...feedback,
                                  [task.id]: event.target.value,
                                })
                              }
                            />
                          </label>
                          <div className="workflow-actions">
                            <button
                              disabled={busy}
                              type="button"
                              onClick={() =>
                                void act(
                                  "approve",
                                  {
                                    expected_fingerprint:
                                      task.approval_fingerprint,
                                  },
                                  task.id,
                                )
                              }
                            >
                              Approve saved submission
                            </button>
                            <button
                              disabled={busy || !feedback[task.id]?.trim()}
                              type="button"
                              onClick={() =>
                                void act(
                                  "changes",
                                  {
                                    owner_feedback: feedback[task.id],
                                    expected_fingerprint:
                                      task.approval_fingerprint,
                                  },
                                  task.id,
                                )
                              }
                            >
                              Request changes
                            </button>
                            <button
                              disabled={busy || !feedback[task.id]?.trim()}
                              type="button"
                              onClick={() =>
                                void act(
                                  "reject",
                                  {
                                    owner_feedback: feedback[task.id],
                                    expected_fingerprint:
                                      task.approval_fingerprint,
                                  },
                                  task.id,
                                )
                              }
                            >
                              Reject with reason
                            </button>
                          </div>
                        </>
                      )}
                  </details>
                ) : (
                  <p>Waiting for a saved departmental submission.</p>
                )}
                <details>
                  <summary>Prior submissions</summary>
                  {data.launch.submissions
                    .filter(
                      (a) =>
                        a.task_id === task.id && a.kind === "recommendation",
                    )
                    .map((a) => (
                      <p key={a.artifact_id}>
                        {a.recommendation.what} · {a.artifact_id.slice(0, 12)}
                      </p>
                    ))}
                </details>
              </article>
            ))}
          </section>
        </aside>
      </div>
    </section>
  );
}
