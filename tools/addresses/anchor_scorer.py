#!/usr/bin/env python3
"""
Anchor scorer for the Utinni address-table pipeline.

A real Ghidra script (not yet built) will walk each function in the
original SWG binary, extract candidate anchors, and ask this module
which one is best. This file owns the scoring logic alone -- testable
in isolation without a Ghidra session.

The Ghidra side is expected to produce candidates of this shape:

    {
        "kind": "string_xref" | "import_pattern" | "byte_signature" | "vtable_slot",
        "value": "...",          # the actual anchor data (the string,
                                 # the byte sig, etc.)
        "occurrences": int,      # times `value` appears in the binary
        "function_count": int,   # distinct functions referencing `value`

        # kind-specific extras:
        "length": int,                 # string_xref or byte_signature
        "wildcards": int,              # byte_signature only
        "is_format_string": bool,      # string_xref only
        "imports": list[str],          # import_pattern only
        "vtable_class": str,           # vtable_slot only
        "vtable_index": int,           # vtable_slot only
    }

Score is a float 0..100. Higher is better. Anchors are also given a
confidence label:

    >= 75   high     -- accept without review
    50..75  medium   -- glance at it in Ghidra, probably fine
    25..50  low      -- needs human verification
    < 25    none     -- effectively unusable

Run the module directly to execute a self-test:

    python3 tools/addresses/anchor_scorer.py
"""

import math
import sys
from typing import Optional


# Base score per anchor kind. Reflects "all else equal, which kind of
# anchor is most likely to still resolve after a binary patch?"
BASE_SCORE = {
    'string_xref':    100.0,  # Strings rarely change; survive most patches
    'vtable_slot':     85.0,  # Stable as long as the class layout is stable
    'import_pattern':  65.0,  # Imports stable, ordering less so
    'byte_signature':  45.0,  # Brittle -- any inline change breaks it
}


def uniqueness_factor(function_count: int) -> float:
    """1.0 when the value identifies exactly one function; decays after.

    The Ghidra script feeds us `function_count` -- how many distinct
    functions reference (or contain) the candidate value across the
    whole binary. Anchors that are unique to one function are gold.
    Anchors shared by 50+ functions are noise.
    """
    if function_count <= 0:
        return 0.0
    if function_count == 1:
        return 1.0
    # Sharp decay: each extra sharer roughly halves the usefulness.
    return 1.0 / math.sqrt(function_count)


def length_factor(length: int, sweet_spot: int = 32) -> float:
    """Reward strings/byte-sigs around the sweet spot; cap very long."""
    if length <= 0:
        return 0.0
    if length >= sweet_spot:
        # Diminishing returns past the sweet spot -- a 200-char string
        # isn't proportionally better than a 32-char one.
        return min(1.0, 0.7 + 0.3 * math.log(length / sweet_spot + 1))
    # Below sweet spot, linear ramp from 0 to 1.
    return length / sweet_spot


def specificity_factor(value: str) -> float:
    """Reward distinctive content (format specifiers, mixed case, etc.)."""
    if not value:
        return 0.0
    score = 0.5  # baseline
    if '%' in value:                       score += 0.20  # format string
    if any(c.isupper() for c in value) and any(c.islower() for c in value):
        score += 0.15                                     # mixed case
    if any(c in value for c in '_:./\\'): score += 0.05  # path-ish / symbol-ish
    if len(set(value.lower().split())) >= 3:
        score += 0.10                                     # multiple distinct words
    return min(1.0, score)


def score_string_xref(c: dict) -> tuple:
    base = BASE_SCORE['string_xref']
    u = uniqueness_factor(c.get('function_count', 1))
    le = length_factor(c.get('length', len(c.get('value', ''))))
    sp = specificity_factor(c.get('value', ''))
    # Format-string bonus on top of specificity
    bonus = 0.05 if c.get('is_format_string') else 0.0
    score = base * u * (0.5 * le + 0.4 * sp + 0.1 + bonus)
    return (score, {
        'base': base, 'uniqueness': u, 'length': le,
        'specificity': sp, 'format_bonus': bonus,
    })


def score_vtable_slot(c: dict) -> tuple:
    base = BASE_SCORE['vtable_slot']
    # Vtable slots don't have "uniqueness" in the same sense -- the slot
    # number is positional. The only risk is whether the class layout
    # changes. Slight penalty for very large vtable indices (more likely
    # to be in append-only-growing parts of the class).
    idx = c.get('vtable_index', 0)
    layout_factor = 1.0 if idx < 32 else max(0.6, 1.0 - (idx - 32) / 200)
    score = base * layout_factor
    return (score, {'base': base, 'layout': layout_factor})


def score_import_pattern(c: dict) -> tuple:
    base = BASE_SCORE['import_pattern']
    u = uniqueness_factor(c.get('function_count', 1))
    # Reward longer patterns (more distinctive)
    imports = c.get('imports', [])
    pat_len_factor = min(1.0, len(imports) / 5.0)
    score = base * u * (0.6 * pat_len_factor + 0.4)
    return (score, {
        'base': base, 'uniqueness': u, 'pattern_length': pat_len_factor,
    })


def score_byte_signature(c: dict) -> tuple:
    base = BASE_SCORE['byte_signature']
    u = uniqueness_factor(c.get('function_count', 1))
    le = length_factor(c.get('length', 0), sweet_spot=16)
    # Wildcards make a signature more portable but less specific.
    wc = c.get('wildcards', 0)
    wc_factor = max(0.4, 1.0 - wc / 20.0)
    score = base * u * (0.6 * le + 0.4) * wc_factor
    return (score, {
        'base': base, 'uniqueness': u, 'length': le, 'wildcard_factor': wc_factor,
    })


_SCORERS = {
    'string_xref':    score_string_xref,
    'vtable_slot':    score_vtable_slot,
    'import_pattern': score_import_pattern,
    'byte_signature': score_byte_signature,
}


def confidence_label(score: float) -> str:
    if score >= 75: return 'high'
    if score >= 50: return 'medium'
    if score >= 25: return 'low'
    return 'none'


def score_candidate(candidate: dict) -> dict:
    """Return {score, confidence, breakdown} for one candidate."""
    kind = candidate.get('kind')
    if kind not in _SCORERS:
        return {
            'score': 0.0,
            'confidence': 'none',
            'breakdown': {'error': f'unknown kind: {kind!r}'},
        }
    score, breakdown = _SCORERS[kind](candidate)
    return {
        'score': round(score, 2),
        'confidence': confidence_label(score),
        'breakdown': breakdown,
    }


def pick_best(candidates: list) -> Optional[dict]:
    """Score all candidates; return the highest-scored along with its result.

    Returns dict {candidate, result} or None if the list is empty.
    """
    if not candidates:
        return None
    scored = [(c, score_candidate(c)) for c in candidates]
    scored.sort(key=lambda t: t[1]['score'], reverse=True)
    candidate, result = scored[0]
    return {'candidate': candidate, 'result': result, 'considered': len(candidates)}


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def _selftest() -> int:
    cases = [
        # 1. Gold-standard anchor: unique distinctive format string.
        ('gold_string', {
            'kind': 'string_xref',
            'value': 'CameraSetMode: invalid mode %d',
            'length': 31,
            'occurrences': 1, 'function_count': 1,
            'is_format_string': True,
        }, 'high'),

        # 2. Garbage anchor: trivially short, shared across many functions.
        ('noise_string', {
            'kind': 'string_xref',
            'value': 'OK',
            'length': 2,
            'occurrences': 247, 'function_count': 89,
            'is_format_string': False,
        }, 'none'),

        # 3. Low-confidence anchor: a string spread across 5 functions
        # genuinely needs human disambiguation -- which of the 5 xrefs
        # points to the function we care about?
        ('ambiguous_string', {
            'kind': 'string_xref',
            'value': 'failed to load resource',
            'length': 23,
            'occurrences': 5, 'function_count': 5,
            'is_format_string': False,
        }, 'low'),

        # 4. Vtable slot at a low index.
        ('vtable_early', {
            'kind': 'vtable_slot',
            'vtable_class': 'utinni::Object',
            'vtable_index': 3,
        }, 'high'),

        # 5. Vtable slot deep in a large class -- still ok but less so.
        ('vtable_deep', {
            'kind': 'vtable_slot',
            'vtable_class': 'utinni::Object',
            'vtable_index': 120,
        }, 'medium'),

        # 6. Distinctive import pattern, used by exactly one function.
        ('imports_unique', {
            'kind': 'import_pattern',
            'imports': ['CreateFileA', 'WriteFile', 'CloseHandle', 'GetLastError'],
            'function_count': 1,
            'value': 'CreateFileA,WriteFile,CloseHandle,GetLastError',
        }, 'medium'),

        # 7. Short, common byte signature shared across many functions.
        ('weak_bytes', {
            'kind': 'byte_signature',
            'value': '55 8B EC',
            'length': 3,
            'wildcards': 0,
            'function_count': 4000,
        }, 'none'),

        # 8. Long unique byte signature with a few wildcards.
        ('strong_bytes', {
            'kind': 'byte_signature',
            'value': '55 8B EC 6A FF 68 ?? ?? ?? ?? 64 A1 00 00 00 00 50 64 89 25',
            'length': 20,
            'wildcards': 4,
            'function_count': 1,
        }, 'low'),

        # 9. Pick-best across a mix should choose the gold string.
    ]

    print(f"{'name':<20} {'kind':<16} {'score':>7}   confidence  expected   {'OK' if False else ''}")
    print("-" * 78)
    failures = 0
    for name, c, expected_conf in cases:
        r = score_candidate(c)
        ok = (r['confidence'] == expected_conf)
        marker = '   ok' if ok else '   FAIL'
        if not ok:
            failures += 1
        print(f"{name:<20} {c['kind']:<16} {r['score']:>7.2f}   "
              f"{r['confidence']:<10}  {expected_conf:<10}{marker}")

    # pick_best demo
    candidates_for_func = [c for _, c, _ in cases[:3]]
    best = pick_best(candidates_for_func)
    print()
    print("pick_best across the first 3 candidates:")
    if best is not None:
        bk = best['candidate']['kind']
        bv = best['candidate'].get('value', '')[:50]
        bs = best['result']['score']
        bc = best['result']['confidence']
        print(f"  winner: {bk}  score={bs:.2f}  confidence={bc}")
        print(f"  value:  {bv!r}")
        # Expect the gold_string to win
        if best['candidate'].get('value', '').startswith('CameraSetMode'):
            print("  ok -- expected winner")
        else:
            print("  FAIL -- expected gold_string to win")
            failures += 1

    print()
    if failures:
        print(f"FAIL: {failures} case(s) did not match expected confidence.")
        return 1
    print("All self-test cases passed.")
    return 0


if __name__ == '__main__':
    sys.exit(_selftest())
