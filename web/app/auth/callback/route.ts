import { NextResponse, type NextRequest } from "next/server";
import { supabase } from "../../../lib/supabase";
export async function GET(request: NextRequest) {
  const client = await supabase();
  const base = process.env.APP_URL || request.nextUrl.origin;
  const code = request.nextUrl.searchParams.get("code");
  if (code) {
    const { error } = await client.auth.exchangeCodeForSession(code);
    if (!error) return NextResponse.redirect(new URL("/workspace", base));
  }
  return NextResponse.redirect(new URL("/login?error=confirmation", base));
}
