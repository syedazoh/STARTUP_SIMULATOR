import Link from "next/link";
export default function Home() {
  return (
    <section className="hero">
      <p className="eyebrow">A clearer way to run your startup</p>
      <h1>
        A startup takes a team.
        <br />
        Meet yours.
      </h1>
      <p>
        Give your five executive departments a shared direction. Explore their
        3D workspace, review the work and stay in control of every approval.
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
        The executive studio visualizes recorded task states. A separate visual
        preview lets you explore handoffs without taking real actions.
      </p>
    </section>
  );
}
