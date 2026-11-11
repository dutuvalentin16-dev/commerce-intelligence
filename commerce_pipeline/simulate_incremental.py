"""Write deterministic synthetic baseline, change batch and expected final CSVs."""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from commerce_pipeline.generate_sample_data import generate, write_csv


def simulate(output: Path) -> None:
    final = generate()
    first, new = final['orders'][0], final['orders'][-1]
    baseline = deepcopy(final)
    baseline['orders'] = baseline['orders'][:-1]
    baseline['order_items'] = [i for i in baseline['order_items'] if i['order_id'] != new['order_id']]
    first['status'] = 'paid'
    old_items = [i for i in final['order_items'] if i['order_id'] == first['order_id']]
    replacement = [{**old_items[0], 'quantity': 5, 'unit_price': '100.00'},
                   {**old_items[0], 'order_item_id': 90001, 'quantity': 1, 'unit_price': '25.00'}]
    final['order_items'] = [i for i in final['order_items'] if i['order_id'] != first['order_id']] + replacement
    batch = {name: [] for name in final}
    batch['orders'] = [first, new]
    batch['order_items'] = [i for i in final['order_items'] if i['order_id'] in (first['order_id'], new['order_id'])]
    for name, rows in [('baseline', baseline), ('batch', batch), ('expected', final)]:
        write_csv(rows, output / name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/incremental'))
    simulate(parser.parse_args().output)


if __name__ == '__main__':
    main()
