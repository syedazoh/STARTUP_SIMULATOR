import { NextResponse, type NextRequest } from "next/server";
import { supabase } from "../../../lib/supabase";
export async function GET(request: NextRequest) {
  const client = await supabase();
  const base = process.env.APP_URL || request.nextUrl.origin;
  const token_hash = request.nextUrl.searchParams.get("token_hash"),
    type = request.nextUrl.searchParams.get("type");
  if (token_hash && type === "email") {
    const { error } = await client.auth.verifyOtp({
      token_hash,
      type: "email",
    });
    if (!error) return NextResponse.redirect(new URL("/workspace", base));
  }
  return NextResponse.redirect(new URL("/login?error=confirmation", base));
}
