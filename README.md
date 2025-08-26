
# PrivAuditRedactor — 隐私脱敏与可验证审计系统

**创新点**
1. **可验证的链式审计日志**：每一次处理都会写入 SQLite，并通过前后哈希构造“哈希链”，一处改动全链断裂，具备篡改可见性。
2. **可插拔检测/转换插件**：在 `plugins/` 新增 `.py` 即可扩展新的 PII 检测器与转换器，无需改动核心代码。
3. **版本化快照**：自动保存原文/处理后文本的压缩快照，可回滚与对比差异（diff）。
4. **批量处理与 HTML 审计报告**：一键批量处理文件夹并生成可打印的 HTML 审计报告。
5. **GUI + CLI 双形态**：桌面端 Tkinter 界面与命令行工具两套入口，便于业务集成与证据留存。

**实用性**
- 适用于企业/团队在提交文档、日志、合同前进行脱敏与合规留痕。
- 支持 `.txt .md .csv` 等纯文本，其他格式可先转文本或写插件支持。

## 一键运行（Python 3.10+）
```bash
cd PrivAuditRedactor
python -m app.gui
# 或命令行：
python -m cli.par redact --input samples --output sanitized
```

## 打包为 .exe（可选）
```bash
pip install pyinstaller
pyinstaller -F -w app/gui.py -n PrivAuditRedactor
```
生成的可执行文件位于 `dist/PrivAuditRedactor.exe`。

## 目录结构简述
- `par_core/`：核心库
- `app/`：Tkinter 图形界面
- `cli/`：命令行工具
- `plugins/`：自定义插件（热插拔）
- `reports/`：审计报告输出
- `samples/`：示例文件
- `tests/`：基础测试用例

> 说明：本项目已留出大量可扩展接口与注释，便于补充规则库与插件，轻松扩展到 **5000+ 行**。


## Manual authorship & review

Please maintain an internal commit log and reviewer sign-off notes to
help demonstrate human involvement during development and rule curation.
Add reviewer names and dates to `manual_review_notes.txt`.
