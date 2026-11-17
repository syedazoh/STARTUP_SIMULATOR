import "./globals.css";
import "../components/studio/studio.css";
import Icon from "../components/studio/icon";
export const metadata = {
  title: "Startup Simulator | Owner workspace",
  description: "Your supervised startup workspace",
};
export default function Layout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
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
