"use client";
import { useEffect, useId, useState } from "react";
const money = (value) =>
  `GBP ${(value / 100).toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export default function RetailData({ businessId, read, upload }) {
  const [report, setReport] = useState(null),
    [preview, setPreview] = useState(null),
    [file, setFile] = useState(null),
    [format, setFormat] = useState("csv"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const id = useId();
  useEffect(() => {
    let active = true;
    read(businessId)
      .then((result) => {
        if (active) {
          if (result.ok) setReport(result.data);
          else setError(result.error);
        }
      })
      .catch(() => {
        if (active) setError("Historical retail data could not load.");
      });
    return () => {
      active = false;
    };
  }, [businessId, read]);
  async function run(action) {
    if (!file || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const form = new FormData();
      form.set("file", file);
      form.set("format", format);
      if (action === "import") form.set("expected_digest", preview.digest);
      const result = await upload(businessId, action, form);
      if (!result.ok) {
        setError(result.error);
        return;
      }
      if (action === "preview") setPreview(result.data);
      else {
        setReport(result.data);
        setPreview(null);
        setNotice(
          "Historical slice imported. No task, email, post or ledger spending was created.",
        );
      }
    } catch {
      setError("Import could not finish. Refresh the report before retrying.");
    } finally {
      setBusy(false);
    }
  }
  const summary = report?.summary,
    maximum = Math.max(
      1,
      ...(summary?.products || []).map((p) => p.gross_units),
    );
  return (
    <section
      className="agent-workflow retail-data"
      aria-label="Historical retail data"
    >
      <header className="workflow-heading">
        <div>
          <h2>Historical sales, clearly sourced.</h2>
          <p>
            Import a small transformed UCI slice to test totals, demand and
            cancellations. It stays separate from your fictional startup’s
            ledger.
          </p>
        </div>
        <a
          href="https://archive.ics.uci.edu/dataset/502/online+retail+ii"
          target="_blank"
          rel="noreferrer"
        >
          UCI Online Retail II · CC BY 4.0
        </a>
      </header>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void run("preview");
        }}
      >
        <label htmlFor={id + "format"}>Retail file format</label>
        <select
          id={id + "format"}
          value={format}
          onChange={(event) => {
            setFormat(event.target.value);
            setPreview(null);
          }}
        >
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
        <label htmlFor={id + "file"}>
          Transformed transactions · maximum 1 MiB / 1,000 rows
        </label>
        <input
          id={id + "file"}
          type="file"
          accept={format === "csv" ? ".csv" : ".json"}
          required
          onChange={(event) => {
            setFile(event.target.files?.[0] || null);
            setPreview(null);
          }}
        />
        <button disabled={busy || !file}>Preview retail import</button>
      </form>
      <p>
        Columns: record_id, invoice_id, stock_code, description, quantity,
        unit_price_minor, invoiced_at, country, source_row, source_sheet. Keep
        quantities signed and prices in GBP pence. Customer identifiers are
        excluded.
      </p>
      {preview && (
        <div className="retail-preview">
          <h3>
            {preview.valid
              ? "Ready to review"
              : "Correct the file before importing"}
          </h3>
          <p>
            {preview.summary.transaction_count} valid rows in this preview · net{" "}
            {money(preview.summary.net_sales_minor)}. Only the first ten rows
            are shown.
          </p>
          {preview.errors.map((item, i) => (
            <p role="alert" key={i}>
              Row {item.row}: {item.error}
            </p>
          ))}
          <div className="retail-table">
            <table>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Unit price</th>
                  <th>Source row</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row) => (
                  <tr key={row.record_id}>
                    <td>{row.invoice_id}</td>
                    <td>{row.stock_code}</td>
                    <td>{row.quantity}</td>
                    <td>{money(row.unit_price_minor)}</td>
                    <td>
                      {row.source_sheet} · {row.source_row}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            type="button"
            disabled={busy || !preview.valid}
            onClick={() => void run("import")}
          >
            Import reviewed retail slice
          </button>
        </div>
      )}
      {summary ? (
        <>
          <div className="retail-totals">
            {[
              ["Gross sales", summary.gross_sales_minor],
              ["Cancellations", summary.cancellations_minor],
              ["Other adjustments", summary.other_adjustments_minor],
              ["Net sales", summary.net_sales_minor],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{money(value)}</strong>
              </div>
            ))}
          </div>
          <p>
            {summary.transaction_count} imported transactions in the latest
            slice. {summary.rule}
          </p>
          <small>{report.source_claim}</small>
          <h3>Product demand in this slice</h3>
          <div className="retail-table">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Gross units</th>
                  <th>Cancelled units</th>
                  <th>Net units</th>
                  <th>Net value</th>
                </tr>
              </thead>
              <tbody>
                {summary.products.slice(0, 20).map((product) => (
                  <tr key={product.stock_code}>
                    <td>
                      {product.description}
                      <small>{product.stock_code}</small>
                    </td>
                    <td>
                      <span
                        className="retail-demand-bar"
                        aria-hidden="true"
                        style={{
                          width: `${(product.gross_units / maximum) * 100}%`,
                        }}
                      />
                      {product.gross_units}
                    </td>
                    <td>{product.returned_units}</td>
                    <td>{product.net_units}</td>
                    <td>{money(product.net_sales_minor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p>
          No historical retail slice is imported yet. Use the repository’s
          preparation script with the official workbook; synthetic arithmetic
          fixtures are not UCI observations.
        </p>
      )}
    </section>
  );
}
