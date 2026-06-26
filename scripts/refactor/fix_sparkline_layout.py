"""修复 sparkline 布局 + 副标题断行"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
p = ROOT / 'templates' / 'views' / 'knowledge.html'
c = p.read_text(encoding='utf-8')
orig = c

# 1. 4 个统计卡副标题 → 文字加 whitespace-nowrap, SVG 缩小到 56x20
# 找到模式: <p class="text-[10px] text-{success|urgent|fg-tertiary}">xxx</p>\n<svg class="overflow-visible" viewBox="0 0 64 24"
# 替换 svg class 为 w-14 h-5, 加 p 的 truncate

# 直接替换 4 个 sparkline 的 svg 容器宽度
# 旧: <svg class="overflow-visible" viewBox="0 0 64 24"
# 新: <svg class="overflow-visible w-14 h-5" viewBox="0 0 64 24"
n = c.count('<svg class="overflow-visible" viewBox="0 0 64 24"')
c = c.replace('<svg class="overflow-visible" viewBox="0 0 64 24"', '<svg class="overflow-visible w-14 h-5" viewBox="0 0 64 24"')
print(f'sparkline svg 缩窄: {n} 处')

# 副标题文字加 whitespace-nowrap + flex-shrink-0
# 匹配 <p class="text-[10px] text-xxx">文字</p> 紧跟 sparkline svg 的模式
# 简单点: 4 个副标题行人工替换
# 实际上副标题 "↑ 7 天 +3" "● 现行有效 38 部" 等可能被 sparkline 挤压
# 让所有副标题加 whitespace-nowrap
patterns = [
    ('<p class="text-[10px] text-success">↑ 7 天 +3</p>', '<p class="text-[10px] text-success whitespace-nowrap">↑ 7 天 +3</p>'),
    ('<p class="text-[10px] text-wiki">由 LLM 维护</p>', '<p class="text-[10px] text-wiki whitespace-nowrap">由 LLM 维护</p>'),
    ('<p class="text-[10px] text-urgent">● 2 个待补</p>', '<p class="text-[10px] text-urgent whitespace-nowrap">● 2 个待补</p>'),
    ('<p class="text-[10px] text-danger">● 1 项紧急</p>', '<p class="text-[10px] text-danger whitespace-nowrap">● 1 项紧急</p>'),
]
for old, new in patterns:
    if old in c:
        c = c.replace(old, new)
        print(f'  {old} → nowrap')

# 写回
p.write_text(c, encoding='utf-8')
print('OK')

# div 平衡
opens = len(re.findall(r'<div\b', c))
closes = c.count('</div>')
print(f'div 平衡: {opens} / {closes}')
