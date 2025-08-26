"""
PII detection patterns.

This file collects regular expressions used to find potentially sensitive
information in free text. Patterns are built from a combination of hand-tuned
expressions and a larger auto-generated ruleset (huge_rules.py).

Developer notes:
- When adding new patterns, please include at least one concrete example in
  par_core/detectors/huge_rules.py EXAMPLES list so that unit tests can sample.
- Regex complexity should be balanced with performance – avoid catastrophic backtracking.
"""

# Human comment: legacy compatibility layer below.

import re
from typing import List, Tuple, Pattern, Dict, Any

# Try to import an extended huge ruleset if present
try:
    from .huge_rules import RULES as HUGE_RULES
except Exception:
    HUGE_RULES = []

# Base patterns
BASE_PATTERNS: List[Tuple[str, Pattern]] = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}")),
    ("phone_cn", re.compile(r"\b1[3-9]\d{9}\b")),
    ("id_card_cn", re.compile(r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]\b")),
    ("bank_card", re.compile(r"\b\d{12,19}\b")),
]

# Convert HUGE_RULES into PATTERNS
PATTERNS = []
for r in HUGE_RULES:
    try:
        PATTERNS.append((r.get('name'), r.get('regex')))
    except Exception:
        pass
PATTERNS.extend(BASE_PATTERNS)


def luhn_check(number: str) -> bool:
    s = 0
    alt = False
    for ch in number[::-1]:
        if not ch.isdigit(): return False
        n = ord(ch) - 48
        if alt:
            n *= 2
            if n > 9: n -= 9
        s += n
        alt = not alt
    return s % 10 == 0


def find_pii(text: str) -> List[Dict[str, Any]]:
    findings = []
    for name, pat in PATTERNS:
        for m in pat.finditer(text):
            span_text = m.group(0)
            if name == "bank_card" and not luhn_check(span_text):
                continue
            findings.append({"type": name, "span": (m.start(), m.end()), "text": span_text})
    # dedupe overlapping by start-end
    findings_sorted = sorted(findings, key=lambda x: (x["span"][0], -x["span"][1]))
    res = []
    last_end = -1
    for f in findings_sorted:
        if f["span"][0] >= last_end:
            res.append(f)
            last_end = f["span"][1]
    return res
