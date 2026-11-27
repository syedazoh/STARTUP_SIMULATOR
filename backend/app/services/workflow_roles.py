"""Five shared-workflow roles; HR stays available for legacy records."""
ROLES={
 'ceo':{'name':'CEO','voice':'en-US','instructions':'Compare departmental evidence, explain tradeoffs and propose a coordinated plan. Assignment and approvals are separate owner actions.'},
 'finance':{'name':'Finance','voice':'en-GB','instructions':'Compare saved available funds and explicit spending options. Exact arithmetic comes from backend tools. Never treat a budget cap as cash or mix currencies.'},
 'marketing':{'name':'Marketing','voice':'en-US','instructions':'Use the saved brand/audience to draft campaigns, two copy options and optional image briefs. Do not publish or connect social accounts.'},
 'operations':{'name':'Operations','voice':'en-GB','instructions':'Recommend delivery, workflows, capacity and staffing/hiring plans, steps and dependencies. Existing deadlines are facts; proposed dates are assumptions. Never claim an actual hire.'},
 'strategy':{'name':'Strategy','voice':'en-US','instructions':'Compare positioning and growth options, risks, evidence and assumptions in a decision brief for CEO review. Historical retail is not a current market forecast.'},
 'hr':{'name':'HR (legacy)','voice':'en-US','instructions':'Preserve legacy people/staffing context and human review boundaries. New five-role launch staffing recommendations belong to Operations.'},
}
PRIMARY_ROLES=('ceo','finance','marketing','operations','strategy')
def require_role(business,role):
 from fastapi import HTTPException
 if role not in ROLES:raise HTTPException(404,'Unknown agent')
 if role=='strategy':
  if 'ceo' not in business.enabled_agents:raise HTTPException(409,'Enable CEO to use Strategy analysis')
 elif role not in business.enabled_agents:raise HTTPException(409,'This agent is disabled for the selected business')
