export function apiError(status: number, body: unknown, path: string) {
  if (status === 401) return "Your session ended. Please sign in again.";
  if (status === 403) return "You do not have access to this business or task.";
  if (status === 404) return "This business or task was not found.";
  if (status === 429)
    return "Too many requests. Wait a minute before trying again.";
  if (status === 409 && path === "/api/auth/me")
    return "Existing account found. Link your original login below to preserve your businesses.";
  if (status >= 500)
    return "The backend or an AI provider is unavailable. Check backend health and configuration, then refresh before retrying.";
  const detail =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : null;
  if (typeof detail === "string") return detail.slice(0, 1500);
  if (Array.isArray(detail))
    return detail
      .slice(0, 5)
      .map((entry) => {
        const loc = Array.isArray(entry?.loc)
          ? entry.loc.filter((x: unknown) => typeof x === "string").join(" · ")
          : "Input";
        return `${loc}: ${typeof entry?.msg === "string" ? entry.msg : "Invalid value"}`;
      })
      .join("; ");
  return "Request failed. Refresh and try again.";
}
