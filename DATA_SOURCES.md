# Data sources and transformation ledger

## UCI Online Retail II — requested, download pending
- Official dataset: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- Publisher: UCI Machine Learning Repository; original donor/creator attribution will be recorded from the official metadata when accessible.
- Published license requested by the owner: Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/ . Official metadata/license verification and original-file hash are pending network access; do not represent fixture rows as downloaded UCI data.
- Current environment rejects archive.ics.uci.edu with HTTP 403. No official transaction rows have yet been downloaded in this change.
- Planned transformations: deterministic bounded slice with original sheet/row references; ISO timestamps; prices converted exactly to integer GBP pence; signed quantities/cancellation invoice markers retained; customer identifiers omitted; invalid quantities/prices quarantined and counted. Historical UK retailer observations are not this startup's real sales or a current market forecast. No GBP/USD/PKR conversion is assumed.

## Fictional startup and conversation examples
- Source: project-authored synthetic records and examples, clearly marked synthetic; no real company outcomes or applicant records.
- Existing sample: datasets/product-launch-v1 (synthetic USD cents). The new shared-workflow demo extends this purpose without relabelling historical transactions as synthetic.
- New startup: datasets/shared-launch-v2 (USD cents), authored fictional budget, product catalog, brand, staffing capacity and 5 December 2026 deadline. No fabricated real sales or results. JSON/CSV share the existing validated dataset schema.
- New examples: datasets/agent-conversations-v1/examples.json, 40 project-authored synthetic conversations; six development and two held-out per agent. No third-party conversation text copied. Held-out answers are never loaded as prompting examples.
- Current-service fixture evaluation on 27 November: 42 user turns across 40 examples returned 200; 25 structured fallbacks and 17 structured-record responses; no successful live model responses or model-accuracy score. Fixture prerequisites and limits are recorded in the delivery report. No fine-tuning performed.

## Optional sources not imported
- World Bank: https://datacatalog.worldbank.org/public-licenses . No indicator/country/year series imported; specific dataset exceptions must be checked before use.
- OpenAssistant: https://huggingface.co/datasets/OpenAssistant/oasst1 . No conversation text copied; no Apache-licensed examples are claimed to have been reviewed/imported.

## UI references supplied by owner
Two WhatsApp ZIPs contain seven screenshots of side-navigation patterns and dashboard layouts. Used as visual inspiration only. No source code, dataset, attribution-free asset or instructions were extracted for execution. Native sign-in and the established purple/beige/light/dark theme remain.
