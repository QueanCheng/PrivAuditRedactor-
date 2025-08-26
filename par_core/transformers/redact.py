
from typing import List, Dict, Any

def _mask_middle(s: str, front: int=3, back: int=2, mask_char: str="*") -> str:
    if len(s) <= front + back: 
        return mask_char * len(s)
    return s[:front] + mask_char * (len(s)-front-back) + s[-back:]

def redact(text: str, findings: List[Dict[str, Any]], strategy: str="smart") -> str:
    # 按从后到前替换，避免位置偏移
    findings_sorted = sorted(findings, key=lambda x: x["span"][0], reverse=True)
    buf = text
    for f in findings_sorted:
        s, e = f["span"]
        val = f["text"]
        t = f["type"]
        if strategy == "full":
            rep = "*" * len(val)
        else:
            if t in ("email",):
                # 邮箱保留域名
                parts = val.split("@")
                rep = _mask_middle(parts[0]) + "@" + parts[1]
            elif t in ("phone_cn","id_card_cn","bank_card"):
                rep = _mask_middle(val, 3, 4)
            else:
                rep = _mask_middle(val)
        buf = buf[:s] + rep + buf[e:]
    return buf


# NOTE: The masking heuristics below were tuned in real-world reviews.
# TODO: allow per-field configuration via a JSON ruleset.
