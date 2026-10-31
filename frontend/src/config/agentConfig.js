// Per-agent field/label config shared by AgentDetail's action form, policy
// form, and metric charts. `ceo` is intentionally absent from action/policy
// UI — arbitration is system-triggered by Finance's escalation, not a
// user-initiated department action, and doesn't fit the threshold-policy shape.
const AGENT_CONFIG = {
  finance: {
    label: 'Finance',
    metricKeys: ['budget_pool', 'revenue', 'expenses'],
    actionEndpoint: 'finance/actions/budget-request',
    actionFields: [
      { name: 'amount', label: 'Amount ($)', type: 'number', default: 1000 },
      { name: 'department', label: 'Department', type: 'text', default: 'Operations' },
    ],
    policyLabels: {
      auto_approve_max: 'Auto-approve budget requests under ($)',
      auto_deny_min: 'Auto-deny budget requests at or above ($)',
    },
  },
  marketing: {
    label: 'Marketing',
    metricKeys: ['customer_base', 'brand_value'],
    actionEndpoint: 'marketing/actions/campaign-launch',
    actionFields: [
      { name: 'campaign_name', label: 'Campaign name', type: 'text', default: 'New Campaign' },
      { name: 'requested_budget', label: 'Requested budget ($)', type: 'number', default: 3000 },
    ],
    policyLabels: {
      auto_approve_max: 'Auto-approve campaigns with budget under ($)',
      auto_deny_min: 'Auto-deny campaigns with budget at or above ($)',
    },
  },
  hr: {
    label: 'HR',
    metricKeys: ['employee_count', 'team_morale'],
    actionEndpoint: 'hr/actions/recruitment-request',
    actionFields: [
      { name: 'role', label: 'Role', type: 'text', default: 'Engineer' },
      { name: 'headcount', label: 'Headcount', type: 'number', default: 1 },
      { name: 'monthly_salary', label: 'Monthly salary per hire ($)', type: 'number', default: 3000 },
    ],
    policyLabels: {
      auto_approve_max: 'Auto-approve headcount requests under',
      auto_deny_min: 'Auto-deny headcount requests at or above',
    },
  },
  operations: {
    label: 'Operations',
    metricKeys: ['resource_pool', 'operational_efficiency'],
    actionEndpoint: 'operations/actions/resource-request',
    actionFields: [
      { name: 'resource_type', label: 'Resource type', type: 'text', default: 'Cloud Compute' },
      { name: 'quantity', label: 'Quantity', type: 'number', default: 100 },
      { name: 'unit_cost', label: 'Cost per unit ($)', type: 'number', default: 100 },
    ],
    policyLabels: {
      auto_approve_max: 'Auto-approve resource requests under quantity',
      auto_deny_min: 'Auto-deny resource requests at or above quantity',
    },
  },
  ceo: null,
}

export default AGENT_CONFIG
