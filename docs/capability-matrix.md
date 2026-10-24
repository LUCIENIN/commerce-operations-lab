# Implementation evidence and honest scope

A local read-only inspection informed the public reconstruction. Private source locations, hashes, customer records, screenshots and knowledge-base documents are deliberately excluded. This table is a description of code inspected, not independently reproducible production evidence.

| Area | Implementation inspected | What can be claimed |
|---|---|---|
| Email | Swift batch manifest validation, approval grants, suppression and historical exclusions, throttle and daily reservation, SMTP result classification, IMAP Sent synchronization and policy regression checks | A guarded email workflow exists in local code. Public demo reconstructs selected policy concepts with stronger explicit synthetic consent requirements. No production delivery or performance measurement was executed in this task. |
| Amazon | Orders/item pagination scripts, marketplace/listing/finance queries, completeness metadata, repeated-token checks and permission stops | API collection and analysis implementation exists. Public pages are synthetic, with no credentials or live adapter. |
| Logistics | Order normalization, preservation of reviewed operational fields, label download and dispatch readiness, buyer-message preview/send and shipment-confirmation functions | Local integration code supports human-reviewed fulfillment stages. Public version only simulates stage order. |
| ERP | Web route handlers for order collection, labels, confirmation and preview; settlement grouping; existing state-merge and reconciliation tests | Local operational workbench and reconciliation tooling exist. This is not evidence of a complete autonomous ERP or certified accounting product. |
| Knowledge index | Amazon/logistics domain index and memory index used to locate relevant code | Discovery support only; private knowledge content is not published as evidence. |

No production scripts were imported or executed. Existing tests were read for behavior and privacy risks, not copied or run against operational configuration. No existing repository history was reused.

## Contribution and AI disclosure

The public project presents the user's workflow requirements and integration decisions as an engineering case study. AI assisted code generation, documentation and test creation. It would be inaccurate to describe every line as handwritten or claim the entire production system was independently authored solely from this publication. Resume language should emphasize workflow definition, integration orchestration, approval gates, verification and the reproducible demo.

## Provenance and licenses

All public Python, JSON, Markdown and CI files were newly authored for this demo. No production Swift/Python/HTML source, vendor code, templates, private text, dependencies or assets were copied. MIT covers only this newly authored material. Third-party platforms and APIs retain their own rights and terms; no SDK or platform code is redistributed. Production licensing and employer ownership are not asserted by this project.
