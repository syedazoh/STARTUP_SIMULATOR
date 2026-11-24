import "./globals.css";
import "../components/appearance.css";
import Appearance from "../components/appearance";
import "../components/agent-avatar.css";
import { headers } from "next/headers";
import "../components/studio/studio.css";
import WorkspaceVisuals from "../components/workspace-visuals";
import WorkspaceFooter from "../components/workspace-footer";
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
        <Appearance/>
        <WorkspaceVisuals/>
        <header className="site-header">
          <a href="/" className="site-brand">
            <Icon name="studio" /> Startup Simulator
          </a>
          <span>Your executive workspace</span>
        </header>
        <div className="site-main">{children}</div>
        <WorkspaceFooter/>
      </body>
    </html>
  );
}
