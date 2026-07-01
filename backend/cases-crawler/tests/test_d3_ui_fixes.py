"""
D3 W8 - 6 项 P1-P3 UI 修复回归测试

W4 评审 6 项 P1-P3 UI 修复, W5 完成 3 项, W7 推 3 项 (P1 移动端 / P2 立场预览 / P3 致命折叠),
W8 D3 集中修复并验证.

测试范围:
- 移动端 < 768px 5 页面适配 (templates/views/contract-review/*.html)
- 立场影响预览 (4 立场 × 3 风险等级 加权/降权)
- 致命条款 > 3 自动折叠 (0/3/5 三种情况 UI 一致)

策略:
- 静态 HTML grep 验证 (快速 + 离线, 不依赖浏览器)
- 静态 JS grep 验证 (single source of truth 暴露检查)
- 用 subprocess 跑 Node.js 脚本, 在 jsdom 中实际执行 contract-review.js 验证交互逻辑
"""
from __future__ import annotations

import re
import json
import subprocess
from pathlib import Path

import pytest


# ====== 路径常量 ======

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CR_VIEWS_DIR = REPO_ROOT / "templates" / "views" / "contract-review"
CR_JS = REPO_ROOT / "assets" / "js" / "contract-review.js"
INDEX_HTML = REPO_ROOT / "index.html"

# 5 页面 (按 W4 设计稿排序: upload/result/suggestion/negotiation/export)
EXPECTED_PAGES = [
    "contract-review-upload.html",
    "contract-review-result.html",
    "contract-review-suggestion.html",
    "contract-review-negotiation.html",
    "contract-review-export.html",
]

# 4 立场 (W4 设计稿: 甲方/乙方/丙方/审查方)
# 律师常用语映射: 原告(甲方) / 被告(乙方) / 第三方(丙方) / 中立(审查方)
EXPECTED_STANCES = ["甲方", "乙方", "丙方", "审查方"]

# 3 风险等级
EXPECTED_IMPACTS = ["fatal", "major", "ok"]


# ====== P1: 移动端 < 768px 5 页面适配测试 ======

class TestMobileResponsive:
    """P1: 移动端 < 768px 5 页面适配验证

    验证项:
    - 5 页面全部存在
    - 5 页面全部含 @media (max-width: 767px) 块
    - 5 页面有 viewport meta (经 index.html 父 shell 统一提供)
    - 5 页面使用 grid 重排 (1fr 单栏)
    """

    @pytest.mark.parametrize("page_file", EXPECTED_PAGES)
    def test_page_exists(self, page_file: str):
        """5 页面存在"""
        path = CR_VIEWS_DIR / page_file
        assert path.exists(), f"页面缺失: {path}"

    @pytest.mark.parametrize("page_file", EXPECTED_PAGES)
    def test_has_mobile_media_query(self, page_file: str):
        """5 页面含 @media (max-width: 767px) 移动端适配"""
        html = (CR_VIEWS_DIR / page_file).read_text(encoding="utf-8")
        assert "@media" in html, f"{page_file}: 缺 @media 块"
        # 验证是 767px 阈值 (W4 设计约定: 移动端 < 768px)
        assert re.search(r"@media\s*\(\s*max-width\s*:\s*767px\s*\)", html), \
            f"{page_file}: 缺 @media (max-width: 767px) 块"

    @pytest.mark.parametrize("page_file", EXPECTED_PAGES)
    def test_mobile_grid_single_column(self, page_file: str):
        """5 页面移动端 grid 重排为 1fr 单栏"""
        html = (CR_VIEWS_DIR / page_file).read_text(encoding="utf-8")
        # 找 @media (max-width: 767px) 块 (用括号深度匹配, 避免被 CSS rule 的 } 提前截断)
        # 从 @media 开始, 计数 { 和 }, 平衡时结束
        start = html.find("@media (max-width: 767px)")
        assert start >= 0, f"{page_file}: 缺 @media (max-width: 767px) 块"
        # 从 { 开始
        brace_start = html.find("{", start)
        assert brace_start >= 0, f"{page_file}: @media 缺 {{"
        depth = 1
        i = brace_start + 1
        while i < len(html) and depth > 0:
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
            i += 1
        block = html[brace_start + 1: i - 1]
        # 验证有 grid-template-columns: 1fr (单栏重排, !important 可选)
        has_grid_1fr = re.search(r"grid-template-columns\s*:\s*1fr", block)
        assert has_grid_1fr, \
            f"{page_file}: 移动端 grid 未重排为 1fr 单栏"

    def test_viewport_meta_in_index_html(self):
        """viewport meta 由 index.html 父 shell 统一提供 (5 页面共享)"""
        html = INDEX_HTML.read_text(encoding="utf-8")
        # viewport meta 在 index.html 里, 顺序可能是 content 在前 name 在后
        assert re.search(r'<meta[^>]*name=["\']viewport["\']', html, re.IGNORECASE), \
            "index.html 缺 viewport meta (name='viewport')"
        # 验证 content 含 width=device-width
        vp_match = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', html, re.IGNORECASE)
        assert vp_match, "index.html 缺 viewport meta tag"
        vp_tag = vp_match.group(0)
        assert "width=device-width" in vp_tag, \
            f"viewport meta 缺 width=device-width: {vp_tag}"

    def test_contract_review_js_loaded(self):
        """index.html 加载 contract-review.js (含移动端 CSS injection)"""
        html = INDEX_HTML.read_text(encoding="utf-8")
        assert "contract-review.js" in html, "index.html 缺 contract-review.js 引用"

    def test_contract_review_js_has_applyMobileStyles(self):
        """contract-review.js 含 applyMobileStyles (JS 层移动端 CSS)"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "applyMobileStyles" in js, "contract-review.js 缺 applyMobileStyles"
        assert "max-width: 767px" in js, "applyMobileStyles 未覆盖 767px 阈值"


# ====== P2: 立场影响预览测试 ======

class TestStancePreview:
    """P2: 立场影响预览 4 立场 × 3 风险等级 加权/降权

    验证项:
    - contract-review.js 暴露 __updateStancePreview (single source of truth)
    - __updateStancePreview(stance) 返回 4 立场 × 3 影响 完整 matrix
    - 4 立场包含 W4 律师常用语映射 (原告/被告/中立)
    - 3 风险等级 fatal/major/ok 都有 sym (方向) + cls (颜色类)
    """

    def test_updateStancePreview_exported(self):
        """__updateStancePreview 是 contract-review.js 暴露的 global"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "__updateStancePreview" in js, "缺 __updateStancePreview 暴露"
        # 必须挂到 globalThis.CR 上
        assert re.search(r"globalThis\.CR\.__updateStancePreview\s*=\s*__updateStancePreview", js), \
            "__updateStancePreview 未挂到 globalThis.CR"

    def test_STANCE_MATRIX_exported(self):
        """__STANCE_MATRIX 暴露 (供测试和调试)"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "__STANCE_MATRIX" in js, "缺 __STANCE_MATRIX 暴露"

    @pytest.mark.parametrize("stance", EXPECTED_STANCES)
    def test_all_stances_in_matrix(self, stance: str):
        """STANCE_MATRIX 包含 4 立场"""
        js = CR_JS.read_text(encoding="utf-8")
        # 在 matrix 字典内查找 '甲方': { ... }
        pattern = rf"['\"]?{stance}['\"]?\s*:\s*\{{"
        assert re.search(pattern, js), f"STANCE_MATRIX 缺 {stance}"

    @pytest.mark.parametrize("stance", EXPECTED_STANCES)
    def test_stance_has_shortLabel(self, stance: str):
        """立场有 shortLabel (律师常用语: 原告/被告/第三方/中立)"""
        js = CR_JS.read_text(encoding="utf-8")
        # shortLabel 出现 4 次 (4 stance)
        matches = re.findall(r"shortLabel\s*:\s*['\"]([^'\"]+)['\"]", js)
        assert len(matches) >= 4, f"shortLabel 应有 4 个立场, 实际 {len(matches)}"
        # 含律师常用 3 词
        labels = set(matches)
        for required in ["原告", "被告", "中立"]:
            assert required in labels, f"shortLabel 缺律师常用词: {required}"

    @pytest.mark.parametrize("stance", EXPECTED_STANCES)
    @pytest.mark.parametrize("impact", EXPECTED_IMPACTS)
    def test_stance_impact_matrix_complete(self, stance: str, impact: str):
        """每个 stance 都有 3 风险等级 impact (sym + cls)"""
        js = CR_JS.read_text(encoding="utf-8")
        # 取 stance 块
        s_block = re.search(rf"['\"]?{stance}['\"]?\s*:\s*\{{(.*?)\n\s*\}}", js, re.DOTALL)
        assert s_block, f"STANCE_MATRIX 缺 {stance} 块"
        body = s_block.group(1)
        # impact: { sym: ..., cls: ... }
        imp_m = re.search(rf"{impact}\s*:\s*\{{\s*sym\s*:\s*['\"]([^'\"]+)['\"]", body)
        cls_m = re.search(rf"{impact}\s*:\s*\{{[^}}]*cls\s*:\s*['\"]([^'\"]+)['\"]", body)
        assert imp_m, f"{stance} 缺 {impact} sym"
        assert cls_m, f"{stance} 缺 {impact} cls"
        sym = imp_m.group(1)
        assert sym in ["↑ 加权", "↓ 降权", "→ 持平"], \
            f"{stance} {impact} sym 不合法: {sym}"

    def test_乙方_致命_加权(self):
        """乙方立场下致命风险加权 (W4 设计: 乙方更关注显失公平)"""
        js = CR_JS.read_text(encoding="utf-8")
        s_block = re.search(r"'乙方'\s*:\s*\{(.*?)\n\s*\}", js, re.DOTALL)
        body = s_block.group(1)
        # 乙方 致命: sym = '↑ 加权'
        fatal_m = re.search(r"fatal\s*:\s*\{\s*sym\s*:\s*['\"]↑ 加权['\"]", body)
        assert fatal_m, "乙方致命 sym 应为 ↑ 加权"

    def test_甲方_致命_降权(self):
        """甲方立场下致命风险降权 (W4 设计: 甲方相对受益方)"""
        js = CR_JS.read_text(encoding="utf-8")
        s_block = re.search(r"'甲方'\s*:\s*\{(.*?)\n\s*\}", js, re.DOTALL)
        body = s_block.group(1)
        # 甲方 致命: sym = '↓ 降权'
        fatal_m = re.search(r"fatal\s*:\s*\{\s*sym\s*:\s*['\"]↓ 降权['\"]", body)
        assert fatal_m, "甲方致命 sym 应为 ↓ 降权"

    def test_upload_html_has_stance_ui(self):
        """upload.html 有立场 UI 4 按钮 + 预览区域"""
        html = (CR_VIEWS_DIR / "contract-review-upload.html").read_text(encoding="utf-8")
        for stance in EXPECTED_STANCES:
            assert f'data-stance="{stance}"' in html, f"upload.html 缺 {stance} 按钮"
        assert 'id="cr-stance-preview"' in html, "upload.html 缺 stance preview 区域"
        assert 'id="cr-stance-preview-grid"' in html, "upload.html 缺 preview grid"
        for impact in EXPECTED_IMPACTS:
            assert f'data-stance-impact="{impact}"' in html, f"upload.html 缺 {impact} impact 元素"

    def test_5_contracts_fixture_support(self):
        """5 合同 fixture 全部存在 (W4 5 大类 baseline)"""
        fixtures_dir = REPO_ROOT / "backend" / "cases-crawler" / "data" / "fixtures" / "contract_review"
        assert fixtures_dir.is_dir(), f"fixtures 目录缺失: {fixtures_dir}"
        expected_fixtures = {"rental.json", "loan.json", "labor.json", "service.json", "sales.json"}
        actual = {f.name for f in fixtures_dir.glob("*.json")}
        assert expected_fixtures == actual, \
            f"5 fixture 不匹配: 期望 {expected_fixtures}, 实际 {actual}"


# ====== P3: 致命条款 > 3 自动折叠测试 ======

class TestFatalCollapse:
    """P3: 致命条款 > 3 自动折叠 0/3/5 三种情况 UI 一致

    验证项:
    - contract-review.js 暴露 __applyFatalCollapse(visibleLimit) (single source of truth)
    - 0/3 致命: 按钮隐藏
    - 5 致命: 按钮显示 + 折叠 4-5
    - result.html 实际 demo 数据 5 致命 (折叠可见)
    - 0/3/5 测试可经 URL ?test_fatals=0|3|5 注入
    """

    def test_applyFatalCollapse_exported(self):
        """__applyFatalCollapse 是 contract-review.js 暴露的 global"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "__applyFatalCollapse" in js, "缺 __applyFatalCollapse 暴露"
        assert re.search(r"globalThis\.CR\.__applyFatalCollapse\s*=\s*__applyFatalCollapse", js), \
            "__applyFatalCollapse 未挂到 globalThis.CR"

    def test_FATAL_VISIBLE_LIMIT_is_3(self):
        """FATAL_VISIBLE_LIMIT = 3 (D3 W8 约定: > 3 折叠)"""
        js = CR_JS.read_text(encoding="utf-8")
        m = re.search(r"FATAL_VISIBLE_LIMIT\s*=\s*(\d+)", js)
        assert m, "缺 FATAL_VISIBLE_LIMIT 常量"
        assert m.group(1) == "3", f"FATAL_VISIBLE_LIMIT 应为 3, 实际 {m.group(1)}"

    def test_applyFatalCollapse_only_counts_clause_fatal(self):
        """__applyFatalCollapse 只数 .clause-fatal (D3 W8 修复: 不含 .clause-major)"""
        js = CR_JS.read_text(encoding="utf-8")
        # 函数内应只 querySelectorAll('.clause-fatal')
        m = re.search(r"function\s+__applyFatalCollapse[^{]*\{(.*?)\n\s{4}\}", js, re.DOTALL)
        assert m, "缺 __applyFatalCollapse 函数体"
        body = m.group(1)
        assert "'.clause-fatal'" in body, "__applyFatalCollapse 未用 .clause-fatal 选择器"
        # 不应再用 .cr-fatal-clause (含 major, 不准)
        assert "'.cr-fatal-clause'" not in body, \
            "__applyFatalCollapse 仍用 .cr-fatal-clause (含 major, 不准)"

    def test_result_html_has_toggle_button(self):
        """result.html 有 fatal toggle 按钮 (id=cr-fatal-toggle)"""
        html = (CR_VIEWS_DIR / "contract-review-result.html").read_text(encoding="utf-8")
        assert 'id="cr-fatal-toggle"' in html, "result.html 缺 fatal toggle 按钮"
        assert 'id="cr-fatal-toggle-text"' in html, "result.html 缺 toggle text"
        assert 'id="cr-fatal-toggle-count"' in html, "result.html 缺 toggle count"

    def test_result_html_has_fatal_container(self):
        """result.html 有 fatal-clauses-container"""
        html = (CR_VIEWS_DIR / "contract-review-result.html").read_text(encoding="utf-8")
        assert 'id="fatal-clauses-container"' in html, "result.html 缺 fatal-clauses-container"
        assert "data-cr-panel" in html, "result.html 缺 data-cr-panel (Tab 切换)"

    def test_result_html_demo_has_5_fatals(self):
        """result.html demo 数据含 5 个致命 (D3 W8: 加了 2 个, 总 5, 触发折叠)"""
        html = (CR_VIEWS_DIR / "contract-review-result.html").read_text(encoding="utf-8")
        # 数 .clause-fatal 元素
        fatals = re.findall(r'class="[^"]*clause-fatal[^"]*"', html)
        assert len(fatals) >= 5, \
            f"result.html demo 致命条款应 >= 5, 实际 {len(fatals)} (D3 W8 加了 2 个致命)"

    def test_URL_test_fatals_injection(self):
        """contract-review.js 支持 ?test_fatals=0|3|5 URL 注入"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "test_fatals" in js, "缺 test_fatals URL param 处理"
        assert "__testInjectFatalClauses" in js, "缺 __testInjectFatalClauses 测试辅助"

    def test_3_cases_logic_0_fatals(self):
        """0 致命: 按钮隐藏, 0 overflow (D3 W8 验证)"""
        # 静态逻辑检查: 0 <= 3 路径
        js = CR_JS.read_text(encoding="utf-8")
        # 应有 `if (fatalCount <= visibleLimit) { ... btn.classList.add('hidden'); ... }`
        assert re.search(r"if\s*\(\s*fatalCount\s*<=\s*visibleLimit\s*\)", js), \
            "缺 fatalCount <= visibleLimit 早返回分支"
        assert "classList.add('hidden')" in js, "缺按钮隐藏逻辑"

    def test_3_cases_logic_3_fatals(self):
        """3 致命: 按钮隐藏, 0 overflow (刚好等于 visibleLimit)"""
        js = CR_JS.read_text(encoding="utf-8")
        # 3 <= 3 走早返回路径, 按钮 hidden
        assert "<= visibleLimit" in js, "缺 <= visibleLimit 比较"

    def test_3_cases_logic_5_fatals(self):
        """5 致命: 按钮显示, 折叠 4-5 (overflow 计数 = 2)"""
        js = CR_JS.read_text(encoding="utf-8")
        # 应有 overflow 计数逻辑: 遍历 idx >= visibleLimit 累加 hiddenCount
        assert re.search(r"idx\s*>=\s*visibleLimit", js), \
            "缺 idx >= visibleLimit 折叠分支"
        assert "hiddenCount" in js, "缺 hiddenCount 计数"


# ====== 集成: contract-review.js 语法检查 ======

class TestJSStatic:
    """contract-review.js 静态语法 + API 暴露检查"""

    def test_js_file_exists(self):
        assert CR_JS.is_file(), f"缺 {CR_JS}"

    def test_js_has_IIFE(self):
        """contract-review.js 是 IIFE 包裹 (避免全局污染)"""
        js = CR_JS.read_text(encoding="utf-8")
        # 文件以 JSDoc 注释开头, IIFE 在注释之后
        assert "(function()" in js, "contract-review.js 不是 IIFE"
        assert js.rstrip().endswith("})();"), "contract-review.js IIFE 未正确闭合"

    def test_js_uses_strict(self):
        """contract-review.js 用 strict mode"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "'use strict'" in js or '"use strict"' in js, "缺 'use strict'"

    def test_js_exposes_CR_namespace(self):
        """globalThis.CR 暴露 (调试用)"""
        js = CR_JS.read_text(encoding="utf-8")
        assert "globalThis.CR = CR" in js, "缺 globalThis.CR 暴露"


# ====== 集成: 用 Node.js 跑 jsdom 验证 stance + fatal 逻辑 ======

class TestJSDynamicRuntime:
    """用 subprocess 跑 Node.js 脚本在 jsdom 中实际执行 contract-review.js 验证

    验证 stance matrix 实际返回值 + fatal collapse 0/3/5 三种情况
    """

    JS_RUNTIME_TEST = r"""
// D3 W8 集成测试脚本: 用 vm 加载 contract-review.js, 验证 3 个核心 API
const fs = require('fs');
const path = require('path');

const result = {passed: [], failed: []};
function assert(cond, msg) {
  if (cond) result.passed.push(msg);
  else result.failed.push(msg);
}

const code = fs.readFileSync(process.argv[2], 'utf-8');

// minimal DOM mock
function makeEl(tag) {
  const classes = new Set();
  const dataset = {};
  const attrs = {};
  return {
    tagName: tag.toUpperCase(),
    classList: {
      add: (...c) => c.forEach(x => classes.add(x)),
      remove: (...c) => c.forEach(x => classes.delete(x)),
      toggle: (c, force) => {
        if (force === true) classes.add(c);
        else if (force === false) classes.delete(c);
        else if (classes.has(c)) classes.delete(c);
        else classes.add(c);
        return classes.has(c);
      },
      contains: c => classes.has(c),
    },
    dataset: new Proxy(dataset, {
      set: (t, k, v) => { t[k] = String(v); return true; },
      get: (t, k) => t[k],
    }),
    setAttribute: (k, v) => { attrs[k] = String(v); },
    getAttribute: k => attrs[k],
    hasAttribute: k => k in attrs,
    style: {},
    addEventListener: () => {},
    querySelectorAll: () => [],
    querySelector: () => null,
    appendChild: () => {},
    removeChild: () => {},
    insertBefore: () => {},
    click: () => {},
  };
}

const dom = {
  URLSearchParams,
  fetch: () => Promise.resolve({ json: () => Promise.resolve({ fixtures: [] }) }),
  console: { log: () => {}, warn: () => {}, error: () => {} },
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  document: {
    readyState: 'complete',
    addEventListener: () => {},
    createElement: makeEl,
    getElementById: () => null,
    querySelectorAll: () => [],
    querySelector: () => null,
  },
  window: {
    matchMedia: () => ({ matches: false, addEventListener: () => {} }),
  },
  globalThis: {},
};

const vm = require('vm');
const ctx = vm.createContext(dom);

// 用 try-catch 包住, 避免 boot() 副作用导致 script 中断
try {
  vm.runInContext(code, ctx);
} catch (e) {
  console.error('JS 加载异常:', e.message);
  // 继续测试 - 我们关心的是 __updateStancePreview / __applyFatalCollapse
}

// 测试 1: __updateStancePreview 暴露
const CR = ctx.globalThis.CR;
assert(!!CR, 'globalThis.CR 暴露');
assert(typeof CR.__updateStancePreview === 'function', '__updateStancePreview 是函数');
assert(typeof CR.__applyFatalCollapse === 'function', '__applyFatalCollapse 是函数');
assert(!!CR.__STANCE_MATRIX, '__STANCE_MATRIX 暴露');

// 测试 2: 4 stance × 3 impact 完整
const matrix = CR.__STANCE_MATRIX;
const stances = ['甲方', '乙方', '丙方', '审查方'];
const impacts = ['fatal', 'major', 'ok'];
for (const s of stances) {
  assert(matrix[s], 'stance ' + s + ' 存在');
  if (matrix[s]) {
    assert(matrix[s].label === s, s + ' label 正确');
    assert(typeof matrix[s].shortLabel === 'string', s + ' shortLabel 存在');
    for (const i of impacts) {
      const imp = matrix[s].impacts[i];
      assert(!!imp, s + '.' + i + ' impact 存在');
      if (imp) {
        assert(['↑ 加权', '↓ 降权', '→ 持平'].includes(imp.sym), s + '.' + i + ' sym 合法');
        assert(typeof imp.cls === 'string', s + '.' + i + ' cls 存在');
      }
    }
  }
}

// 测试 3: 乙方致命加权 (W4 设计: 乙方显失公平)
const p = matrix['乙方'];
assert(p.impacts.fatal.sym === '↑ 加权', '乙方致命加权');
assert(p.impacts.ok.sym === '↓ 降权', '乙方合规降权');

// 测试 4: 甲方致命降权 (W4 设计: 甲方相对受益)
const a = matrix['甲方'];
assert(a.impacts.fatal.sym === '↓ 降权', '甲方致命降权');

// 测试 5: 审查方持平 (W4 设计: 中立报告)
const n = matrix['审查方'];
assert(n.impacts.fatal.sym === '→ 持平', '审查方致命持平');
assert(n.impacts.major.sym === '→ 持平', '审查方重大持平');

// 测试 6: __applyFatalCollapse 返回值正确 (mock container)
let caseNum = 0;
const container = {
  id: 'fatal-clauses-container',
  style: {},
  dataset: {},
  querySelectorAll: (sel) => {
    if (sel === '.clause-fatal') {
      return Array.from({length: caseNum}, () => ({
        classList: { add: () => {}, remove: () => {} },
        style: {},
        dataset: {},
      }));
    }
    return [];
  },
};
const btn = {
  id: 'cr-fatal-toggle',
  classList: { _set: new Set(), add(c) { this._set.add(c); }, remove(c) { this._set.delete(c); }, contains(c) { return this._set.has(c); } },
  style: {},
  dataset: {},
  setAttribute: () => {},
  querySelector: () => null,
  onclick: null,
};
ctx.document.getElementById = (id) => {
  if (id === 'fatal-clauses-container') return container;
  if (id === 'cr-fatal-toggle') return btn;
  if (id === 'cr-fatal-toggle-text') return { textContent: '' };
  if (id === 'cr-fatal-toggle-count') return { textContent: '' };
  return null;
};

// 0 致命
caseNum = 0;
const r0 = CR.__applyFatalCollapse(3);
assert(r0.buttonVisible === false, '0 致命: button hidden');
assert(r0.hidden === 0, '0 致命: hidden = 0');

// 3 致命
caseNum = 3;
const r3 = CR.__applyFatalCollapse(3);
assert(r3.buttonVisible === false, '3 致命: button hidden');
assert(r3.hidden === 0, '3 致命: hidden = 0');

// 5 致命
caseNum = 5;
const r5 = CR.__applyFatalCollapse(3);
assert(r5.buttonVisible === true, '5 致命: button visible');
assert(r5.hidden === 2, '5 致命: hidden = 2');

// 测试 7: __updateStancePreview 返回值
const m1 = CR.__updateStancePreview('乙方');
assert(m1.label === '乙方', '__updateStancePreview 乙方 label');
assert(m1.shortLabel === '被告', '__updateStancePreview 乙方 shortLabel=被告');
assert(m1.impacts.fatal.sym === '↑ 加权', '__updateStancePreview 乙方致命加权');

process.stdout.write('JSON_RESULT_BEGIN\n');
process.stdout.write(JSON.stringify(result));
process.stdout.write('\nJSON_RESULT_END\n');
"""

    @pytest.mark.skipif(
        not (REPO_ROOT / "package.json").exists(),
        reason="需 package.json 跑 Node.js 集成测试"
    )
    def test_runtime_stance_and_fatal(self, tmp_path):
        """实际跑 contract-review.js 验证 stance + fatal 0/3/5 三种 case"""
        script = tmp_path / "d3_runtime_test.js"
        script.write_text(self.JS_RUNTIME_TEST, encoding="utf-8")
        proc = subprocess.run(
            ["node", str(script), str(CR_JS)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
        )
        # 解析 JSON_RESULT_BEGIN/END 之间的输出
        out = proc.stdout
        data = {}
        if "JSON_RESULT_BEGIN" in out:
            start = out.find("JSON_RESULT_BEGIN") + len("JSON_RESULT_BEGIN")
            end = out.find("JSON_RESULT_END", start)
            json_str = out[start:end].strip()
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                pytest.fail(f"JSON 解析失败: {e}\nstdout: {out}\nstderr: {proc.stderr}")
        else:
            pytest.fail(f"Node.js 未输出 JSON_RESULT marker\nstdout: {out}\nstderr: {proc.stderr}")
        if data.get("failed"):
            pytest.fail(f"集成测试失败: {data['failed']}")
        # 期望至少 25+ passed
        assert len(data.get("passed", [])) >= 25, \
            f"集成测试 passed 不足 25, 实际 {len(data.get('passed', []))}: {data}"
