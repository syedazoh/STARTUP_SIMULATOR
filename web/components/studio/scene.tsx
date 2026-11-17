"use client";
import { useEffect, useRef, useState } from "react";
import { AGENTS } from "../../../frontend/src/studio/model.mjs";
import type { Transfer } from "./types";
import Icon from "./icon";

type Engine = {
  select: (id: string) => void;
  playTransfer: (t: Transfer | null) => void;
  setImmersive: (v: boolean) => void;
  follow: (v: boolean) => void;
  resetCamera: () => void;
  dispose: () => void;
};
export default function Scene({
  selected,
  onSelect,
  transfer,
  onRecorded,
}: {
  selected: string;
  onSelect: (id: string) => void;
  transfer: Transfer | null;
  onRecorded?: (t: Transfer) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null),
    labels = useRef<HTMLDivElement>(null),
    engine = useRef<Engine | null>(null);
  const callbacks = useRef({ onSelect, onRecorded });
  callbacks.current = { onSelect, onRecorded };
  const [error, setError] = useState(""),
    [ready, setReady] = useState(false),
    [view, setView] = useState("3d"),
    [immersive, setImmersive] = useState(false),
    [following, setFollowing] = useState(false);
  const section = useRef<HTMLElement>(null),
    expand = useRef<HTMLButtonElement>(null);
  const current = useRef({ selected, transfer });
  current.current = { selected, transfer };
  useEffect(() => {
    if (view !== "3d") return;
    let disposed = false;
    setReady(false);
    setError("");
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const mount = async () => {
      try {
        const [THREE, { createStudio }] = await Promise.all([
          import("three"),
          import("../../../frontend/src/studio/scene.mjs"),
        ]);
        if (disposed || !canvas.current) return;
        const created = createStudio(THREE, canvas.current, {
          reducedMotion: preference.matches,
          onSelect: (id: string) => callbacks.current.onSelect(id),
          onProject: (positions: Record<string, number[]>) => {
            for (const [id, [x, y]] of Object.entries(positions)) {
              const node = labels.current?.querySelector<HTMLElement>(
                `[data-agent="${id}"]`,
              );
              if (node)
                node.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
            }
          },
          onTransfer: (t: Transfer) => callbacks.current.onRecorded?.(t),
        });
        engine.current = created;
        created.select(current.current.selected);
        if (current.current.transfer)
          created.playTransfer(current.current.transfer);
        setReady(true);
      } catch {
        if (!disposed)
          setError(
            "3D is unavailable on this device. Use the team list to inspect work.",
          );
      }
    };
    void mount();
    const lost = (e: Event) => {
      e.preventDefault();
      setError(
        "The 3D connection was interrupted. Switch to the team list or reload to retry.",
      );
    };
    const node = canvas.current;
    node?.addEventListener("webglcontextlost", lost);
    return () => {
      disposed = true;
      node?.removeEventListener("webglcontextlost", lost);
      engine.current?.dispose();
      engine.current = null;
    };
  }, [view]);
  useEffect(() => {
    engine.current?.select(selected);
  }, [selected]);
  useEffect(() => {
    engine.current?.playTransfer(transfer);
  }, [transfer]);
  useEffect(() => {
    engine.current?.setImmersive(immersive);
  }, [immersive, ready]);
  useEffect(() => {
    engine.current?.follow(following);
  }, [following, ready]);
  useEffect(() => {
    if (!immersive) return;
    const prior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    section.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setImmersive(false);
        expand.current?.focus();
      }
      if (e.key === "Tab") {
        const items = Array.from(
          section.current?.querySelectorAll<HTMLButtonElement>(
            "button:not(:disabled)",
          ) || [],
        ).filter((el) => el.offsetParent !== null);
        if (!items.length) return;
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", keys);
    return () => {
      document.body.style.overflow = prior;
      document.removeEventListener("keydown", keys);
    };
  }, [immersive]);
  return (
    <section
      ref={section}
      className={`studio-scene ${immersive ? "is-immersive" : ""}`}
      role={immersive ? "dialog" : undefined}
      aria-modal={immersive || undefined}
      aria-label="Interactive 3D executive team"
    >
      <div className="scene-topline">
        <span className="scene-view-label">
          <Icon name="cube" size={15} />
          {transfer?.source === "visual preview"
            ? "Visual preview · synthetic"
            : "Executive floor"}
        </span>
        <div className="scene-view-controls">
          <button
            type="button"
            aria-pressed={following}
            disabled={view !== "3d" || !ready}
            onClick={() => setFollowing(!following)}
          >
            {following ? "Stop following" : "Follow handoffs"}
          </button>
          <button
            type="button"
            ref={expand}
            aria-label={
              immersive ? "Exit immersive view" : "Enter immersive view"
            }
            disabled={view !== "3d" || !ready}
            onClick={() => setImmersive(!immersive)}
          >
            <Icon name={immersive ? "cross" : "expand"} size={16} />
          </button>
          <button
            type="button"
            aria-label="Reset camera"
            onClick={() => engine.current?.resetCamera()}
            disabled={view !== "3d" || !ready}
          >
            <Icon name="refresh" size={16} />
          </button>
          <button
            type="button"
            onClick={() => {
              setView(view === "3d" ? "list" : "3d");
              setImmersive(false);
            }}
          >
            <Icon name={view === "3d" ? "list" : "cube"} size={16} />
            {view === "3d" ? "Team list" : "3D view"}
          </button>
        </div>
      </div>
      {view === "3d" ? (
        <div className="scene-viewport">
          <canvas
            ref={canvas}
            aria-label="Five three-dimensional executive avatars. Drag to orbit. Select agents with the labelled buttons."
          />
          {!ready && !error && (
            <div role="status" className="scene-loading">
              Preparing your executive floor…
            </div>
          )}
          {error && (
            <p role="alert" className="scene-loading">
              {error}
              <button onClick={() => setView("list")}>Open team list</button>
            </p>
          )}
          <div
            className={`scene-labels ${ready && !error ? "is-ready" : ""}`}
            ref={labels}
            inert={!ready || !!error}
          >
            {AGENTS.map((a) => (
              <button
                key={a.id}
                data-agent={a.id}
                aria-label={`Select ${a.label}`}
                aria-pressed={selected === a.id}
                onClick={() => onSelect(a.id)}
                style={{ "--agent-color": a.color } as React.CSSProperties}
              >
                <i />
                {a.label}
              </button>
            ))}

          </div>
        </div>
      ) : (
        <div className="studio-accessible-team">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              onClick={() => onSelect(a.id)}
              aria-pressed={selected === a.id}
            >
              <span style={{ color: a.color }}>
                <Icon name="cube" size={30} />
              </span>
              <strong>{a.label}</strong>
              <small>{a.role}</small>
              <Icon name="chevron" />
            </button>
          ))}
        </div>
      )}
      <div className="scene-bottomline">
        <span>
          <i className="status-dot" />{" "}
          {transfer
            ? `${transfer.sender.toUpperCase()} → ${transfer.receiver.toUpperCase()} · ${transfer.label}`
            : "Select an avatar to see its work"}
        </span>
        <span>Drag to orbit</span>
      </div>
    </section>
  );
}
