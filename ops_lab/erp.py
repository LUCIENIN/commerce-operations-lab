"""Settlement evidence grouping: shared group is not proof of causality."""


def reconcile(transactions: list[dict], *, complete: bool) -> dict:
    groups, unassigned = {}, []
    for row in transactions:
        settlement = row.get('settlement')
        if isinstance(settlement, str) and settlement.startswith('demo-set-'):
            groups.setdefault(settlement, []).append(row['id'])
        else:
            unassigned.append(row['id'])
    return {'groups': groups, 'unassigned': unassigned, 'complete': complete,
            'profit': None, 'basis': 'exact settlement identity; no causal pairing inferred',
            'limitation': 'No cost ledger or accounting integration; profit unknown'}
