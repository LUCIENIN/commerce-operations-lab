# Architecture and operating boundaries

The public version is a small Python package with four explicit responsibilities. It uses only the standard library and reads one fixed synthetic fixture. It writes JSON to stdout. No module loads environment variables, credential stores, production configuration, or operational ledgers.

| Module | Input → output | Decision boundary |
|---|---|---|
| `email.py` | Synthetic consent record + reviewed digest + demo clock → decision | Suppression and uncertainty override consent; consent must have evidence, matching scope and an inclusive validity window; approval binds the whole record |
| `amazon.py` | Callable returning synthetic pages → orders + completeness | Repeated tokens, budget exhaustion, invalid records and permission errors never imply a complete query |
| `fulfillment.py` | Demo order + event → simulated state + audit | Complete order and approval before label; message before confirmation; repeat events have no additional effect |
| `erp.py` | Synthetic transaction references → evidence groups | Exact settlement identity only; absence remains unassigned; no inferred profit or causal pairing |

Email plans reserve in-memory daily budget and spacing together; nothing is submitted. The example generates its approval digest automatically to make a deterministic demo. A real reviewer service would have to authenticate a reviewer, store approvals separately, support revocation, and revalidate immediately before an operation. Hashing alone cannot provide those guarantees.

Fulfillment milestones represent event order, not a carrier acceptance or delivery claim. `confirmation_simulated` never means Amazon accepted a shipment. Uncertainty blocks further progress and requires external human reconciliation; no automatic retry is provided. No production recovery procedure is executed here.

The read adapter accepts a callable for testing. The included callable is an in-memory fixture lookup. Adding any real adapter would change the threat model and requires a separately reviewed system, not a configuration toggle in this demo.

The ERP sample illustrates evidence discipline rather than full accounting. A refund and recovery in the same settlement are grouped but not declared causally linked. Currency conversion, taxes, freight, margin, inventory and procurement are outside this implementation.
