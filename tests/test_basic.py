
from pathlib import Path
from par_core.service import process_file
from par_core.detectors.patterns import find_pii

def test_find_pii():
    t = "a@b.com 13912345678 110101199003071234 6222021234567890"
    r = find_pii(t)
    assert any(x["type"]=="email" for x in r)
    assert any(x["type"]=="phone_cn" for x in r)
    assert any(x["type"]=="id_card_cn" for x in r)

def test_process(tmp_path: Path):
    p = tmp_path/"a.txt"; p.write_text("a@b.com 13912345678")
    res = process_file(p)
    assert "@" in res["redacted"]
    assert len(res["findings"]) >= 2
