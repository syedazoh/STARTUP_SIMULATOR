"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBusiness } from "./actions";
export default function CreateBusiness() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const router = useRouter();
  return (
    <details className="card wide">
      <summary>Create a business</summary>
      <p>
        Start a separate workspace with all five departments. These are
        simulator starting values; importing a dataset uses its own isolated
        scenario.
      </p>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          if (busy) return;
          setBusy(true);
          setError("");
          try {
            const result = await createBusiness(
              new FormData(event.currentTarget),
            );
            if (result.ok) {
              router.push(`/workspace/${encodeURIComponent(result.id)}`);
              router.refresh();
            } else setError(result.error);
          } catch {
            setError(
              "Connection interrupted. Refresh the business list before creating again.",
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        <label htmlFor="company-name">Company name</label>
        <input id="company-name" name="company_name" required maxLength={200} />
        <label htmlFor="industry">Industry</label>
        <input id="industry" name="industry" required maxLength={100} />
        <div className="form-grid">
          <label>
            Starting budget (simulated units)
            <input
              name="starting_budget"
              type="number"
              min="0"
              max="1000000000"
              step="0.01"
              defaultValue="10000"
              required
            />
          </label>
          <label>
            Customers
            <input
              name="starting_customer_base"
              type="number"
              min="0"
              max="1000000000"
              step="1"
              defaultValue="0"
              required
            />
          </label>
          <label>
            Headcount
            <input
              name="starting_headcount"
              type="number"
              min="0"
              max="1000000"
              step="1"
              defaultValue="2"
              required
            />
          </label>
          <label>
            Resource units
            <input
              name="starting_resources"
              type="number"
              min="0"
              max="1000000000"
              step="1"
              defaultValue="100"
              required
            />
          </label>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button disabled={busy}>
          {busy ? "Creating…" : "Create workspace"}
        </button>
      </form>
    </details>
  );
}
