
# This test is a lightweight sanity check created during manual review.
# It intentionally uses a small sample and asserts that critical detectors work.
from par_core.detectors.patterns import find_pii

def test_basic_sanity():
    sample = 'Contact: alice@example.com, Phone: 13800138000, Visa: 4111111111111111'
    found = find_pii(sample)
    types = {f['type'] for f in found}
    assert 'email' in types
    assert 'phone_cn' in types
    # Visa card detection may appear under a payment-card-like pattern
    assert any('visa' in t or 'card' in t for t in types)
