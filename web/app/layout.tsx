import "./globals.css";
import { headers } from "next/headers";
import "../components/studio/studio.css";
import Icon from "../components/studio/icon";
export const metadata = {
  title: "Startup Simulator | Owner workspace",
  description: "Your supervised startup workspace",
};
export default async function Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  await headers(); // Per-request nonce must never be reused from static HTML.
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <a href="/" className="site-brand">
            <Icon name="studio" /> Startup Simulator
          </a>
          <span>Your executive workspace</span>
        </header>
        <div className="site-main">{children}</div>
      </body>
    </html>
  );
}
