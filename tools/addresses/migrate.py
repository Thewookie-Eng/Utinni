#!/usr/bin/env python3
"""
Source migration step of the Utinni address-table pipeline.

For every `function_pointer` entry in addresses.yaml, rewrites the
binding's hex literal to use the codegen constant:

    pAlter alter = (pAlter)0x00788740;
to:
    pAlter alter = (pAlter)addresses::swg::gameCamera::alter;

Also adds `#include "generated/addresses_generated.h"` to UtinniCore/utinni.h
if not already present (one include flows transitively to all source
files that include utinni.h, which is the bulk of UtinniCore).

Idempotent: running twice produces no further changes -- the bind-pattern
regex requires `0x...` on the right side, so already-migrated lines are
skipped automatically.

This step only migrates `kind: function_pointer`. `address_constant`
entries (`constexpr swgptr ... = 0x...;`) remain as local declarations;
`nop_patch`, `data_read`, and `data_write` call sites stay inline.

Usage:
    python3 tools/addresses/migrate.py
    python3 tools/addresses/migrate.py --dry-run
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Local imports rely on running from repo root.
sys.path.insert(0, str(Path(__file__).parent))
from codegen import read_entries  # noqa: E402


# pFoo name = (pFoo)0xADDR;
BIND_RE = re.compile(
    r'(^\s*(?:static\s+|extern\s+)?'
    r'p[A-Z][A-Za-z0-9_]*\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'\(\s*p[A-Z][A-Za-z0-9_]*\s*\)\s*)'
    r'(0x[0-9A-Fa-f]{6,8})(\s*;)',
)


INCLUDE_LINE = '#include "generated/addresses_generated.h"'
UTINNI_H = Path('UtinniCore/utinni.h')


def migrate_file(path: Path, entries_for_file: list, dry_run: bool) -> tuple:
    """Return (rewritten_count, skipped_count, miss_count)."""
    try:
        lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    except OSError as e:
        print(f"WARN: cannot read {path}: {e}", file=sys.stderr)
        return (0, 0, len(entries_for_file))

    # Build a map: (variable_name, addr_as_int) -> entry. Comparing as ints
    # avoids zero-padding mismatches between YAML (always 8 hex chars) and
    # source (which may omit leading zeros, e.g. 0xAA4900).
    targets = {}
    for e in entries_for_file:
        key = (e['name'], int(e['original_addr'], 16))
        targets[key] = e

    rewritten = 0
    skipped_already = 0
    matched_keys = set()

    for i, line in enumerate(lines):
        # Strip line ending for matching but keep it for output.
        stripped = line.rstrip('\r\n')
        line_end = line[len(stripped):]
        m = BIND_RE.match(stripped)
        if not m:
            continue
        prefix, var, addr, suffix = m.group(1), m.group(2), m.group(3), m.group(4)
        key = (var, int(addr, 16))
        if key not in targets:
            continue
        entry = targets[key]
        symbol = entry['symbol']
        new_rhs = f"addresses::{symbol}"
        new_line = f"{prefix}{new_rhs}{suffix}{line_end}"
        if new_line == line:
            skipped_already += 1
        else:
            lines[i] = new_line
            rewritten += 1
        matched_keys.add(key)

    missed = len(targets) - len(matched_keys)
    if missed and rewritten:
        # Only report misses for files we did rewrite -- otherwise it's
        # likely an already-migrated file and the misses are because the
        # hex literal is gone.
        missing_names = [e['name'] for k, e in targets.items() if k not in matched_keys]
        print(f"  NOTE: {path}: did not find {missed} expected bindings ({', '.join(missing_names[:3])}{'...' if len(missing_names) > 3 else ''})")

    if rewritten and not dry_run:
        path.write_text(''.join(lines), encoding='utf-8')

    return (rewritten, skipped_already, missed)


def ensure_include(dry_run: bool) -> bool:
    """Add the generated-header include to utinni.h if missing. Returns True if file changed."""
    if not UTINNI_H.is_file():
        print(f"WARN: {UTINNI_H} not found; skipping include insertion.", file=sys.stderr)
        return False
    text = UTINNI_H.read_text(encoding='utf-8')
    if INCLUDE_LINE in text:
        return False
    # Insert after the last #include line.
    lines = text.splitlines(keepends=True)
    last_include = -1
    for i, line in enumerate(lines):
        if line.lstrip().startswith('#include'):
            last_include = i
    if last_include < 0:
        print(f"WARN: {UTINNI_H} has no existing #include lines; inserting at top.", file=sys.stderr)
        lines.insert(0, INCLUDE_LINE + '\n')
    else:
        # Preserve the line ending style of the surrounding file
        eol = '\r\n' if lines[last_include].endswith('\r\n') else '\n'
        lines.insert(last_include + 1, INCLUDE_LINE + eol)
    if not dry_run:
        UTINNI_H.write_text(''.join(lines), encoding='utf-8')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().split('\n')[0])
    parser.add_argument('--input', type=Path,
                        default=Path('tools/addresses/addresses.yaml'))
    parser.add_argument('--dry-run', action='store_true',
                        help="Report what would change without writing files.")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        return 1

    entries = read_entries(args.input)
    fp_entries = [e for e in entries if e.get('kind') == 'function_pointer']

    by_file = defaultdict(list)
    for e in fp_entries:
        src = e['source'].split(':')[0]  # strip ":line"
        by_file[Path(src)].append(e)

    total_rewritten = 0
    total_skipped = 0
    total_missed = 0
    files_changed = 0

    for path in sorted(by_file):
        if not path.is_file():
            print(f"WARN: {path} not found; skipping.", file=sys.stderr)
            continue
        rewritten, skipped, missed = migrate_file(path, by_file[path], args.dry_run)
        total_rewritten += rewritten
        total_skipped += skipped
        total_missed += missed
        if rewritten:
            files_changed += 1

    include_changed = ensure_include(args.dry_run)

    mode = "DRY RUN " if args.dry_run else ""
    print()
    print(f"{mode}Migration summary:")
    print(f"  Source files visited: {len(by_file)}")
    print(f"  Files rewritten:      {files_changed}")
    print(f"  Bindings rewritten:   {total_rewritten}")
    print(f"  Already migrated:     {total_skipped}")
    if total_missed:
        print(f"  Unmatched (review):   {total_missed}")
    print(f"  utinni.h include:     {'added' if include_changed else 'already present'}")
    if args.dry_run:
        print("  (dry-run: no files written)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
