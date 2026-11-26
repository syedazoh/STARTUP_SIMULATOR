import {ACCESS_COOKIE,REFRESH_COOKIE,restoreNative,refreshedCookie,accessOptions} from "./lib/native-session";
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
    // Retire the old scoped refresh cookie without replacing the current root cookie.
    result.headers.append('Set-Cookie', `${REFRESH_COOKIE}=; Path=/api/auth; Max-Age=0; HttpOnly; SameSite=Strict${process.env.NODE_ENV==='production'?'; Secure':''}`);
    return result;
  }
  let response = next();
  // Public pages need a CSP nonce, not a provider round trip.
  if (!/^\/(workspace|auth)(\/|$)/.test(request.nextUrl.pathname)) return response;
  if(!request.nextUrl.pathname.startsWith('/workspace'))return response;
  try{
    const session=await restoreNative(request.cookies.get(ACCESS_COOKIE)?.value,request.cookies.get(REFRESH_COOKIE)?.value);
    if(!session){const destination=new URL('/login',request.url);destination.searchParams.set('next',request.nextUrl.pathname+request.nextUrl.search);return NextResponse.redirect(destination)}
    request.cookies.set(ACCESS_COOKIE,session.access);response=next();
    response.cookies.set(ACCESS_COOKIE,session.access,accessOptions());
    if(session.response){const refresh=refreshedCookie(session.response);if(refresh){request.cookies.set(refresh.name,refresh.value);response.cookies.set(refresh.name,refresh.value,refresh.options)}}
  }catch{/* Data routes still validate the existing bearer; failures never grant access. */}
  return response;
}
export const config = {matcher: ['/((?!_next/static|_next/image|favicon.ico|media/|fonts/).*)']};
