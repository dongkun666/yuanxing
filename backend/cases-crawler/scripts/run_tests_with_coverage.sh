#!/bin/bash
set -e

echo "======================================"
echo "LexPrime API 测试覆盖率报告"
echo "======================================"

cd "$(dirname "$0")/.."

echo "运行测试并生成覆盖率报告..."
python -m pytest tests/ -v --cov=. --cov-report=term --cov-report=html --cov-report=xml

echo ""
echo "======================================"
echo "覆盖率报告已生成:"
echo "- 终端报告: 已显示"
echo "- HTML 报告: htmlcov/index.html"
echo "- XML 报告: coverage.xml"
echo "======================================"

echo ""
echo "目标覆盖率: 80%"
echo "当前覆盖率检查..."
python -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
total = data['totals']['percent_covered']
print(f'当前覆盖率: {total:.1f}%')
if total >= 80:
    print('✓ 覆盖率达标!')
else:
    print(f'✗ 覆盖率未达标, 还差 {80 - total:.1f}%')
"
