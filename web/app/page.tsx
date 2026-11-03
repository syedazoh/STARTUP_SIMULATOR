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
        Connect your identity and keep your business records as we build your
        team of five AI departments.
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
        Authentication is the first migration milestone. Department screens
        remain in the existing application.
      </p>
    </section>
  );
}
