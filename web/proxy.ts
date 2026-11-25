import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
export async function proxy(request: NextRequest) {
  const nonce = btoa(crypto.randomUUID());
  const csp = ["default-src 'self'", `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${process.env.NODE_ENV === 'development' ? " 'unsafe-eval'" : ''}`,
    "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob:", "font-src 'self' data:",
    "connect-src 'self'", "media-src 'self'", "frame-src 'none'", "frame-ancestors 'none'",
    "base-uri 'self'", "form-action 'self'", "object-src 'none'"].join('; ');
  function next() {
    const headers = new Headers(request.headers);
    headers.set('Content-Security-Policy', csp);
    headers.set('x-nonce', nonce);
    const result = NextResponse.next({request: {headers}});
    result.headers.set('Content-Security-Policy', csp);
    result.headers.set('Cache-Control', 'private, no-store');
    return result;
  }
  let response = next();
  // Public pages need a CSP nonce, not a provider round trip.
  if (!/^\/(workspace|auth)(\/|$)/.test(request.nextUrl.pathname)) return response;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL, key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) return response;
  const client = createServerClient(url, key, {
    cookieOptions: {httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/'},
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(values) {
        values.forEach(({name,value})=>request.cookies.set(name,value));
        response=next();
        values.forEach(({name,value,options})=>response.cookies.set(name,value,options));
      },
    },
  });
  try {const {data:{user}}=await client.auth.getUser();if(!user&&/^\/workspace(?:\/|$)/.test(request.nextUrl.pathname)){const destination=new URL('/login',request.url);destination.searchParams.set('next',request.nextUrl.pathname+request.nextUrl.search);const redirect=NextResponse.redirect(destination);response.cookies.getAll().forEach(cookie=>redirect.cookies.set(cookie));redirect.headers.set('Cache-Control','private, no-store');return redirect;}} catch {/* Pages validate identity fail-closed. */}
  return response;
}
export const config = {matcher: ['/((?!_next/static|_next/image|favicon.ico|media/|fonts/).*)']};
