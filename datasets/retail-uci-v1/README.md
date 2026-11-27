# Historical retail slice contract — source download pending

No UCI observation files are present yet: the official source host is blocked. Unit tests use explicitly synthetic arithmetic fixtures. Obtain the workbook only from the official [UCI Online Retail II page](https://archive.ics.uci.edu/dataset/502/online+retail+ii), verify its CC BY 4.0 license and creator/donor credit, then run `python scripts/prepare_uci_retail.py <online_retail_II.xlsx> --limit 250`. Keep the generated `provenance.json` with source/output hashes and exclusion counts. Do not distribute incomplete attribution.

| Field | Meaning |
| --- | --- |
| `record_id` | Stable hash of source workbook hash, worksheet and row; unique per slice. |
| `invoice_id` | Source invoice, preserving `C` cancellation marker. |
| `stock_code`, `description` | Source product identity and description. |
| `quantity` | Signed nonzero integer; negative C-invoice quantity is cancellation; other negatives are adjustments. |
| `unit_price_minor` | Positive integer GBP pence, converted exactly from source price. |
| `invoiced_at` | ISO source timestamp; timezone unspecified, no invented UTC conversion. |
| `country` | Source country; explicit unspecified label if absent. |
| `source_row`, `source_sheet` | Original worksheet row and XML sheet identifier. |

JSON is an array of these objects; CSV has these header fields. The importer accepts 1–1000 rows, at most 1 MiB. Customer IDs are omitted. Zero/negative prices, fractional/zero quantities and incomplete product identity are excluded and counted during preparation. Negative sales are not discarded. Product gross demand is ranked by positive units; cancellations and other adjustments are separately reported, not automatically matched to a particular original invoice.

Net sales = sum(signed quantity × GBP pence). Gross excludes negative quantities; cancellations are reported as a positive deduction; other adjustments retain their negative sign. No currency conversion, current-market forecast or claim about the fictional startup's earned revenue follows from these historical observations. Sampling deliberately includes negative quantities and is not representative of the entire dataset.
