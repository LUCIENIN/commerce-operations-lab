"""Read adapter contract demonstrated with in-memory pages only."""


def collect_orders(fetch_page, max_pages: int = 10) -> dict:
    result = {'orders': [], 'pages': 0, 'complete': False, 'error': None}
    orders, seen, token = {}, set(), None
    for _ in range(max_pages):
        try:
            page = fetch_page(token)
        except PermissionError:
            result['error'] = 'permission'
            break
        except (KeyError, ValueError):
            result['error'] = 'invalid_page'
            break
        if not isinstance(page, dict) or not isinstance(page.get('orders'), list):
            result['error'] = 'invalid_page'
            break
        if any(not isinstance(row, dict) or not isinstance(row.get('id'), str)
               or not row['id'].startswith('demo-order-') for row in page['orders']):
            result['error'] = 'invalid_order'
            break
        result['pages'] += 1
        for row in page['orders']:
            orders[row['id']] = dict(row)
        token = page.get('next')
        if token is None:
            result['complete'] = True
            break
        if not isinstance(token, str) or token in seen:
            result['error'] = 'pagination_cycle'
            break
        seen.add(token)
    else:
        result['error'] = 'page_budget'
    result['orders'] = list(orders.values())
    return result
