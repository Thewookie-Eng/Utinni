# Extract candidate anchors from each function in addresses.yaml.
# Jython 2.7 -- run inside Ghidra with the original SWG client loaded.
# Open the Script Manager (Window -> Script Manager), find this script
# under the "Utinni" category, and Run. You'll be prompted for the
# Utinni repo root; everything else is automatic.
#
# Outputs: tools/addresses/anchor_candidates.json
#
# Next step (outside Ghidra): run tools/addresses/apply_auto_anchors.py
# to score the candidates and write back into addresses.yaml.
#
#@author Utinni
#@category Utinni
#@keybinding
#@menupath
#@toolbar

from __future__ import print_function

import json
import os
import re


# ---------------------------------------------------------------------------
# Minimal YAML reader -- duplicate of codegen.read_entries, ported to Py2.
# Matches only the subset bootstrap_extractor.py emits.
# ---------------------------------------------------------------------------

_QUOTED = re.compile(r'^"((?:[^"\\]|\\.)*)"$')


def _unquote(v):
    m = _QUOTED.match(v)
    if m:
        return m.group(1).replace('\\"', '"').replace('\\\\', '\\')
    return v


def read_entries(path):
    entries = []
    current = None
    fh = open(path, 'r')
    try:
        for raw in fh.readlines():
            line = raw.rstrip()
            if not line or line.lstrip().startswith('#'):
                if not line.strip() and current is not None:
                    entries.append(current)
                    current = None
                continue
            if line.startswith('- '):
                if current is not None:
                    entries.append(current)
                current = {}
                line = line[2:]
            else:
                line = line.lstrip()
            if ':' not in line:
                continue
            key, _, value = line.partition(':')
            current[key.strip()] = _unquote(value.strip())
    finally:
        fh.close()
    if current is not None:
        entries.append(current)
    return entries


# ---------------------------------------------------------------------------
# Candidate extractors. Each returns a list of dicts shaped for the scorer.
# ---------------------------------------------------------------------------

def _count_referencing_functions(target_addr):
    """How many references total, and how many distinct functions among them."""
    funcs = set()
    n_refs = 0
    for r in getReferencesTo(target_addr):
        n_refs += 1
        from_addr = r.getFromAddress()
        if from_addr is None:
            continue
        fn = getFunctionContaining(from_addr)
        if fn is not None:
            funcs.add(fn.getEntryPoint().toString())
    return len(funcs), n_refs


def extract_string_candidates(func):
    seen = {}  # value -> True; suppresses duplicates within one function
    out = []
    listing = currentProgram.getListing()
    instr_iter = listing.getInstructions(func.getBody(), True)
    while instr_iter.hasNext():
        if monitor.isCancelled():
            break
        instr = instr_iter.next()
        for ref in instr.getReferencesFrom():
            target = ref.getToAddress()
            if target is None:
                continue
            data = getDataAt(target)
            if data is None or not data.hasStringValue():
                continue
            value = unicode(data.getValue())
            if value in seen:
                continue
            seen[value] = True
            fc, n_refs = _count_referencing_functions(target)
            out.append({
                'kind': 'string_xref',
                'value': value,
                'length': len(value),
                'occurrences': n_refs,
                'function_count': fc if fc > 0 else 1,
                'is_format_string': ('%' in value),
            })
    return out


def extract_import_pattern(func):
    """Return a single import_pattern candidate (if any imports called).

    Captures the ordered sequence of external symbols called from this
    function; the function_count is approximated by checking how many
    functions share this exact ordered import set.
    """
    imports = []
    seen_call_targets = {}
    listing = currentProgram.getListing()
    instr_iter = listing.getInstructions(func.getBody(), True)
    while instr_iter.hasNext():
        if monitor.isCancelled():
            break
        instr = instr_iter.next()
        for ref in instr.getReferencesFrom():
            if not ref.getReferenceType().isCall():
                continue
            target = ref.getToAddress()
            if target is None or target.toString() in seen_call_targets:
                continue
            seen_call_targets[target.toString()] = True
            sym = getSymbolAt(target)
            if sym is None:
                continue
            # Walk through thunks to find the real external symbol
            tgt_func = getFunctionAt(target)
            if tgt_func is not None and tgt_func.isThunk():
                thunked = tgt_func.getThunkedFunction(True)
                if thunked is not None and thunked.isExternal():
                    imports.append(thunked.getName())
                    continue
            if sym.isExternal():
                imports.append(sym.getName())
    if not imports:
        return None
    return {
        'kind': 'import_pattern',
        'value': ','.join(imports),
        'imports': imports,
        # Uniqueness across the whole binary is expensive to compute;
        # the scorer treats function_count=1 as "unique"; downstream
        # review should verify when this fires.
        'function_count': 1,
    }


def extract_byte_signature(func, n_bytes=16):
    body = func.getBody()
    start = body.getMinAddress()
    try:
        raw = getBytes(start, n_bytes)
    except Exception:
        return None
    # raw is a Java byte[] (signed). Mask to unsigned hex.
    hex_parts = []
    for b in raw:
        hex_parts.append('%02X' % (b & 0xFF))
    return {
        'kind': 'byte_signature',
        'value': ' '.join(hex_parts),
        'length': len(hex_parts),
        'wildcards': 0,
        # Byte-sig binary-wide uniqueness is expensive (memory.find()
        # across the whole binary per call). v1 punts and assumes 1;
        # the scorer's base * length factors keep the score modest.
        'function_count': 1,
    }


def extract_vtable_candidate(func):
    """If func is referenced from a vtable, capture the slot.

    Detection heuristic: any reference of type 'data' from a memory
    region named like '.rdata' that points at this function start.
    """
    entry = func.getEntryPoint()
    refs = getReferencesTo(entry)
    for r in refs:
        if not r.getReferenceType().isData():
            continue
        from_addr = r.getFromAddress()
        block = currentProgram.getMemory().getBlock(from_addr)
        if block is None:
            continue
        bname = block.getName() or ''
        if '.rdata' not in bname and 'rdata' not in bname.lower():
            continue
        # Found a data reference from rdata -- candidate vtable entry.
        # Approximate the slot index from the offset within the block,
        # divided by pointer size (4 on x86).
        offset = from_addr.subtract(block.getStart())
        return {
            'kind': 'vtable_slot',
            'value': '%s+0x%x' % (bname, offset),
            'vtable_class': '<unknown>',
            'vtable_index': int(offset / 4),
        }
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _normalize_addr(s):
    """'0x00788740' -> long(0x00788740)."""
    return long(s, 16) if s.startswith('0x') else long(s, 16)


def main():
    repo_root_obj = askDirectory("Select Utinni repo root", "Use this folder")
    repo_root = repo_root_obj.getAbsolutePath()

    yaml_path = os.path.join(repo_root, 'tools', 'addresses', 'addresses.yaml')
    out_path = os.path.join(repo_root, 'tools', 'addresses', 'anchor_candidates.json')

    if not os.path.isfile(yaml_path):
        print('ERROR: %s not found' % yaml_path)
        return

    entries = read_entries(yaml_path)
    target_entries = [e for e in entries if e.get('kind') == 'function_pointer']
    print('Loaded %d total entries; %d are function_pointer.'
          % (len(entries), len(target_entries)))

    results = {}
    no_function = []
    n_done = 0
    monitor.initialize(len(target_entries))

    for entry in target_entries:
        if monitor.isCancelled():
            print('Cancelled by user.')
            break
        sym = entry['symbol']
        addr_str = entry['original_addr']
        monitor.setMessage('Extracting %s' % sym)
        monitor.incrementProgress(1)
        n_done += 1

        try:
            addr_val = _normalize_addr(addr_str)
        except Exception as e:
            results[sym] = {'error': 'cannot parse address %r: %s' % (addr_str, e)}
            continue

        addr = toAddr(addr_val)
        func = getFunctionAt(addr)
        if func is None:
            no_function.append((sym, addr_str))
            results[sym] = {'error': 'no function defined at %s' % addr_str}
            continue

        candidates = []
        candidates.extend(extract_string_candidates(func))
        imp = extract_import_pattern(func)
        if imp is not None:
            candidates.append(imp)
        sig = extract_byte_signature(func)
        if sig is not None:
            candidates.append(sig)
        vt = extract_vtable_candidate(func)
        if vt is not None:
            candidates.append(vt)

        results[sym] = {
            'address': addr_str,
            'function_name': func.getName(),
            'candidate_count': len(candidates),
            'candidates': candidates,
        }

    # Write JSON (Jython's json.dump handles unicode strings fine).
    fh = open(out_path, 'w')
    try:
        json.dump(results, fh, indent=2, sort_keys=True)
    finally:
        fh.close()

    print('=' * 60)
    print('Processed: %d of %d function_pointer entries' % (n_done, len(target_entries)))
    print('No function found: %d' % len(no_function))
    if no_function:
        for sym, addr_str in no_function[:10]:
            print('  %s  @ %s' % (sym, addr_str))
        if len(no_function) > 10:
            print('  ... and %d more' % (len(no_function) - 10))
        print('  -> consider disassembling those addresses (right-click '
              '"Create Function") and rerunning.')
    print('Wrote %s' % out_path)
    print('Next: python3 tools/addresses/apply_auto_anchors.py')


main()
