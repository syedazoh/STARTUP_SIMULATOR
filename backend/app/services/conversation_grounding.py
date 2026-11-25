"""Small explicit cases use structured records, not language-model arithmetic."""
import re
from ..agents.schemas import ChatReply
from ..database.utils import find_one

DEFINITIONS = {
    'runway':'Runway is how long a startup can keep operating before its cash runs out. A simple estimate is available cash divided by monthly net cash burn; no account data is needed to define the term.',
    'roi':'ROI means return on investment: the gain relative to the investment cost. A company-specific ROI calculation needs an identified cost and measured return.',
    'mrr':'MRR means monthly recurring revenue: recurring subscription revenue normalized to one month.',
    'arr':'ARR means annual recurring revenue: recurring revenue normalized to one year.',
    'hr':'HR means Human Resources: the department responsible for people and staffing.',
    'ceo':'CEO means Chief Executive Officer: the role coordinating strategy and departmental plans.',
    'csv':'CSV means comma-separated values, a tabular file format used by the simulator importer.',
}

async def direct_reply(db,business,agent,content,history,screen):
    text=content.strip();low=text.lower()
    # The center of our actual task-status donut represents the same loaded task list.
    if 'total' in low and any(word in low for word in ('chart','donut','task')):
        count=await db['tasks'].count_documents({'business_id':business.id})
        shown=min(count,200)
        return ChatReply(reply=f'The center total in the task-status donut is the number of loaded tasks for {business.company_name}: {shown}. Each task contributes once to a status segment. The chart is limited to the latest 200 tasks, not a lifetime total.')
    if re.match(r'^(what (?:is|does)|define|explain)\b',low):
        for term,definition in DEFINITIONS.items():
            if re.search(r'\b'+term+r'\b',low) and not any(word in low for word in ('our ','my ','this startup','calculate')):
                return ChatReply(reply=definition)
    ambiguous=re.fullmatch(r"(?:what is|what does)\s+(?:(?:a|an)\s+)?['\"]?([A-Za-z]{1,3})['\"]?(?:\s+(?:mean|stand for))?\s*[?.!]*",text,re.I)
    if ambiguous and ambiguous.group(1).lower() not in DEFINITIONS:
        term=ambiguous.group(1)
        # Explicit owner clarification in this business's own conversation can resolve a term.
        definitions=[m['content'] for m in history[-20:] if m.get('role')=='owner' and re.search(r'\b'+re.escape(term)+r'\s+(?:means|stands for|refers to)\b',m.get('content',''),re.I)]
        if not definitions:
            return ChatReply(reply=f'Where did you see “{term}” in the simulator?',intent='clarify')
    business_words=r'\b(startup|business|campaign|marketing|finance|budget|shipping|customer|employee|hiring|operations|strategy|simulat|cash|runway|sales)'
    if re.search(r'\b(recipe|horoscope|football score|celebrity gossip|tell me a joke|write a love poem)\b',low) and not re.search(business_words,low):
        return ChatReply(reply='I can help with your startup and this simulator. Would you like to review your team’s pending tasks?',intent='out_of_scope')
    if re.search(r'\b(which|what|list|show)\b',low) and 'task' in low and any(word in low for word in ('approval','waiting','pending')):
        role=next((r for r in ('marketing','finance','operations','hr','ceo') if re.search(r'\b'+r+r'\b',low)),agent)
        query={'business_id':business.id,'agent':role,'status':'pending_approval'}
        count=await db['tasks'].count_documents(query)
        tasks=await db['tasks'].find(query).sort('created_at',-1).to_list(length=20)
        lines=[f'{role.upper() if role in {"ceo","hr"} else role.title()} has {count} task(s) waiting for owner approval in {business.company_name}.']
        lines.extend(f"• {t['task_id']}: {t.get('objective') or t['action_type'].replace('_',' ')}" for t in tasks)
        if count>20:lines.append('Showing the latest 20; open the approval inbox for details.')
        return ChatReply(reply='\n'.join(lines))
    if 'runway' in low and any(word in low for word in ('our','my','this startup','calculate')):
        return ChatReply(reply='To calculate this startup’s runway, I need its monthly net cash burn and the period it covers. What monthly net cash burn should I use? A budget cap is not the same as measured burn.',intent='missing_data')
    if 'afford' in low and any(word in low for word in ('campaign','promotion','post')):
        account=await find_one(db['financial_accounts'],{'_id':business.id})
        if not account:
            return ChatReply(reply='I do not have a recorded available balance for this business. Check Finance’s simulated ledger and tell me which campaign budget you want reviewed.',intent='missing_data')
        tasks=await db['tasks'].find({'business_id':business.id,'agent':'marketing','status':{'$in':['pending_approval','pending_ceo_review']}}).to_list(length=20)
        candidates=[t for t in tasks if isinstance(t.get('payload',{}).get('requested_budget'),(int,float))]
        if len(candidates)!=1:return ChatReply(reply='Which campaign or proposed promotion amount should I compare with the available simulated budget?',intent='clarify')
        amount=candidates[0]['payload']['requested_budget'];available=(account['cash_minor']-account['reserved_minor'])/100
        return ChatReply(reply=f"The recorded available simulated balance is {available:,.2f} units. {candidates[0].get('objective','The campaign')} requests {amount:,.2f} units. It {'fits' if amount<=available else 'exceeds'} that balance. This is an affordability check, not approval to spend.")
    return None
