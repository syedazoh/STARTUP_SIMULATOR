import { NextResponse, type NextRequest } from "next/server";
import { backendResponse } from "../../../lib/backend";
import { agentRole } from "../../../lib/agent-tools-contracts";
export async function GET(request: NextRequest) {
  try {
    const params = request.nextUrl.searchParams,
      businessId = params.get("businessId") || "",
      id = params.get("id") || "",
      role = agentRole(params.get("role") || "");
    if (!/^[a-f0-9]{64}$/.test(id) || !businessId || businessId.length > 80)
      return NextResponse.json(
        { error: "Invalid image reference" },
        { status: 400 },
      );
    const response = await backendResponse(
      `/api/businesses/${encodeURIComponent(businessId)}/workflow/${role}/artifacts/${id}/image`,
    );
    return new NextResponse(response.body, {
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Image unavailable for this session and business." },
      { status: 403 },
    );
  }
}
