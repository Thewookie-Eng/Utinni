#!/usr/bin/env python3
"""
Validator for the Utinni address-table pipeline.

Diffs two address snapshots (YAML files) and reports drift, grouped by
status:

    unchanged  -- same symbol, same original_addr, same kind/signature
    shifted    -- same symbol, different original_addr
    modified   -- same symbol & address, but kind or signature changed
    removed    -- symbol present in baseline but missing from current
    added      -- symbol present in current but missing from baseline

Symbols are matched by their fully-qualified `symbol` field; the `name`
alone is ambiguous (e.g., many entries called `ctor` or `alter` in
different namespaces).

Typical uses:

  Compare a BG snapshot against the committed original:
      python3 tools/addresses/validate.py --against snapshots/bg.yaml

  Compare any two snapshots explicitly:
      python3 tools/addresses/validate.py \\
          --baseline snapshots/before.yaml --current snapshots/after.yaml

  Sanity check (should report 275 unchanged, 0 of everything else):
      python3 tools/addresses/validate.py \\
          --against tools/addresses/addresses.yaml

Exit codes:
  0 -- nothing concerning (only `unchanged` and/or `added`)
  1 -- drift detected (shifted, modified, or removed)
  2 -- argument error or input file missing

Pass --allow-drift to always exit 0 for advisory CI checks.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from codegen import read_entries  # noqa: E402


def entry_key(e):
    """Identity used to match entries across snapshots.

    Symbol alone is ambiguous for synthetic entries (nop/read/write all
    share a generic symbol like `utinni::<read>`); name disambiguates
    within them (it contains the address). For named bindings the
    symbol already contains the name as its suffix, so adding name is
    redundant but harmless.
    """
    return (e['symbol'], e['name'])


def index_by_key(entries):
    out = {}
    for e in entries:
        out[entry_key(e)] = e
    return out


def compare(baseline_entries, current_entries):
    base = index_by_key(baseline_entries)
    curr = index_by_key(current_entries)
    base_syms = set(base)
    curr_syms = set(curr)

    buckets = {
        'unchanged': [],
        'shifted': [],
        'modified': [],
        'removed': [],
        'added': [],
    }

    for key in sorted(base_syms & curr_syms):
        sym = '::'.join(filter(None, key)) if key[1] not in key[0] else key[0]
        b, c = base[key], curr[key]
        if b['original_addr'].lower() != c['original_addr'].lower():
            buckets['shifted'].append((sym, b, c))
        elif any(b.get(k, '') != c.get(k, '') for k in ('kind', 'signature')):
            buckets['modified'].append((sym, b, c))
        else:
            buckets['unchanged'].append((sym, b, c))

    for key in sorted(base_syms - curr_syms):
        e = base[key]
        label = e['symbol'] if e['name'] in e['symbol'] else f"{e['symbol']}::{e['name']}"
        buckets['removed'].append((label, e, None))
    for key in sorted(curr_syms - base_syms):
        e = curr[key]
        label = e['symbol'] if e['name'] in e['symbol'] else f"{e['symbol']}::{e['name']}"
        buckets['added'].append((label, None, e))

    return buckets


def print_report(buckets, baseline_label: str, current_label: str):
    total = sum(len(v) for v in buckets.values())
    print(f"Baseline:  {baseline_label}")
    print(f"Current:   {current_label}")
    print(f"Compared:  {total} symbols (union of both)")
    print()
    print(f"  unchanged  {len(buckets['unchanged']):>4}")
    print(f"  shifted    {len(buckets['shifted']):>4}")
    print(f"  modified   {len(buckets['modified']):>4}")
    print(f"  removed    {len(buckets['removed']):>4}")
    print(f"  added      {len(buckets['added']):>4}")

    if buckets['shifted']:
        print()
        print("Shifted (address differs):")
        for sym, b, c in buckets['shifted']:
            print(f"  {sym}")
            print(f"      {b['original_addr']} -> {c['original_addr']}")
            if b.get('source') != c.get('source'):
                print(f"      source: {b.get('source','?')} -> {c.get('source','?')}")

    if buckets['modified']:
        print()
        print("Modified (kind or signature differs):")
        for sym, b, c in buckets['modified']:
            print(f"  {sym}  @ {c['original_addr']}")
            if b.get('kind') != c.get('kind'):
                print(f"      kind: {b.get('kind')} -> {c.get('kind')}")
            if b.get('signature') != c.get('signature'):
                print(f"      signature changed")

    if buckets['removed']:
        print()
        print(f"Removed ({len(buckets['removed'])} in baseline but not current):")
        for sym, b, _ in buckets['removed'][:20]:
            print(f"  {sym}  was @ {b['original_addr']}")
        if len(buckets['removed']) > 20:
            print(f"  ... and {len(buckets['removed']) - 20} more")

    if buckets['added']:
        print()
        print(f"Added ({len(buckets['added'])} in current but not baseline):")
        for sym, _, c in buckets['added'][:20]:
            print(f"  {sym}  @ {c['original_addr']}")
        if len(buckets['added']) > 20:
            print(f"  ... and {len(buckets['added']) - 20} more")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.strip().split('\n')[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See module docstring for full usage examples.",
    )
    parser.add_argument('--baseline', type=Path,
                        help="Baseline YAML (default: tools/addresses/addresses.yaml)")
    parser.add_argument('--current', type=Path,
                        help="Current YAML to compare against baseline.")
    parser.add_argument('--against', type=Path,
                        help="Shorthand for --current; treats default baseline as baseline.")
    parser.add_argument('--allow-drift', action='store_true',
                        help="Always exit 0; useful for advisory CI checks.")
    args = parser.parse_args()

    if args.current and args.against:
        print("ERROR: pass --current OR --against, not both.", file=sys.stderr)
        return 2

    current_path = args.current or args.against
    if not current_path:
        print("ERROR: must provide --against <FILE> or --current <FILE>.\n"
              "       (See --help for usage.)", file=sys.stderr)
        return 2

    baseline_path = args.baseline or Path('tools/addresses/addresses.yaml')

    for p, label in [(baseline_path, 'baseline'), (current_path, 'current')]:
        if not p.is_file():
            print(f"ERROR: {label} not found: {p}", file=sys.stderr)
            return 2

    baseline_entries = read_entries(baseline_path)
    current_entries = read_entries(current_path)
    buckets = compare(baseline_entries, current_entries)
    print_report(buckets, str(baseline_path), str(current_path))

    concerning = (len(buckets['shifted'])
                  + len(buckets['modified'])
                  + len(buckets['removed']))
    if concerning and not args.allow_drift:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
