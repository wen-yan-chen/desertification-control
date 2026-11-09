# -*- coding: utf-8 -*-
"""把 .tmp.docx 替换为正式文件名（被占用时重试，最多约 5 分钟）"""
import os
import time

BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Reports"
)
pairs = ["数据来源与获取说明.docx", "数据预处理报告.docx"]

done = {}
deadline = time.time() + 300
while time.time() < deadline and len(done) < len(pairs):
    for name in pairs:
        if name in done:
            continue
        stage = os.path.join(BASE, name + ".tmp.docx")
        target = os.path.join(BASE, name)
        if not os.path.exists(stage):
            done[name] = "no-tmp"
            continue
        try:
            os.replace(stage, target)
            done[name] = "ok"
            print("replaced:", name, flush=True)
        except PermissionError:
            pass
    time.sleep(3)

for name in pairs:
    print(name, "->", done.get(name, "timeout"), flush=True)
