"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <section className="card">
      <h1>We couldn’t load this page</h1>
      <p role="alert">
        Check service configuration and connectivity, then retry.
      </p>
      <button onClick={reset}>Try again</button>
      <p>
        <a href="/login">Return to sign in</a>
      </p>
    </section>
  );
}
