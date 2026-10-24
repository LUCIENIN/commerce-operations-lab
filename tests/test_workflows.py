import copy
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from ops_lab.email import EmailPlanner, approval_digest
from ops_lab.amazon import collect_orders
from ops_lab.fulfillment import Fulfillment
from ops_lab.erp import reconcile
from ops_lab.demo import run

FIXTURE = json.loads((Path(__file__).parents[1] / 'fixtures/scenario.json').read_text())


class EmailTests(unittest.TestCase):
    def setUp(self):
        self.row = copy.deepcopy(FIXTURE['contacts'][0])
        self.approval = approval_digest(self.row)
        self.planner = EmailPlanner()

    def test_consent_is_required_even_for_public_address(self):
        self.row['consent']['status'] = 'public_address_only'
        self.assertEqual(self.planner.plan(self.row, approval_digest(self.row), 0), 'held:consent')

    def test_approval_is_bound_to_content(self):
        self.row['template'] = 'changed'
        self.assertEqual(self.planner.plan(self.row, self.approval, 0), 'held:approval')

    def test_suppression_wins_over_approval(self):
        self.planner.suppressed.add(self.row['email'])
        self.assertEqual(self.planner.plan(self.row, self.approval, 0), 'held:suppressed')

    def test_consent_scope_and_validity(self):
        for key, value in [('scope', 'different'), ('evidence', ''), ('valid_until', -1), ('valid_from', 1)]:
            row = copy.deepcopy(self.row)
            row['consent'][key] = value
            self.assertEqual(self.planner.plan(row, approval_digest(row), 0), 'held:consent')

    def test_consent_endpoints_are_inclusive(self):
        for at in [0, 86400]:
            self.assertEqual(EmailPlanner().plan(self.row, self.approval, at), 'dry_run:planned')
        self.assertEqual(EmailPlanner().plan(self.row, self.approval, 86401), 'held:consent')

    def test_unknown_address_domain_rejected(self):
        self.row['email'] = 'invalid-address'
        self.assertEqual(self.planner.plan(self.row, approval_digest(self.row), 0), 'held:fixture_only')

    def test_throttle_daily_limit_and_replay(self):
        self.assertEqual(self.planner.plan(self.row, self.approval, 0), 'dry_run:planned')
        self.assertEqual(self.planner.plan(self.row, self.approval, 120), 'held:duplicate')
        other = copy.deepcopy(self.row)
        other.update(id='contact-new', email='next@example.invalid')
        self.assertEqual(self.planner.plan(other, approval_digest(other), 119), 'held:spacing')
        self.assertEqual(self.planner.plan(other, approval_digest(other), 120), 'dry_run:planned')
        self.planner.daily[0] = 200
        other.update(id='contact-third', email='third@example.invalid')
        self.assertEqual(self.planner.plan(other, approval_digest(other), 240), 'held:daily_cap')

    def test_uncertain_never_automatically_retries(self):
        self.planner.uncertain.add(self.row['email'])
        self.assertEqual(self.planner.plan(self.row, self.approval, 0), 'held:manual_review')


class AmazonTests(unittest.TestCase):
    def test_pages_deduplicate_and_report_completeness(self):
        pages = {None: {'orders': [{'id': 'demo-order-a'}], 'next': 'p2'},
                 'p2': {'orders': [{'id': 'demo-order-a'}, {'id': 'demo-order-b'}]}}
        result = collect_orders(pages.__getitem__)
        self.assertTrue(result['complete'])
        self.assertEqual(len(result['orders']), 2)

    def test_cycle_and_page_budget_are_incomplete(self):
        fetch = lambda token: {'orders': [], 'next': 'repeat'}
        self.assertEqual(collect_orders(fetch)['error'], 'pagination_cycle')
        self.assertEqual(collect_orders(fetch, max_pages=1)['error'], 'page_budget')

    def test_invalid_page_preserves_prior_orders_and_incompleteness(self):
        for invalid in [{'orders': 'invalid'}, {'orders': [{'id': None}]}]:
            pages = {None: {'orders': [{'id': 'demo-order-a'}], 'next': 'p2'}, 'p2': invalid}
            result = collect_orders(pages.__getitem__)
            self.assertFalse(result['complete'])
            self.assertIsNotNone(result['error'])
            self.assertEqual(result['orders'], [{'id': 'demo-order-a'}])

    def test_authorization_failure_stops(self):
        calls = []
        def fetch(token):
            calls.append(token)
            raise PermissionError('denied')
        self.assertEqual(collect_orders(fetch)['error'], 'permission')
        self.assertEqual(len(calls), 1)


class FulfillmentTests(unittest.TestCase):
    def test_ordered_gates_and_idempotency(self):
        flow = Fulfillment('demo-order-a')
        self.assertEqual(flow.advance('confirm'), 'held:invalid_transition')
        for event in ['approve', 'label', 'message', 'confirm']:
            self.assertEqual(flow.advance(event), 'simulated:applied')
            self.assertEqual(flow.advance(event), 'simulated:already_applied')
        self.assertEqual(flow.state, 'confirmation_simulated')
        self.assertEqual(len(flow.audit), 4)

    def test_incomplete_order_and_uncertainty_block(self):
        flow = Fulfillment('demo-order-a', complete=False)
        self.assertEqual(flow.advance('approve'), 'held:incomplete_order')
        flow.complete = True
        flow.uncertain = True
        self.assertEqual(flow.advance('approve'), 'held:manual_review')


class ERPTests(unittest.TestCase):
    def test_exact_settlement_only_and_unknown_not_zero(self):
        rows = [{'id': 'demo-tx-a', 'settlement': 'demo-set-a', 'kind': 'refund'},
                {'id': 'demo-tx-b', 'settlement': 'demo-set-a', 'kind': 'recovery'},
                {'id': 'demo-tx-c', 'kind': 'refund'}]
        result = reconcile(rows, complete=False)
        self.assertEqual(len(result['groups']['demo-set-a']), 2)
        self.assertEqual(result['unassigned'], ['demo-tx-c'])
        self.assertIsNone(result['profit'])
        self.assertFalse(result['complete'])


class IntegrationTests(unittest.TestCase):
    def test_full_demo_runs_with_network_and_processes_denied(self):
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), \
             patch('subprocess.Popen', side_effect=AssertionError('process forbidden')):
            result = run()
        self.assertEqual(result['mode'], 'offline_dry_run')
        self.assertEqual(result['external_operations'], 0)
        self.assertEqual(result['fulfillment']['state'], 'confirmation_simulated')
        self.assertIn('held:consent', [x['decision'] for x in result['email']])
        self.assertEqual(result, run())


if __name__ == '__main__':
    unittest.main()
