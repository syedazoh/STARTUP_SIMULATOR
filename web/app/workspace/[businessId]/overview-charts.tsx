import {
  departments,
  labels,
  type Workspace,
} from "../../../lib/workspace-contracts";
const format = (value: number) =>
  new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
function Bars({
  items,
  label,
}: {
  items: { name: string; value: number; color: string }[];
  label: string;
}) {
  const min = Math.min(0, ...items.map((i) => i.value)),
    max = Math.max(1, ...items.map((i) => i.value));
  const x = (value: number) => 170 + ((value - min) / (max - min)) * 340;
  return (
    <dl className="overview-bars" aria-label={label}>
      {items.map((item) => (
        <div key={item.name}>
          <dt>{item.name}</dt>
          <dd>
            <span className="overview-bar-track" aria-hidden="true">
              <i style={{ left: `${((x(0) - 170) / 340) * 100}%` }} />
              <span
                style={{
                  left: `${((Math.min(x(0), x(item.value)) - 170) / 340) * 100}%`,
                  width: `${(Math.abs(x(item.value) - x(0)) / 340) * 100}%`,
                  background: item.color,
                }}
              />
            </span>
            <strong>{format(item.value)}</strong>
          </dd>
        </div>
      ))}
    </dl>
  );
}
export default function OverviewCharts({ data }: { data: Workspace }) {
  const finance = data.finances.data;
  const colors = ["#b9a0ed", "#d8c4a2", "#d99cce", "#e1b49e", "#97ace0"];
  return (
    <div className="overview-charts">
      <section className="overview-panel">
        <div className="overview-panel-heading">
          <h2>Work across the team</h2>
          <span>Loaded task snapshot</span>
        </div>
        {data.tasks.error ? (
          <p role="alert">
            Task distribution unavailable. Refresh to try again.
          </p>
        ) : data.tasks.data.length ? (
          <Bars
            label="Tasks by department"
            items={departments.map((key, i) => ({
              name: labels[key],
              value: data.tasks.data.filter((t) => t.agent === key).length,
              color: colors[i],
            }))}
          />
        ) : (
          <div className="overview-empty">
            <h3>A clear floor, ready for work.</h3>
            <p>
              No tasks loaded yet. Create a proposal or ask the CEO for a plan
              below.
            </p>
          </div>
        )}
        <p className="overview-caption">
          Latest 200 tasks. Counts show recorded assignments, not completion
          rates.
        </p>
      </section>
      <section className="overview-panel">
        <div className="overview-panel-heading">
          <h2>The financial picture</h2>
          <span>Simulator ledger units</span>
        </div>
        {data.finances.error ||
        !finance ||
        !Object.values(finance).every(Number.isFinite) ? (
          <div className="overview-empty">
            <h3>Finance snapshot unavailable</h3>
            <p>
              Refresh the workspace to try again. No estimated balance is shown.
            </p>
          </div>
        ) : (
          <Bars
            label="Recorded financial snapshot"
            items={[
              {
                name: "Available funds",
                value: finance.available,
                color: "#b9a0ed",
              },
              { name: "Revenue", value: finance.revenue, color: "#d8c4a2" },
              { name: "Expenses", value: finance.expenses, color: "#d99cce" },
              {
                name: "Monthly payroll",
                value: finance.monthly_payroll_commitment,
                color: "#97ace0",
              },
            ]}
          />
        )}
        <p className="overview-caption">
          Current recorded values, not a historical trend. Dataset balances are
          separate.
        </p>
      </section>
    </div>
  );
}
