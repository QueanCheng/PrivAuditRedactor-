import os
import sys
import datetime

# 定义要打包的核心代码目录和文件
CORE_DIRS = [
    'par_core/detectors',
    'par_core/transformers',
    'par_core/utils',
    'par_core/db',
    'app',
    'cli'
]

CORE_FILES = [
    'par_core/__init__.py',
    'par_core/service.py',
    'README.md'
]

# 获取桌面路径
DESKTOP_PATH = 'C:\\Users\\Administrator\\Desktop'
OUTPUT_FILE = os.path.join(DESKTOP_PATH, 'PrivAuditRedactor核心代码.txt')

# 检查文件是否存在并确认覆盖
if os.path.exists(OUTPUT_FILE):
    print(f"文件 {OUTPUT_FILE} 已存在，将被覆盖。")

# 创建输出文件并写入内容
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("# PrivAuditRedactor 隐私脱敏与可验证审计系统 - 核心代码\n\n")
    f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # 写入目录下的所有Python文件
    for core_dir in CORE_DIRS:
        if not os.path.exists(core_dir):
            f.write(f"## 警告：目录 {core_dir} 不存在\n\n")
            continue
            
        f.write(f"## 目录: {core_dir}\n\n")
        
        # 遍历目录中的所有Python文件
        for root, _, files in os.walk(core_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, '.')
                    
                    f.write(f"### 文件: {relative_path}\n")
                    f.write("```python\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as code_file:
                            f.write(code_file.read())
                    except Exception as e:
                        f.write(f"# 读取文件失败: {str(e)}")
                    f.write("\n```\n\n")
    
    # 写入单独的核心文件
    for core_file in CORE_FILES:
        if not os.path.exists(core_file):
            f.write(f"## 警告：文件 {core_file} 不存在\n\n")
            continue
            
        f.write(f"## 文件: {core_file}\n")
        f.write("```python\n")
        try:
            with open(core_file, 'r', encoding='utf-8') as code_file:
                f.write(code_file.read())
        except Exception as e:
            f.write(f"# 读取文件失败: {str(e)}")
        f.write("\n```\n\n")

print(f"核心代码已成功打包到: {OUTPUT_FILE}")