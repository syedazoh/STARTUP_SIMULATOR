import {readRuns} from './actions';
import Runs from './panel';
export const dynamic = 'force-dynamic';
export default async function Page({params}: {params: Promise<{businessId: string}>}) {
  const {businessId} = await params;
  try {return <Runs businessId={businessId} initial={await readRuns(businessId)}/>;}
  catch {return <section className="card"><h1>Simulation unavailable</h1><p role="alert">Sign in and check backend connectivity and business access.</p><a href="/workspace">Return to businesses</a></section>;}
}
