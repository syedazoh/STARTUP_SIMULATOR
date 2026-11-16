import Link from "next/link";
export default function Home() {
  return (
    <section className="hero">
      <p className="eyebrow">A clearer way to run your startup</p>
      <h1>
        Your ambition.
        <br />
        One shared workspace.
      </h1>
      <p>
        Plan work with five AI departments, review proposals and keep the
        results in your business workspace.
      </p>
      <div className="actions">
        <Link className="button" href="/login">
          Sign in
        </Link>
        <Link className="button secondary" href="/signup">
          Create account
        </Link>
      </div>
      <p>
        Create your business, delegate a plan and review simulated outcomes
        before connecting real services.
      </p>
    </section>
  );
}
