import {NextResponse,type NextRequest} from 'next/server';
import {backendResponse} from '../../../../lib/backend';
import {classicOriginAllowed} from '../../../../lib/classic-origin';
export async function POST(request:NextRequest){
 if(!classicOriginAllowed(request.headers))return NextResponse.json({detail:'Invalid session request origin'},{status:403});
 try{const response=await backendResponse('/api/auth/supabase-session',{method:'POST',headers:{'X-Requested-With':'XMLHttpRequest'}});const body=await response.json();if(typeof body.access_token!=='string')throw new Error();const result=NextResponse.json({access_token:body.access_token,token_type:'bearer'});result.headers.set('Cache-Control','no-store');for(const cookie of response.headers.getSetCookie()){if(cookie.startsWith('simulator_refresh='))result.headers.append('Set-Cookie',cookie)}return result;}
 catch{return NextResponse.json({detail:'Open the main sign-in on port 3000, then retry. Existing businesses may need the one-time ownership link.'},{status:401,headers:{'Cache-Control':'no-store'}})}
}
