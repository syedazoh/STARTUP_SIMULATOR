// Run only against the intended database, with an operator-authenticated admin.
// On existing volumes, apply explicitly after backup; init scripts run only once.
const target = db.getSiblingDB('startup_simulator');
const password = process.env.MONGO_WORKER_PASSWORD;
if (!password || password.length < 24) throw new Error('A separate worker password of at least 24 characters is required');
const role = 'analysisWorker';
const privileges = [
  {resource:{db:'startup_simulator',collection:'background_jobs'},actions:['find','update']},
  {resource:{db:'startup_simulator',collection:'role_worker_health'},actions:['find','insert','update']},
  ...['businesses','distributed_runs','financial_accounts','knowledge_documents','agent_snapshots'].map(collection=>({resource:{db:'startup_simulator',collection},actions:['find']})),
];
if (target.getRole(role)) target.updateRole(role,{privileges,roles:[]});
else target.createRole({role,privileges,roles:[]});
if (!target.getUser('analysis_worker')) target.createUser({user:'analysis_worker',pwd:password,roles:[{role,db:'startup_simulator'}]});
// Existing password is deliberately not replaced implicitly.
