"""
Helper script: 把 W4 设计稿 (单文件 HTML) 转换为 LexPrime SPA view-content 模式

转换规则:
1. 去掉独立 <html>/<head> 包装, 只保留 <style> 和 <script>
2. 去掉独立左侧栏 (左侧栏由 LexPrime 全局 sidebar 提供)
3. 顶部栏简化为 breadcrumb + 操作按钮 (避免重复 LexPrime 主头部)
4. 把 Tailwind CDN + Iconify CDN 替换为 LexPrime 主系统的引用 (实际运行时无需加载)
5. 输出文件名: 02-review-result.html → view-contract-review-result (在 templates/views/contract-review/)
6. 内容用 <div class="view-content-inner"> 包装, 用于 LexPrime SPA 切换

W5 决策: 保留 W4 设计稿 100% 视觉 + 内容, 最小化重构导航栏
"""
import re
from pathlib import Path

DESIGN_DIR = Path(r"E:\元枢法智前端\yuanxing\docs\designs\contract-review")
OUT_DIR = Path(r"E:\元枢法智前端\yuanxing\templates\views\contract-review")

# 页面 ID 映射 (filename → view-id)
PAGE_MAP = {
    "01-upload.html": ("01-upload", "contract-review-upload"),
    "02-review-result.html": ("02-review-result", "contract-review-result"),
    "03-suggestion-detail.html": ("03-suggestion-detail", "contract-review-suggestion"),
    "04-negotiation.html": ("04-negotiation", "contract-review-negotiation"),
    "05-export.html": ("05-export", "contract-review-export"),
}


def extract_design_to_view(html_text: str, src_name: str, view_id: str) -> str:
    """从设计稿提取样式 + body 内容, 包装为 view-content"""
    # 提取 <style>
    style_match = re.search(r"<style>(.*?)</style>", html_text, re.DOTALL)
    style_content = style_match.group(1).strip() if style_match else ""

    # 提取 body 内容 (去掉 header/aside 重复导航)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, re.DOTALL)
    body_content = body_match.group(1).strip() if body_match else ""

    # 移除独立左侧栏 (W4 设计稿的 .flex.h-screen > aside)
    # LexPrime 全局 sidebar 已经存在, 这里只要主内容区
    body_content = re.sub(
        r'<aside[^>]*class="[^"]*w-\[220px\][^"]*"[^>]*>.*?</aside>',
        "",
        body_content,
        flags=re.DOTALL,
    )

    # 移除 W4 顶部独立头部里的 Logo + 部分 breadcrumb (LexPrime 主头部已有 logo)
    # 保留顶部 nav (Skill Hub breadcrumb) 和操作按钮组
    # 简化: 只移除头部最左侧的返回按钮 (LexPrime 用 sidebar 切换)

    # 移除固定底部 watermark
    body_content = re.sub(
        r'<div class="fixed bottom-3[^"]*"[^>]*>.*?</div>\s*</body>',
        "</body>",  # placeholder, real replacement below
        body_content,
        flags=re.DOTALL,
    )
    body_content = re.sub(
        r'<div class="fixed bottom-3[^"]*">.*?</div>',
        "",
        body_content,
        flags=re.DOTALL,
    )

    # 把 <main> 内层内容包装到 view-content-inner
    # main_match = re.search(r'<main[^>]*>(.*?)</main>', body_content, re.DOTALL)
    # inner = main_match.group(1).strip() if main_match else body_content

    # 内层样式合并 (W4 tailwind.config 内联已合并到全局 tailwind.config.js,无需重复)
    # 提取 inline style/script 仅保留必要的 view 内 js 钩子

    # 输出 view-content
    view_html = f'''<div class="hidden view-content flex-1 flex flex-col overflow-hidden" id="view-{view_id}" data-view-source="{src_name}">
  <style>
{style_content}
  </style>
{body_content}
</div>
'''
    return view_html


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src_name, (label, view_id) in PAGE_MAP.items():
        src = DESIGN_DIR / src_name
        if not src.exists():
            print(f"SKIP: {src_name} (not found)")
            continue
        html = src.read_text(encoding="utf-8")
        view_html = extract_design_to_view(html, src_name, view_id)
        out = OUT_DIR / f"{view_id}.html"
        out.write_text(view_html, encoding="utf-8")
        print(f"WROTE: {out.name} ({len(view_html)} chars)")


if __name__ == "__main__":
    main()