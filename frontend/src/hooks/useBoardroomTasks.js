import { useEffect, useState } from "react";
import apiClient from "../api/client";

// The approval queue omits work after execution. The floor needs full task snapshots.
const EMPTY = { items: [], ready: false, error: null };
export default function useBoardroomTasks(businessId) {
  const [snapshot, setSnapshot] = useState({ ...EMPTY, businessId });
  useEffect(() => {
    let active = true,
      inFlight = false;
    const controller = new AbortController();
    const refresh = async () => {
      if (inFlight || document.hidden) return;
      inFlight = true;
      try {
        const response = await apiClient.get(
          `/api/businesses/${encodeURIComponent(businessId)}/tasks`,
          { params: { limit: 200 }, signal: controller.signal },
        );
        if (active)
          setSnapshot({
            businessId,
            items: response.data,
            ready: true,
            error: null,
          });
      } catch {
        if (active)
          setSnapshot((old) => ({
            ...(old.businessId === businessId ? old : EMPTY),
            businessId,
            error:
              "Task connections could not refresh. Showing the last available snapshot.",
          }));
      } finally {
        inFlight = false;
      }
    };
    void refresh();
    const timer = setInterval(refresh, 1800);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      active = false;
      controller.abort();
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [businessId]);
  return snapshot.businessId === businessId ? snapshot : EMPTY;
}
