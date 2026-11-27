export function linkFailure(status:number,phase:'login'|'link'){
 if(status>=500)return 'link_backend';
 if(phase==='login'&&(status===400||status===401))return 'link_credentials';
 if(phase==='link'&&status===409)return 'link_conflict';
 if(phase==='link'&&(status===400||status===401||status===403))return 'link_identity';
 if(status===429)return 'link_rate';
 return 'link';
}
export const workspaceIssues:Record<string,string>={
 link_credentials:'The original Startup Simulator email or password was not accepted. Use the old account password, which may differ from your Supabase password. No new business is needed to link an existing company.',
 link_backend:'The original-account service is unavailable. Check that the backend and your original MongoDB database are running, then retry.',
 link_conflict:'This identity is already linked or conflicts with an existing account. Do not create another company to recover it; resolve the account link first.',
 link_identity:'The backend could not verify the account link. Check that frontend and backend use the same Supabase project, then sign in again before retrying.',
 link_rate:'Too many account-link attempts. Wait briefly before trying again.',
 link:'The account link could not finish. Check the backend connection and original account details, then retry.',
 logout:'Sign out could not finish. Retry signing out.',
 input:'Enter the original account email and a password of 8–128 characters.'
};

export function workspaceIssue(code:string){
 if(code==='demo_setup')return 'The fictional demo could not finish loading. Check backend/Mongo connectivity and retry; existing companies are unchanged.';return Object.hasOwn(workspaceIssues,code)?workspaceIssues[code]:"The request could not finish. Retry or check the connection message below."}
