#!/bin/bash
set -e

echo "======================================"
echo "LexPrime 回归测试套件"
echo "======================================"

cd "$(dirname "$0")/.."

echo "1. 运行核心 API 回归测试..."
python -m pytest tests/test_regression.py -v --tb=short

echo ""
echo "2. 运行认证 API 测试..."
python -m pytest tests/test_auth_api.py -v --tb=short

echo ""
echo "3. 运行案件 API 测试..."
python -m pytest tests/test_case_api.py -v --tb=short

echo ""
echo "4. 运行合同审查 API 测试..."
python -m pytest tests/test_contract_api.py -v --tb=short

echo ""
echo "5. 运行客户 API 测试..."
python -m pytest tests/test_client_api.py -v --tb=short

echo ""
echo "======================================"
echo "回归测试完成"
echo "======================================"
