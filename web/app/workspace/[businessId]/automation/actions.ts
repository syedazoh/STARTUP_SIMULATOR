"use server";
import { backend } from "../../../../lib/backend";
const root = (id: string) => `/api/businesses/${encodeURIComponent(id)}`;
export async function readAutomation(id: string) {
  try {
    return { ok: true as const, data: await backend(root(id) + "/automation") };
  } catch (e) {
    return {
      ok: false as const,
      error: e instanceof Error ? e.message : "Workspace unavailable",
    };
  }
}
export async function automationCommand(
  id: string,
  command: string,
  payload: Record<string, unknown>,
  target = "",
  version = 0,
) {
  try {
    let path = root(id),
      method = "POST";
    const item = encodeURIComponent(target);
    switch (command) {
      case "job":
        path += "/jobs";
        break;
      case "cancel":
      case "retry":
        path += `/jobs/${item}/${command}`;
        break;
      case "document":
        path += "/knowledge";
        break;
      case "answer":
      case "search":
        path += `/knowledge/${command}`;
        break;
      case "delete":
        path += `/knowledge/${item}?version=${Number(version)}`;
        method = "DELETE";
        break;
      case "reindex":
        path += `/knowledge/${item}/reindex?version=${Number(version)}`;
        break;
      case "grant":
        path += "/mcp-grants";
        break;
      case "revoke":
        path += `/mcp-grants/${item}/revoke`;
        break;
      case "read":
        path += `/notifications/${item}/read`;
        break;
      case "deadline":
        path = `/api/tasks/${item}/deadline`;
        method = "PUT";
        break;
      default:
        throw new Error("Unknown automation command");
    }
    return {
      ok: true as const,
      data: await backend(path, {
        method,
        ...(method === "DELETE" ? {} : { body: JSON.stringify(payload) }),
        signal: AbortSignal.timeout(command === "answer" ? 45000 : 15000),
      }),
    };
  } catch (e) {
    return {
      ok: false as const,
      error:
        e instanceof Error
          ? e.message
          : "Request failed. Refresh before retrying.",
    };
  }
}
