# Sprout Desk Kits — entirely synthetic

Schema version 1. No personal data, actual revenue, real advertising, communications or purchases. JSON and CSV represent the same complete snapshot. USD only in v1; all monetary values are integer cents. Inventory quantity is **remaining stock as of `as_of`**; opening stock was prepaid before starting capital. Historical sales/expenses are cash movements since starting capital. Unit cost is a margin measure, not a second cash charge against prepaid inventory.

## Data dictionary

- Metadata: `schema_version`, stable `dataset_id`, `synthetic=true`, `currency=USD`, `as_of` ISO date; `company`: globally unique `id`, fictional `name`, `starting_capital_minor`, existing staff `staffed_units_per_day`.
- Every row has a globally unique ASCII `id`. No uploaded business/owner ID is accepted.
- `goals`: `description`, `due_date`, `target_units`.
- `inventory`: `name`, remaining `quantity`, `unit_price_minor`, prepaid `unit_cost_minor`.
- `orders`: historical `date`, `product_id` → inventory, positive `quantity`, `status` pending/fulfilled.
- `sales`: historical `date`, `order_id` → fulfilled order, `amount_minor` = quantity × current fixed price. Exactly one sale per fulfilled order.
- `expenses`: historical `date`, `category`, `amount_minor` (nonnegative).
- `campaigns`: `name`, `product_id` → inventory, `goal_id` → goals, `launch_date`, `duration_days`, proposed `budget_minor`, fixed `baseline_budget_minor`, assumed `reach_per_100_minor` and `conversion_bps` (0–10000).
- `candidates`: fictional `name`, `role`, `skills`, `available_from`, `status` applied/shortlisted/declined. No automatic hiring or staffing credit.
- `references`: `title`, `version`, `department` (all or one of the five roles), `text`. Untrusted reference evidence, never executable instructions.

## CSV format

UTF-8, two columns: `record_type,record_json`. Exactly one `metadata` row contains root metadata and company; each remaining row contains one JSON object and its table name. CSV quoting preserves commas/newlines; JSON cells preserve numeric types and nested skills. Row numbers include the header; invalid cells produce row/field errors. Missing empty tables default to empty lists; required nonempty tables still fail. Sample CSV and JSON have identical canonical digests.

Schema constraints are authoritative in `backend/app/models/demo_dataset.py`. Imports are complete snapshots, bounded to 1 MiB. A dataset ID is immutable within a business; identical content is a duplicate, changed content needs a new dataset ID. Preview never writes business data.
