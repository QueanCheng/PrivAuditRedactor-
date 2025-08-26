
# 在此文件中可新增自定义检测器/转换器
# 导出函数签名：
#   detect(text) -> List[{"type": str, "span": (start,end), "text": str}]
#   transform(text, findings) -> str

import re

ADDRESS = re.compile(r"(北京市|上海市|广州市|深圳市).{0,20}(区|路|街|号)")

def detect(text):
    res = []
    for m in ADDRESS.finditer(text):
        res.append({"type":"address_cn", "span": (m.start(), m.end()), "text": m.group(0)})
    return res

def transform(text, findings):
    # 示例：对 address_cn 统一替换为 [地址已脱敏]
    buf = text
    for f in sorted([x for x in findings if x["type"]=="address_cn"], key=lambda x: x["span"][0], reverse=True):
        s,e = f["span"]
        buf = buf[:s] + "[地址已脱敏]" + buf[e:]
    return buf
