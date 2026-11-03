import "./globals.css";
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
        <header>
          <a href="/">STARTUP SIMULATOR</a>
          <span>Owner workspace · Authentication preview</span>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
