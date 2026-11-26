import {NextResponse,type NextRequest} from 'next/server';
import {classicOriginAllowed} from '../../../../lib/classic-origin';
import {logoutSessions} from '../../../../lib/logout-sessions';
export async function POST(request:NextRequest){if(!classicOriginAllowed(request.headers))return NextResponse.json({detail:'Invalid session request origin'},{status:403});try{await logoutSessions(request.headers.get('authorization')?.replace(/^Bearer /i,''));return NextResponse.json({ok:true},{headers:{'Cache-Control':'no-store'}})}catch{return NextResponse.json({detail:'Sign out could not finish. Keep this tab open and retry.'},{status:503,headers:{'Cache-Control':'no-store'}})}}
