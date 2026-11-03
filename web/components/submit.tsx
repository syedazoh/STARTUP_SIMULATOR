"use client";
import { useFormStatus } from "react-dom";
export function Submit({ children }: { children: React.ReactNode }) {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Please wait…" : children}
    </button>
  );
}
