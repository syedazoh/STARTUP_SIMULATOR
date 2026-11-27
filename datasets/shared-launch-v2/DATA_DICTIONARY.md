# Fictional startup dictionary

All records are project-authored **synthetic** data. Dates and IDs are scenario inputs, not real-world history. Schema version **1** reuses `datasets/product-launch-v1/schema.json` and `backend/app/models/demo_dataset.py`; `shared-launch-v2` names a different sample, not a breaking schema change. JSON and CSV represent the same validated snapshot.

| Record / field | Meaning and relationships |
| --- | --- |
| `schema_version`, `dataset_id`, `synthetic` | Version 1; stable sample ID `sprout-five-agent-v2`; synthetic must be true. |
| `currency`, `as_of` | USD; snapshot date 2026-11-27. Money is integer cents, never floating minor units. |
| `company.id`, `name` | Fictional company identity, distinct from the authenticated business ID assigned by the server. |
| `company.starting_capital_minor` | 30000 cents = USD 300 simulated starting cash. Existing businesses' cash is never overwritten by the demo opener. |
| `company.staffed_units_per_day` | 20 units per staffed working day; does not establish working hours or a calendar schedule. |
| `goals[].id`, `description`, `due_date`, `target_units` | Goal `goal-launch`: 50 fictional kits, owner-proposed deadline 2026-12-05. |
| `inventory[].id`, `name`, `quantity` | Product `product-kit`, 150 available fictional kits. |
| `inventory[].unit_price_minor`, `unit_cost_minor` | Proposed unit price USD 50; unit cost USD 20. Scenario inputs, not achieved sales or live supplier quotes. |
| `campaigns[].id`, `product_id`, `goal_id` | `campaign-launch` links the kit to `goal-launch`. |
| `campaigns[].launch_date`, `duration_days` | Proposed 2026-12-01 start, four days. No campaign is posted automatically. |
| `campaigns[].budget_minor`, `baseline_budget_minor` | USD 200 proposal and USD 100 deterministic-simulator baseline. They do not spend money by being imported. |
| `campaigns[].reach_per_100_minor`, `conversion_bps` | Explicit fictional simulator coefficients (10 reach per USD 1; 100 basis points = 1%). Shared conversational briefs do not claim these forecasts were achieved. |
| `candidates[].id`, `name`, `role`, `skills`, `available_from`, `status` | Fictional candidate `candidate-001`; proposed fulfillment assistant available 2026-12-01; applicant status is not employment. Operations covers staffing recommendations in the new workflow. |
| `references[].id`, `title`, `version`, `department`, `text` | Stable versioned synthetic launch policy, brand guide and operating brief. Indexed via existing authorized knowledge jobs; citations refer to saved document/chunk versions. |
| `sales`, `expenses`, `orders` | Empty arrays deliberately mean no historical observations for this fictional startup. No fake earned revenue is added. |

Server-created companion profile: warm/practical voice; remote teams/designers; deep purple/beige direction; USD 300 planning cap. Owner-reported fictional workforce totals five: two Operations packers, two Engineering designers and one part-time Marketing planner. A budget cap is not the ledger balance; exact spending comparisons load the saved ledger. Starting USD 300 versus proposed USD 400 gives a USD 100 gap. Capacity for 50 kits at 20/day requires three **staffed working days**, not a guaranteed calendar date.

The shared launch stores four zero-cost internal brief tasks, references to immutable recommendation/image artifacts, explicit proposed deadlines, prior versions and owner decisions. It does not simulate market outcomes from a chat answer. The retained older deterministic launch evaluator has separately documented rules/baselines in `docs/DATASET_SIMULATION.md`. Historical UCI GBP records remain a separate analytical snapshot with no conversion to this USD ledger.
