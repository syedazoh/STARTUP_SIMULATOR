"use client";
import { useEffect, useRef, useState, useId } from "react";
import { AGENTS } from "../studio/model.mjs";
const labels = {...Object.fromEntries(AGENTS.map((agent) => [agent.id, agent.label])),hr:'HR (legacy)'};
let activeSpeech = null;
function Narration({ text }) {
  const [status, setStatus] = useState(""), own = useRef(null);
  useEffect(() => () => {
    if (own.current && own.current === activeSpeech) {
      window.speechSynthesis?.cancel();
      activeSpeech = null;
    }
  }, []);
  return <div className="recommendation-narration"><button type="button" onClick={() => {
    if (typeof window.speechSynthesis?.speak!=="function" || typeof window.SpeechSynthesisUtterance!=="function") {
      setStatus("Voice unavailable. The full recommendation remains visible.");
      return;
    }
    try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.onend = () => {
      setStatus("Narration complete.");
      if (activeSpeech === utterance) activeSpeech = null;
    };
    utterance.onerror = () => setStatus("Voice unavailable or interrupted. Read the recommendation above.");
    own.current = utterance;
    activeSpeech = utterance;
    setStatus("Reading the visible recommendation in English.");
    window.speechSynthesis.speak(utterance);
    }catch{activeSpeech=null;setStatus("Voice unavailable. The full recommendation remains visible.")}
  }}>Hear recommendation</button><button type="button" onClick={() => {
    if (own.current === activeSpeech) {
      window.speechSynthesis?.cancel();
      activeSpeech = null;
    }
    setStatus("Narration stopped.");
  }}>Stop</button><small role="status">{status}</small></div>;
}
const blank = { platform: "instagram", caption_a: "", caption_b: "", selected_caption: "a", audience: "", rationale: "", promotion_budget: 0 };
function Recommendations({ businessId, role = "ceo", boardroom = false, readRecommendations, recommendationCommand }) {
  const [items, setItems] = useState([]), [loaded, setLoaded] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState(""), [busy, setBusy] = useState(false), [draft, setDraft] = useState(blank), [editing, setEditing] = useState(null), [feedback, setFeedback] = useState({});
  const lock = useRef(false), requestId = useRef("");
  const formId=useId();
  async function refresh() {
    const result = await readRecommendations(businessId);
    if (result.ok) {
      setItems(result.data);
      setLoaded(true);
    } else setError(result.error);
  }
  useEffect(() => {
    let active = true;
    readRecommendations(businessId).then((result) => {
      if (!active) return;
      if (result.ok) {
        setItems(result.data);
        setLoaded(true);
      } else setError(result.error);
    }).catch(()=>{if(active)setError("Recommendations could not load. Check the connection and retry.")});
    return () => {
      active = false;
    };
  }, [businessId, readRecommendations]);
  async function act(command, payload, id = "") {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await recommendationCommand(businessId, command, payload, id);
      if (!result.ok) setError(result.error);
      else {
        setNotice(command === "decision" ? "CEO plan review saved. Assigned tasks still follow the existing owner execution approval." : command === "revise" ? "Revision saved. It needs a fresh review." : "Recommendation saved. The boardroom uses this same record.");
        requestId.current = "";
        setEditing(null);
        setDraft(blank);
        await refresh();
      }
    } catch {
      setError("Connection interrupted. Refresh saved recommendations before retrying.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const shown = (boardroom ? items : items.filter((item) => item.proposed_by === role)).slice(0, boardroom ? 50 : 5);
  return <section className="recommendations" id="recommendations" aria-label="Saved recommendations"><header><h2>{boardroom ? "Recommendations on the table" : `${labels[role]} recommendations`}</h2><button type="button" className="secondary" disabled={busy} onClick={() => void refresh()}>Refresh recommendations</button></header><p>Business-scoped, saved planning advice. Source snapshots and owner-recorded reviews are shown explicitly. Nothing here publishes a post or spends money.</p>{error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}{!boardroom && <form className="recommendation-form" onSubmit={(e) => {
    e.preventDefault();
    if (editing) {
      void act("revise", { expected_revision: editing.revision, draft }, editing.id);
      return;
    }
    if (!requestId.current) requestId.current = crypto.randomUUID();
    void act("create", { ...draft, agent: role, request_id: requestId.current });
  }}>{role === "marketing" && <><h3>{editing ? "Revise this saved draft" : "Prepare a reviewable social draft"}</h3><p>Leave caption fields empty for clearly labelled starter templates based only on company name and industry.</p><div className="draft-comparison">{["a", "b"].map((option) => <div key={option}><label htmlFor={`${formId}-caption-${option}`}>Caption {option.toUpperCase()}</label><textarea id={`${formId}-caption-${option}`} maxLength={2200} rows={3} value={draft[`caption_${option}`]} onChange={(e) => setDraft({ ...draft, [`caption_${option}`]: e.target.value })} /></div>)}</div><div className="form-grid"><div><label htmlFor={`${formId}-platform`}>Platform</label><select id={`${formId}-platform`} value={draft.platform} onChange={(e) => setDraft({ ...draft, platform: e.target.value })}><option value="instagram">Instagram draft</option><option value="facebook">Facebook draft</option></select></div><div><label htmlFor={`${formId}-selection`}>Use caption</label><select id={`${formId}-selection`} value={draft.selected_caption} onChange={(e) => setDraft({ ...draft, selected_caption: e.target.value })}><option value="a">Caption A</option><option value="b">Caption B</option></select></div><label>Audience<input maxLength={500} value={draft.audience} onChange={(e) => setDraft({ ...draft, audience: e.target.value })} /></label><label>Proposed promotion budget (simulated units, advisory only)<input type="number" min="0" max="1000000000" step="0.01" value={draft.promotion_budget} onChange={(e) => setDraft({ ...draft, promotion_budget: Number(e.target.value) })} /></label></div><label>Rationale<textarea maxLength={2e3} rows={2} value={draft.rationale} onChange={(e) => setDraft({ ...draft, rationale: e.target.value })} /></label></>}<button disabled={busy}>{busy ? "Working\u2026" : editing ? "Save draft revision" : role === "marketing" ? "Save Marketing recommendation" : "Save grounded recommendation"}</button>{editing && <button type="button" disabled={busy} onClick={() => {
    setEditing(null);
    setDraft(blank);
  }}>Cancel edit</button>}</form>}{!loaded && !error && <p>Loading saved recommendations…</p>}{loaded && !shown.length && <p>No saved recommendations for this view. Save one in an agent workspace.</p>}{shown.map((item) => {
    const r = item.recommendation;
    const speech = [r.what, r.why_now, r.decision_needed].join(" ");
    return <article className="saved-recommendation" key={item.plan_id} data-recommendation={item.plan_id}><header><h3>{r.what}</h3><span>{item.status.replaceAll("_", " ")} · revision {item.revision}</span></header><p><strong>Why now:</strong> {r.why_now}</p><p><strong>Decision needed:</strong> {r.decision_needed}</p><small>Proposed by {item.proposed_by.toUpperCase()} · {new Date(item.evidence.as_of).toLocaleString()} · latest {item.evidence.loaded_tasks} tasks, maximum 200.</small>{r.caption_a && <><div className="draft-comparison"><div><h4>Caption A{r.selected_caption === "a" ? " \xB7 selected" : ""}</h4><p>{r.caption_a}</p></div><div><h4>Caption B{r.selected_caption === "b" ? " \xB7 selected" : ""}</h4><p>{r.caption_b}</p></div></div><p><strong>Audience:</strong> {r.audience}</p><p><strong>Rationale:</strong> {r.rationale}</p><dl className="recommendation-finance"><div><dt>Available simulated funds at review</dt><dd>{item.evidence.available_simulated_units.toLocaleString()}</dd></div><div><dt>Proposed promotion, not authorized spending</dt><dd>{r.promotion_budget?.toLocaleString()}</dd></div></dl></>}{item.proposed_by === "operations" && <dl className="recommendation-workload">{Object.entries(item.evidence.workload).map(([agent, count]) => <div key={agent}><dt>{agent}</dt><dd>{count} recorded tasks</dd></div>)}</dl>}<details><summary>Contributions & evidence</summary>{item.contributions.map((c, i) => <p key={i}><strong>{c.agent} · {c.basis}:</strong> {c.text}</p>)}</details><Narration text={speech} />{item.feedback.map((f, i) => <p key={i}><strong>{f.decision.replaceAll("_", " ")} · revision {f.revision}:</strong> {f.text}</p>)}{item.ceo_decision && <p><strong>CEO plan review, recorded by owner:</strong> {item.ceo_decision.decision} — {item.ceo_decision.reason}</p>}{item.task_ids.length > 0 && <p><strong>Assigned simulation tasks:</strong> {item.task_ids.map((id) => <a key={id} href={`/workspace/${encodeURIComponent(businessId)}/agents/marketing#tasks`}>{id} </a>)}</p>}{!boardroom && <a href={`/workspace/${encodeURIComponent(businessId)}/boardroom#recommendations`}>Review this saved recommendation in the boardroom →</a>}{!boardroom && item.proposed_by === "marketing" && ["draft", "needs_revision"].includes(item.status) && <button type="button" className="secondary" disabled={busy} onClick={() => {
      setEditing({ id: item.plan_id, revision: item.revision });
      setDraft({ platform: r.platform || "instagram", caption_a: r.caption_a || "", caption_b: r.caption_b || "", selected_caption: r.selected_caption || "a", audience: r.audience || "", rationale: r.rationale || "", promotion_budget: r.promotion_budget || 0 });
      document.querySelector(".recommendation-form")?.scrollIntoView({ block: "center" });
    }}>Edit draft for a fresh review</button>}{boardroom && item.status === "needs_revision" && <a href={`/workspace/${encodeURIComponent(businessId)}/agents/marketing#recommendations`}>Open Marketing to revise this saved draft →</a>}{(boardroom || role === "ceo") && item.status === "draft" && <div className="recommendation-review"><label>CEO review feedback or reason<textarea value={feedback[item.plan_id] || ""} maxLength={2e3} rows={2} onChange={(e) => setFeedback({ ...feedback, [item.plan_id]: e.target.value })} /></label><p>You are recording an owner-authorized CEO plan decision. This is separate from final approval to execute the assigned simulation task.</p>{["approve", "request_changes", "reject"].map((decision) => <button key={decision} type="button" disabled={busy || decision !== "approve" && !feedback[item.plan_id]?.trim()} onClick={() => void act("decision", { decision, expected_revision: item.revision, feedback: feedback[item.plan_id] || "" }, item.plan_id)}>{decision === "approve" ? "Authorize CEO plan & assign" : decision === "request_changes" ? "Request revision" : "Reject recommendation"}</button>)}</div>}</article>;
  })}</section>;
}
export {
  Recommendations as default
};
