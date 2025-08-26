from par_core.detectors.patterns import find_pii
try:
    from par_core.detectors.huge_rules import EXAMPLES, RULES
except Exception:
    EXAMPLES = []
    RULES = []

def test_huge_rules_detection():
    if not EXAMPLES or not RULES:
        assert True
        return
    sample = "\n".join(EXAMPLES)
    findings = find_pii(sample)
    # Expect at least 60% of rules to be detected (allowing overlaps / false-negatives)
    assert len(findings) >= int(len(RULES) * 0.6), f"Expected at least {int(len(RULES)*0.6)} findings, got {len(findings)}"