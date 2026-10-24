"""Run a deterministic offline demonstration; writes JSON to stdout only."""
import json
from pathlib import Path
from .email import EmailPlanner, approval_digest
from .amazon import collect_orders
from .fulfillment import Fulfillment
from .erp import reconcile


def run() -> dict:
    fixture = json.loads((Path(__file__).parents[1] / 'fixtures/scenario.json').read_text())
    planner = EmailPlanner(suppressed={'opted-out@example.invalid'})
    decisions = [{'contact': row['id'], 'decision': planner.plan(row, approval_digest(row), n * 120)}
                 for n, row in enumerate(fixture['contacts'])]
    orders = collect_orders(lambda token: fixture['pages'][token or 'first'])
    flow = Fulfillment(orders['orders'][0]['id'], complete=orders['complete'])
    for event in ['approve', 'label', 'message', 'confirm']:
        flow.advance(event)
    return {'mode': 'offline_dry_run', 'external_operations': 0,
            'email': decisions, 'amazon': orders,
            'fulfillment': {'state': flow.state, 'audit': flow.audit},
            'erp': reconcile(fixture['transactions'], complete=False)}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, ensure_ascii=False))
