import {notFound} from 'next/navigation';
import {backend} from '../../../../../lib/backend';
import {allDepartments,type Business,type Department} from '../../../../../lib/workspace-contracts';
import {readWorkspace} from '../../actions';
import CommandCenter from '../../command-center';
import AgentTools from './tools';
import {readAgentTools} from './actions';
export const dynamic='force-dynamic';
export default async function AgentPage({params}:{params:Promise<{businessId:string;department:string}>}){
 const {businessId,department}=await params;
 if(!allDepartments.includes(department as Department))notFound();
 let business:Business;
 try{business=await backend(`/api/businesses/${encodeURIComponent(businessId)}`)}catch(error){return <section className="card"><h1>Department workspace unavailable</h1><p role="alert">{error instanceof Error?error.message:'Could not load this business.'}</p><a href="/workspace">Return to your businesses</a></section>}
 const role=department as Department;const [initial,tools]=await Promise.all([readWorkspace(businessId),readAgentTools(businessId,role)]);
 return <CommandCenter key={`${businessId}:${role}`} business={business} initial={initial} initialDepartment={role} agentTools={<AgentTools businessId={businessId} department={role} initial={tools} enabled={business.enabled_agents.includes(role)||(role==='strategy'&&business.enabled_agents.includes('ceo'))}/>}/>;
}
