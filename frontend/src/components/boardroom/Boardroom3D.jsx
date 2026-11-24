import "../../studio/collaboration.css";
import {useAppearance} from "../../appearance/Appearance";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import {
  AGENTS,
  observedChanges,
  previewTransfers,
  collaborationRoles,
} from "../../studio/model.mjs";
import { createStudio } from "../../studio/scene.mjs";
import { observedMessages, decisionEvents } from "./eventRoutes";
import "./boardroom.css";

export const EXECUTIVES = AGENTS;
export default function Boardroom3D({
  focusAgent = null,
  decisions = [],
  decisionsReady = false,
  statuses = {},
  events = [],
  tasks = [],
  ready = true,
  eventsReady = ready,
  onSelect = () => {},
  selected = "ceo",
  showApprovalLabel = false,
}) {
  const {theme,preferences}=useAppearance();
  const canvas = useRef(null),
    labels = useRef(null),
    engine = useRef(null);
  const select = useRef(onSelect);
  select.current = onSelect;
  const [mode, setMode] = useState("3d"),
    [error, setError] = useState(""),
    [preview, setPreview] = useState(false);
  const [handoff, setHandoff] = useState(null),
    [stage, setStage] = useState("");
  const queue = useRef([]),
    previewing = useRef(false);
  previewing.current = preview;
  const seenDecisions = useRef(null);
  const previous = useRef(null),
    seen = useRef(null);
  useEffect(() => {
    if (mode !== "3d") return;
    try {
      const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
      engine.current = createStudio(THREE, canvas.current, {
        reducedMotion: motion.matches,
        onSelect: (id) => select.current(id),
        onTransfer: (value) => setStage(value.stage),
        onProject: (positions) => {
          for (const [id, [x, y]] of Object.entries(positions)) {
            const node = labels.current?.querySelector(`[data-agent="${id}"]`);
            if (node)
              node.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
          }
        },
      });
      setError("");
    } catch {
      setError(
        "3D is unavailable. Use the team list to inspect your executives.",
      );
    }
    return () => {
      engine.current?.dispose();
      engine.current = null;
    };
  }, [mode]);
  useEffect(()=>{engine.current?.setTheme(theme)},[theme,mode]);
  useEffect(()=>{const reduced=matchMedia('(prefers-reduced-motion: reduce)');const update=()=>engine.current?.setReducedMotion(reduced.matches||!preferences.motion);update();reduced.addEventListener('change',update);return()=>reduced.removeEventListener('change',update)},[preferences.motion,mode]);
  useEffect(() => {
    engine.current?.select(selected);
  }, [selected, mode]);
  useEffect(() => { engine.current?.showOnly(focusAgent) }, [focusAgent, mode]);
  useEffect(() => {
    if (!decisionsReady) return;
    const rows = decisionEvents(decisions);
    queue.current.push(...observedMessages(seenDecisions.current, rows));
    queue.current = queue.current.slice(-32);
    seenDecisions.current = new Set(rows.map(e => e.event_id));
  }, [decisions, decisionsReady]);
  useEffect(() => {
    if (!ready) return;
    const changes = observedChanges(previous.current, tasks);
    previous.current = new Map(tasks.map((t) => [t.id, t]));
    // CEO assignments are now emitted as durable directed backend events.
    // Do not animate the same assignment again from its task snapshot.
    queue.current.push(...changes.filter((change) => change.label !== "Task assigned"));
    queue.current = queue.current.slice(-32);
  }, [tasks, ready, preview]);
  useEffect(() => {
    if (!eventsReady) return;
    queue.current.push(...observedMessages(seen.current, events));
    queue.current = queue.current.slice(-32);
    seen.current = new Set(events.map((event) => event.event_id));
  }, [events, eventsReady]);
  useEffect(() => {
    const timer = setInterval(() => {
      if (!document.hidden && !previewing.current && queue.current.length)
        setHandoff(queue.current.shift());
    }, 4200);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!preview) return;
    const rows = previewTransfers();
    let index = 0;
    setHandoff(rows[0]);
    const timer = setInterval(() => {
      if (document.hidden) return;
      index = (index + 1) % rows.length;
      setHandoff(rows[index]);
    }, 4200);
    return () => clearInterval(timer);
  }, [preview]);
  useEffect(() => {
    engine.current?.playTransfer(handoff);
  }, [handoff, mode]);
  return (
    <section className="boardroom-shell" aria-label="AI executive boardroom">
      <div className="boardroom-toolbar">
        <div>
          <strong>Executive floor</strong>
          <span>
            {preview
              ? "Visual preview · synthetic · no tasks created"
              : "Select an avatar. Inspect real work. Keep approval in your hands."}
          </span>
        </div>
        <div className="boardroom-controls">
          <button
            onClick={() => {
              setPreview(!preview);
              if (preview) setHandoff(null);
            }}
          >
            {preview ? "Exit preview" : "Preview handoff"}
          </button>
          <button onClick={() => setMode(mode === "3d" ? "list" : "3d")}>
            {mode === "3d" ? "Team list" : "3D view"}
          </button>
        </div>
      </div>
      {handoff && (
        <div className="boardroom-transfer" role="status">
          <strong>
            {handoff.sender.toUpperCase()} <span aria-hidden="true">→</span>{" "}
            {handoff.receiver.toUpperCase()}
          </strong>
          <span>{handoff.title || handoff.label}</span>
          <small>
            {handoff.source === "visual preview" ? "Synthetic preview · " : ""}
            {stage === "arrived"
              ? "Task visual arrived"
              : "Sending task"} · {handoff.label}
          </small>
        </div>
      )}
      {mode === "3d" ? (
        <div className="boardroom-canvas">
          <canvas
            ref={canvas}
            aria-label="3D executive avatars; drag to orbit or use the labelled selection buttons"
          />
          {error ? (
            <p role="alert" className="boardroom-render-error">
              {error}
              <button onClick={() => setMode("list")}>Open team list</button>
            </p>
          ) : (
            <div className="boardroom-projected-labels" ref={labels}>
              {AGENTS.map((a) => (
                <button
                  hidden={!!focusAgent && focusAgent !== a.id}
                data-agent={a.id}
                  data-direction={
                    handoff?.sender === a.id
                      ? "sending"
                      : handoff?.receiver === a.id
                        ? "receiving"
                        : "idle"
                  }
                  key={a.id}
                  aria-label={`Select ${a.label}`}
                  aria-pressed={selected === a.id}
                  onClick={() => onSelect(a.id)}
                >
                  {a.label}
                </button>
              ))}
              {showApprovalLabel && (
                <span data-agent="owner">You · Approval desk</span>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="boardroom-list">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              onClick={() => onSelect(a.id)}
              aria-pressed={selected === a.id}
            >
              <span style={{ background: a.color }} />
              {a.label}
              <small>
                {statuses[a.id] ? "State available" : "No snapshot"}
              </small>
            </button>
          ))}
        </div>
      )}
      <div
        className="collaboration-strip"
        aria-label="Task transfer participants"
      >
        {collaborationRoles(handoff, stage).map((a) => (
          <button
            key={a.id}
            type="button"
            data-direction={a.direction}
            onClick={() => onSelect(a.id)}
            aria-pressed={selected === a.id}
          >
            <strong>{a.label}</strong>
            <span>{a.activity}</span>
          </button>
        ))}
      </div>
      <p className="boardroom-note" role="status">
        {handoff
          ? `${handoff.source === "visual preview" ? "Visual preview: " : ""}${handoff.sender.toUpperCase()} → ${handoff.receiver.toUpperCase()} · ${handoff.label}`
          : "No new handoff. Historical tasks are not replayed as live activity."}
      </p>
    </section>
  );
}
