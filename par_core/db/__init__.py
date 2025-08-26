"""
Database helper for PrivAuditRedactor

This module manages a lightweight SQLite-backed audit log. The log stores
compressed snapshots of 'before' and 'after' content and builds a simple
hash-chain to make post-hoc tampering evident.

Notes by developer:
- Keep the schema simple to ease manual inspection.
- The hashing approach is intentionally straightforward (SHA-256 of payload)
  so that auditors can reproduce chain hashes offline if necessary.
"""

# Small human touch: a very short usage example is embedded below.
# Example usage:
#   from par_core.db import record_operation
#   record_operation('alice', 'redact', '/tmp/a.txt', 'orig', 'redacted', {'notes':'sample'})

# -- file continues with original content --


import sqlite3, pathlib, datetime, hashlib, zlib, json, os
from typing import Optional, Tuple, Dict, Any

DB_PATH = pathlib.Path.home() / ".priv_audit_redactor.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  op_time TEXT NOT NULL,
  user TEXT,
  action TEXT NOT NULL,
  file_path TEXT,
  before_hash TEXT,
  after_hash TEXT,
  prev_chain_hash TEXT,
  chain_hash TEXT,
  meta TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  op_id INTEGER NOT NULL,
  kind TEXT NOT NULL, -- "before" | "after"
  content BLOB NOT NULL,
  FOREIGN KEY(op_id) REFERENCES operations(id)
);
"""

def _connect():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA journal_mode=WAL;")
    return con

def init_db():
    con = _connect()
    with con:
        con.executescript(SCHEMA)
    con.close()

def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _calc_chain(prev_chain_hash: Optional[str], payload: Dict[str, Any]) -> str:
    base = (prev_chain_hash or "").encode("utf-8") + json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _hash_bytes(base)

def _compress(text: str) -> bytes:
    return zlib.compress(text.encode("utf-8"))

def _decompress(blob: bytes) -> str:
    return zlib.decompress(blob).decode("utf-8")

def _get_last_chain_hash(con) -> Optional[str]:
    cur = con.execute("SELECT chain_hash FROM operations ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    return row[0] if row else None

def record_operation(user: str, action: str, file_path: str, before_text: str, after_text: str, meta: Dict[str, Any]):
    init_db()
    con = _connect()
    with con:
        prev_chain_hash = _get_last_chain_hash(con)
        before_hash = _hash_bytes(before_text.encode("utf-8"))
        after_hash = _hash_bytes(after_text.encode("utf-8"))
        op_time = datetime.datetime.utcnow().isoformat()
        payload = {
            "op_time": op_time, "user": user, "action": action,
            "file_path": file_path, "before_hash": before_hash, "after_hash": after_hash, "meta": meta
        }
        chain_hash = _calc_chain(prev_chain_hash, payload)
        cur = con.execute(
            "INSERT INTO operations (op_time, user, action, file_path, before_hash, after_hash, prev_chain_hash, chain_hash, meta) VALUES (?,?,?,?,?,?,?,?,?);",
            (op_time, user, action, file_path, before_hash, after_hash, prev_chain_hash, chain_hash, json.dumps(meta, ensure_ascii=False))
        )
        op_id = cur.lastrowid
        con.execute("INSERT INTO snapshots (op_id, kind, content) VALUES (?,?,?);", (op_id, "before", _compress(before_text)))
        con.execute("INSERT INTO snapshots (op_id, kind, content) VALUES (?,?,?);", (op_id, "after", _compress(after_text)))
        return op_id, chain_hash

def read_operation(op_id: int):
    con = _connect()
    cur = con.execute("SELECT id, op_time, user, action, file_path, before_hash, after_hash, prev_chain_hash, chain_hash, meta FROM operations WHERE id=?;", (op_id,))
    op = cur.fetchone()
    if not op: return None
    s_cur = con.execute("SELECT kind, content FROM snapshots WHERE op_id=?;", (op_id,))
    snaps = dict(s_cur.fetchall())
    return {
        "operation": {
            "id": op[0], "op_time": op[1], "user": op[2], "action": op[3], "file_path": op[4],
            "before_hash": op[5], "after_hash": op[6], "prev_chain_hash": op[7], "chain_hash": op[8],
            "meta": json.loads(op[9] or "{}")
        },
        "snapshots": { k: _decompress(v) for k,v in snaps.items() }
    }

def export_chain_html(dest_path: os.PathLike):
    con = _connect()
    rows = list(con.execute("SELECT id, op_time, user, action, file_path, before_hash, after_hash, prev_chain_hash, chain_hash, meta FROM operations ORDER BY id;"))
    html = ["<html><head><meta charset='utf-8'><title>Audit Chain</title><style>body{font-family:Arial} code{word-break:break-all}</style></head><body>"]
    html.append("<h1>PrivAuditRedactor 审计链报告</h1>")
    html.append(f"<p>导出时间（UTC）：{datetime.datetime.utcnow().isoformat()}</p>")
    html.append("<table border='1' cellspacing='0' cellpadding='6'>")
    html.append("<tr><th>ID</th><th>时间</th><th>用户</th><th>动作</th><th>文件</th><th>前哈希</th><th>后哈希</th><th>前链哈希</th><th>当前链哈希</th><th>元数据</th></tr>")
    for r in rows:
        html.append("<tr>" + "".join([f"<td><code>{str(c)}</code></td>" for c in r]) + "</tr>")
    html.append("</table></body></html>")
    pathlib.Path(dest_path).write_text("\n".join(html), encoding="utf-8")
    return str(dest_path)


def export_chain_html_with_stats(dest_path: os.PathLike):
    con = _connect()
    rows = list(con.execute("SELECT id, op_time, user, action, file_path, before_hash, after_hash, prev_chain_hash, chain_hash, meta FROM operations ORDER BY id;"))
    # compute stats
    total = len(rows)
    by_user = {}
    by_action = {}
    for r in rows:
        user = r[2] or "unknown"
        by_user[user] = by_user.get(user, 0) + 1
        action = r[3]
        by_action[action] = by_action.get(action, 0) + 1
    import html, json, datetime, pathlib
    html_lines = ["<html><head><meta charset=\'utf-8\'><title>Audit Chain</title>",
                  "<style>body{font-family:Arial} code{word-break:break-all} .chart{width:600px;height:300px;}</style>",
                  "</head><body>"]
    html_lines.append("<h1>PrivAuditRedactor 审计链报告（含统计）</h1>")
    html_lines.append(f"<p>导出时间（UTC）：{datetime.datetime.utcnow().isoformat()}</p>")
    html_lines.append(f"<p>总记录数：<strong>{total}</strong></p>")
    html_lines.append("<h2>按用户统计</h2>")
    html_lines.append(f"<pre>{html.escape(json.dumps(by_user, ensure_ascii=False, indent=2))}</pre>")
    html_lines.append("<h2>按动作统计</h2>")
    html_lines.append(f"<pre>{html.escape(json.dumps(by_action, ensure_ascii=False, indent=2))}</pre>")
    # table
    html_lines.append('<table border=\"1\" cellspacing=\"0\" cellpadding=\"6\">')
    html_lines.append("<tr><th>ID</th><th>时间</th><th>用户</th><th>动作</th><th>文件</th><th>前哈希</th><th>后哈希</th><th>元数据</th></tr>")
    for r in rows:
        meta = r[9] if r[9] else "{}"
        html_lines.append("<tr>" + "".join([f"<td><code>{str(c)}</code></td>" for c in r[:8]]) + f"<td><code>{html.escape(str(meta))}</code></td></tr>")
    html_lines.append("</table>")
    # simple JS pie using Chart.js CDN
    users_json = json.dumps(by_user)
    actions_json = json.dumps(by_action)
    html_lines.append('<h2>可视化</h2>')
    html_lines.append('<canvas id="userChart" class="chart"></canvas>')
    html_lines.append('<canvas id="actionChart" class="chart"></canvas>')
    html_lines.append('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
    html_lines.append(f"<script>const userData = {users_json}; const actionData = {actions_json}; const uLabels=Object.keys(userData), uVals=Object.values(userData); const aLabels=Object.keys(actionData), aVals=Object.values(actionData); new Chart(document.getElementById('userChart').getContext('2d'), {{type:'bar', data:{{labels:uLabels,datasets:[{{label:'按用户',data:uVals}}]}}}}); new Chart(document.getElementById('actionChart').getContext('2d'), {{type:'pie', data:{{labels:aLabels,datasets:[{{label:'按动作',data:aVals}}]}}}});</script>")
    html_lines.append("</body></html>")
    pathlib.Path(dest_path).write_text("\\n".join(html_lines), encoding="utf-8")
    return str(dest_path)


# TODO: add optional HMAC signing to the chain for an extra verification layer.
