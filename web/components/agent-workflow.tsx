"use client";
import SharedWorkflow from "../../frontend/src/workflow/AgentWorkflow";
import {
  readWorkflow,
  workflowCommand,
} from "../app/workspace/workflow-actions";
async function readImage(businessId: string, role: string, id: string) {
  const response = await fetch(
    `/api/agent-image?businessId=${encodeURIComponent(businessId)}&role=${encodeURIComponent(role)}&id=${encodeURIComponent(id)}`,
  );
  if (!response.ok) throw new Error("Image unavailable");
  return response.blob();
}
export default function AgentWorkflow({
  businessId,
  role = "ceo",
  boardroom = false,
}: {
  businessId: string;
  role?: string;
  boardroom?: boolean;
}) {
  return (
    <SharedWorkflow
      key={`${businessId}:${role}:${boardroom}`}
      businessId={businessId}
      role={role}
      boardroom={boardroom}
      read={readWorkflow}
      command={workflowCommand}
      readImage={readImage}
    />
  );
}
