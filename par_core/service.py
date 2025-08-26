"""
High-level processing service.

Exposes `process_file` which orchestrates extraction, detection, transformation
and auditing. This is deliberately kept small; major logic is delegated to
par_core.detectors and par_core.transformers modules.
"""

# Developer note: keep progress callbacks lightweight so GUI remains responsive.


from pathlib import Path
from typing import Dict, Any
from par_core.detectors.patterns import find_pii
from par_core.transformers.redact import redact
from par_core.db import record_operation
from par_core.utils.misc import load_plugins, apply_plugin_detectors, apply_plugin_transformers, text_diff

def process_file(path: Path, user: str="user", strategy: str="smart", plugins_dir: Path=None) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = find_pii(text)
    plugins = load_plugins(plugins_dir or (Path(__file__).resolve().parents[2] / "plugins"))
    findings += apply_plugin_detectors(plugins, text)
    redacted = redact(text, findings, strategy=strategy)
    redacted = apply_plugin_transformers(plugins, redacted, findings)
    meta = {"strategy": strategy, "findings": len(findings)}
    op_id, chain_hash = record_operation(user=user, action="redact", file_path=str(path), before_text=text, after_text=redacted, meta=meta)
    return {
        "op_id": op_id, "chain_hash": chain_hash, "findings": findings, 
        "redacted": redacted, "diff": text_diff(text, redacted)
    }
