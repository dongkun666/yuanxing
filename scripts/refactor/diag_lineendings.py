"""诊断: 检查 case-detail.html 当前状态 vs 期望行为"""
import re
from pathlib import Path

p = Path(r'E:\元枢法智前端\yuanxing\templates\views\case-detail.html')
content = p.read_bytes()
print(f'文件大小: {len(content)} bytes')

# 数 CR LF CRLF
crlf = content.count(b'\r\n')
lf_only = content.count(b'\n') - crlf
cr_only = content.count(b'\r') - crlf
print(f'CRLF: {crlf}, LF only: {lf_only}, CR only: {cr_only}')

# 重新读为字符串, 看前 20 行
text = p.read_text(encoding='utf-8', errors='ignore')
print('\n=== 前 20 行 ===')
for i, line in enumerate(text.split('\n')[:20]):
    print(f'L{i+1:2d} [{len(line):3d}] {repr(line[:80])}')

# 用 binary 模式读, 看 raw line endings
print('\n=== raw lines with endings ===')
for i, line in enumerate(content.split(b'\n')[:20]):
    has_crlf = line.endswith(b'\r')
    print(f'L{i+1:2d} CRLF={has_crlf} [{len(line):3d}] {repr(line[:60])}')
