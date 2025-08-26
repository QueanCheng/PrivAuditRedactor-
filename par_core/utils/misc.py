
import importlib.util, sys, pathlib, difflib, gzip
from typing import Callable, List, Dict, Any

def load_plugins(plugin_dir: pathlib.Path):
    plugins = []
    if not plugin_dir.exists(): return plugins
    for py in plugin_dir.glob("*.py"):
        spec = importlib.util.spec_from_file_location(py.stem, py)
        if not spec or not spec.loader: 
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore
            plugins.append(mod)
        except Exception as e:
            print(f"[PluginError] {py.name}: {e}")
    return plugins

def apply_plugin_detectors(plugins, text: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for p in plugins:
        if hasattr(p, "detect"):
            try:
                res = p.detect(text)
                if isinstance(res, list):
                    results.extend(res)
            except Exception as e:
                print(f"[PluginDetectError] {p.__name__}: {e}")
    return results

def apply_plugin_transformers(plugins, text: str, findings: List[Dict[str, Any]]) -> str:
    buf = text
    for p in plugins:
        if hasattr(p, "transform"):
            try:
                buf = p.transform(buf, findings)
            except Exception as e:
                print(f"[PluginTransformError] {p.__name__}: {e}")
    return buf

def text_diff(a: str, b: str) -> str:
    return "\n".join(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))
