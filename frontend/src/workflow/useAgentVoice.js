"use client";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
let speakingOwner = null;
const subscribe = () => () => {},
  microphoneSnapshot = () =>
    !!(window.SpeechRecognition || window.webkitSpeechRecognition),
  serverMicrophone = () => false;
/** Browser dictation is reviewed before Send; no audio file is retained by the app. */
export default function useAgentVoice(onTranscript, locale = "en-US") {
  const owner = useRef({}),
    live = useRef(false),
    sequence = useRef(0),
    recognition = useRef(null),
    transcript = useRef(onTranscript);
  const microphone = useSyncExternalStore(
    subscribe,
    microphoneSnapshot,
    serverMicrophone,
  );
  const [phase, setPhase] = useState("idle"),
    [notice, setNotice] = useState("");
  function stop() {
    sequence.current++;
    recognition.current?.abort();
    recognition.current = null;
    if (speakingOwner === owner.current) {
      window.speechSynthesis?.cancel();
      speakingOwner = null;
    }
    if (live.current) {
      setPhase("idle");
      setNotice("");
    }
  }
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
      stop();
    };
  }, []);
  function dictate(initial) {
    stop();
    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setNotice("Voice input is unavailable. Type your message below.");
      return;
    }
    const token = ++sequence.current,
      rec = new Recognition();
    recognition.current = rec;
    let text = "";
    rec.lang = locale;
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (event) => {
      if (!live.current || token !== sequence.current) return;
      text = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      setNotice("Listening: " + text);
    };
    rec.onend = () => {
      if (!live.current || token !== sequence.current) return;
      recognition.current = null;
      setPhase("idle");
      if (text.trim()) {
        transcript.current((initial + " " + text.trim()).trim());
        setNotice("Transcript ready. Review it, then press Send.");
      } else setNotice("No words captured. Try again or type your message.");
    };
    rec.onerror = () => {
      if (live.current && token === sequence.current) {
        recognition.current = null;
        sequence.current++;
        setPhase("idle");
        setNotice(
          "Microphone or speech service unavailable. Typed input still works.",
        );
      }
    };
    try {
      rec.start();
      setPhase("listening");
      setNotice(
        "Listening. Press Finish dictation when you are done. Nothing is sent automatically.",
      );
    } catch {
      setPhase("idle");
      setNotice("Could not start the microphone. Type your message instead.");
    }
  }
  function finish() {
    recognition.current?.stop();
  }
  function speak(text) {
    stop();
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
      setNotice("Spoken playback unavailable. The response remains visible.");
      return;
    }
    const token = ++sequence.current,
      utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = locale;
    const voices = window.speechSynthesis.getVoices?.() || [];
    utterance.voice =
      voices.find((voice) => voice.lang === locale) ||
      voices.find((voice) => voice.lang.startsWith("en")) ||
      null;
    utterance.onend = () => {
      if (live.current && token === sequence.current) {
        setPhase("idle");
        setNotice("Playback finished.");
        if (speakingOwner === owner.current) speakingOwner = null;
      }
    };
    utterance.onerror = () => {
      if (live.current && token === sequence.current) {
        setPhase("idle");
        setNotice("Playback stopped or unavailable. Read the response below.");
      }
    };
    try {
      window.speechSynthesis.cancel();
      speakingOwner = owner.current;
      window.speechSynthesis.speak(utterance);
      setPhase("speaking");
      setNotice(
        "Reading the visible short response. You can interrupt at any time.",
      );
    } catch {
      setPhase("idle");
      setNotice("Playback unavailable. Read the response below.");
    }
  }
  return { microphone, phase, notice, dictate, finish, speak, stop, version: () => sequence.current };
}
