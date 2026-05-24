#!/usr/bin/env python3
"""
Bootstrap extractor for the Utinni address-table pipeline.

Scans UtinniCore source files for hardcoded SWG client addresses and
emits a YAML "phone book" -- the initial source of truth for the
address-table pipeline.

Detects five patterns:
  1. Function-pointer bindings:    pFoo name = (pFoo)0xADDR;
  2. Inline NOP patches:           memory::nopAddress(0xADDR, count);
  3. Static data reads:            memory::read<T>(0xADDR);
  4. Static data writes:           memory::write<T>(0xADDR, value);
  5. Named address constants:      constexpr swgptr name = 0xADDR;

The most recent `namespace foo::bar` directive is treated as the active
namespace for symbol qualification. This codebase uses flat per-file
namespace blocks, so the heuristic is accurate in practice.

Usage:
    python3 tools/addresses/bootstrap_extractor.py
    python3 tools/addresses/bootstrap_extractor.py --root UtinniCore --output tools/addresses/addresses.yaml
"""

import argparse
import re
import sys
from pathlib import Path

# pFoo varname = (pFoo)0xADDR;
ADDR_BIND = re.compile(
    r'^\s*(?:static\s+|extern\s+)?'
    r'(p[A-Z][A-Za-z0-9_]*)\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'\(\s*\1\s*\)\s*'
    r'(0x[0-9A-Fa-f]{6,8})\s*;'
)

# using pFoo = signature;  (tolerates trailing // or /* comments)
USING_TYPEDEF = re.compile(
    r'^\s*using\s+(p[A-Z][A-Za-z0-9_]*)\s*=\s*(.+?)\s*;'
)

# memory::nopAddress(0xADDR, N);
NOP_PATCH = re.compile(
    r'memory::nopAddress\s*\(\s*(0x[0-9A-Fa-f]{6,8})\s*,\s*(\d+)\s*\)'
)

# memory::read<T>(0xADDR ...) -- T captured for the signature field
MEMORY_READ = re.compile(
    r'memory::read\s*<\s*([^>]+?)\s*>\s*\(\s*(0x[0-9A-Fa-f]{6,8})\s*[,)]'
)

# memory::write<T>(0xADDR, ...)
MEMORY_WRITE = re.compile(
    r'memory::write\s*<\s*([^>]+?)\s*>\s*\(\s*(0x[0-9A-Fa-f]{6,8})\s*,'
)

# constexpr swgptr name = 0xADDR;  (optionally `static constexpr ...`)
ADDR_CONSTANT = re.compile(
    r'^\s*(?:static\s+)?constexpr\s+swgptr\s+'
    r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'(0x[0-9A-Fa-f]{6,8})\s*;'
)

# namespace foo::bar  (tolerates trailing { and/or // or /* comments)
NAMESPACE_OPEN = re.compile(
    r'^\s*namespace\s+([A-Za-z_][A-Za-z0-9_:]*)\b'
)


def category_from_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == 'swg':
        return parts[1]
    if len(parts) >= 2:
        return parts[0]
    return 'misc'


def scan_file(path: Path, root: Path) -> list:
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError as e:
        print(f"WARN: cannot read {path}: {e}", file=sys.stderr)
        return []

    entries = []
    typedefs = {}
    rel_display = path.relative_to(root.parent).as_posix()
    category = category_from_path(path, root)
    current_ns = ''

    for lineno, line in enumerate(lines, start=1):
        m = NAMESPACE_OPEN.match(line)
        if m:
            current_ns = m.group(1)
            continue

        m = USING_TYPEDEF.match(line)
        if m:
            typedefs[m.group(1)] = m.group(2).strip()
            continue

        m = ADDR_BIND.match(line)
        if m:
            ptype, name, addr = m.group(1), m.group(2), m.group(3)
            symbol = f"{current_ns}::{name}" if current_ns else name
            entries.append({
                'name': name,
                'symbol': symbol,
                'signature': typedefs.get(ptype, '<unknown>'),
                'category': category,
                'original_addr': '0x' + addr[2:].upper().zfill(8),
                'source': f"{rel_display}:{lineno}",
                'kind': 'function_pointer',
                'confidence': 'unknown',
            })
            continue

        m = ADDR_CONSTANT.match(line)
        if m:
            name, addr = m.group(1), m.group(2)
            symbol = f"{current_ns}::{name}" if current_ns else name
            entries.append({
                'name': name,
                'symbol': symbol,
                'signature': 'swgptr',
                'category': category,
                'original_addr': '0x' + addr[2:].upper().zfill(8),
                'source': f"{rel_display}:{lineno}",
                'kind': 'address_constant',
                'confidence': 'unknown',
            })
            continue

        for m in NOP_PATCH.finditer(line):
            addr, count = m.group(1), m.group(2)
            normalized = '0x' + addr[2:].upper().zfill(8)
            entries.append({
                'name': f"nop_{normalized.lower()}",
                'symbol': f"{current_ns}::<nop>" if current_ns else '<nop>',
                'signature': '<inline NOP patch>',
                'category': category,
                'original_addr': normalized,
                'source': f"{rel_display}:{lineno}",
                'kind': 'nop_patch',
                'confidence': 'unknown',
                'nop_bytes': int(count),
            })

        for m in MEMORY_READ.finditer(line):
            t, addr = m.group(1).strip(), m.group(2)
            normalized = '0x' + addr[2:].upper().zfill(8)
            entries.append({
                'name': f"read_{normalized.lower()}",
                'symbol': f"{current_ns}::<read>" if current_ns else '<read>',
                'signature': f"read<{t}>",
                'category': category,
                'original_addr': normalized,
                'source': f"{rel_display}:{lineno}",
                'kind': 'data_read',
                'confidence': 'unknown',
            })

        for m in MEMORY_WRITE.finditer(line):
            t, addr = m.group(1).strip(), m.group(2)
            normalized = '0x' + addr[2:].upper().zfill(8)
            entries.append({
                'name': f"write_{normalized.lower()}",
                'symbol': f"{current_ns}::<write>" if current_ns else '<write>',
                'signature': f"write<{t}>",
                'category': category,
                'original_addr': normalized,
                'source': f"{rel_display}:{lineno}",
                'kind': 'data_write',
                'confidence': 'unknown',
            })

    return entries


# YAML chars that force quoting in a scalar value
_YAML_RESERVED = set(':#*&!|>%@`')


def yaml_scalar(s: str) -> str:
    if not s:
        return '""'
    if any(c in _YAML_RESERVED for c in s) or s.startswith('-') or s.startswith('?') \
            or s.startswith('[') or s.startswith('{') or s.startswith('<') \
            or s != s.strip():
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return s


def emit_yaml(entries, out_path: Path) -> None:
    lines = [
        '# Auto-generated by tools/addresses/bootstrap_extractor.py',
        '# DO NOT edit this file by hand for routine updates -- rerun the extractor.',
        '# Manually curated fields (anchor, bg_addr, notes) can be merged in once',
        '# the schema is extended; for now this captures only what is extractable',
        '# from source.',
        '#',
        '# Schema (v1):',
        '#   name           short identifier (variable name from source)',
        '#   symbol         fully-qualified name (namespace::name)',
        '#   signature      typedef signature, or "<unknown>"',
        '#   category       subsystem (camera, object, scene, ...)',
        '#   original_addr  address as seen in the original SWG client (0xXXXXXXXX)',
        '#   source         file:line where the binding lives',
        '#   kind           function_pointer | nop_patch | data_read | data_write | address_constant',
        '#   confidence     unknown | inferred | verified',
        '#   nop_bytes      (nop_patch only) number of NOP bytes written',
        '',
    ]
    for e in entries:
        lines.append(f"- name: {yaml_scalar(e['name'])}")
        lines.append(f"  symbol: {yaml_scalar(e['symbol'])}")
        lines.append(f"  signature: {yaml_scalar(e['signature'])}")
        lines.append(f"  category: {yaml_scalar(e['category'])}")
        lines.append(f"  original_addr: {e['original_addr']}")
        lines.append(f"  source: {yaml_scalar(e['source'])}")
        lines.append(f"  kind: {e['kind']}")
        lines.append(f"  confidence: {e['confidence']}")
        if 'nop_bytes' in e:
            lines.append(f"  nop_bytes: {e['nop_bytes']}")
        lines.append('')
    out_path.write_text('\n'.join(lines), encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().split('\n')[0])
    parser.add_argument('--root', type=Path, default=Path('UtinniCore'),
                        help='Source root to scan (default: UtinniCore)')
    parser.add_argument('--output', type=Path,
                        default=Path('tools/addresses/addresses.yaml'),
                        help='Output YAML path')
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: {root} not found", file=sys.stderr)
        return 1

    excluded = {'external', 'imgui'}
    files = sorted(
        p for ext in ('*.cpp', '*.h')
        for p in root.rglob(ext)
        if not any(part in excluded for part in p.parts)
    )

    all_entries = []
    for f in files:
        all_entries.extend(scan_file(f, root))

    all_entries.sort(key=lambda e: (e['category'], e['source']))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    emit_yaml(all_entries, args.output)

    by_kind = {}
    by_category = {}
    unknown_sigs = 0
    for e in all_entries:
        by_kind[e['kind']] = by_kind.get(e['kind'], 0) + 1
        by_category[e['category']] = by_category.get(e['category'], 0) + 1
        if e['signature'] == '<unknown>':
            unknown_sigs += 1

    print(f"Scanned {len(files)} files under {root}")
    print(f"Wrote {len(all_entries)} entries to {args.output}")
    print()
    print("By kind:")
    for k, n in sorted(by_kind.items()):
        print(f"  {k:>17}: {n}")
    print()
    print("By category:")
    for c, n in sorted(by_category.items(), key=lambda kv: -kv[1]):
        print(f"  {c:>17}: {n}")
    if unknown_sigs:
        print()
        print(f"NOTE: {unknown_sigs} entries have signature=<unknown>")
        print("      (typedef likely defined in a header the scanner didn't see)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
