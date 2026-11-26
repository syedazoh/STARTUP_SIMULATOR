import {NextResponse,type NextRequest} from 'next/server';
import {ACCESS_COOKIE,REFRESH_COOKIE,restoreNative,accessOptions} from '../../../../lib/native-session';
import {classicOriginAllowed} from '../../../../lib/classic-origin';
export async function POST(request:NextRequest){
 if(!classicOriginAllowed(request.headers))return NextResponse.json({detail:'Invalid session request origin'},{status:403});
 try{const session=await restoreNative(request.cookies.get(ACCESS_COOKIE)?.value,request.cookies.get(REFRESH_COOKIE)?.value);if(!session)throw new Error();const result=NextResponse.json({access_token:session.access,token_type:'bearer'},{headers:{'Cache-Control':'no-store'}});result.cookies.set(ACCESS_COOKIE,session.access,accessOptions());if(session.response)for(const cookie of session.response.headers.getSetCookie())if(cookie.startsWith('simulator_refresh='))result.headers.append('Set-Cookie',cookie);return result}
 catch{return NextResponse.json({detail:'Sign in with your original simulator email and password on port 3000.'},{status:401,headers:{'Cache-Control':'no-store'}})}
}
