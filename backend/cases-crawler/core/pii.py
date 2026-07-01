"""
LexPrime OCR 文本 PII 脱敏 (W5 Track B)

复用 core.sanitize 的 PII 正则, 增加:
- 报告机制 (哪些被脱敏, 多少个)
- 一站式 sanitize_for_review(text) 入口
- 面向 OCR 文本 (可能含空行/段位, 优化 regex 应用)

PII 规则 (W5 stop when):
- 身份证: 保留前 4 后 4, 中间 8 位 mask
- 手机号: 保留前 3 后 4, 中间 mask
- 银行卡: 保留前 4 后 4, 中间 mask
- 地址: 保留到区/县, 详细地址 mask
- 邮箱: 用户名 mask, 保留域名
- 人名: 姓 + *, 单名不变

参考: core.sanitize.py (W1 已实现基础 PII), 本模块是其面向 OCR 的扩展
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import List

from core.sanitize import (
    sanitize_address,
    sanitize_person_name,
)


@dataclass
class PiiReport:
    """PII 脱敏报告 (供前端展示 + 律师审计)"""

    id_card_count: int = 0
    mobile_count: int = 0
    bank_card_count: int = 0
    email_count: int = 0
    address_count: int = 0
    person_name_count: int = 0
    total: int = 0
    samples: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        # samples 保留前 5
        d["samples"] = d["samples"][:5]
        return d

    def add(self, pii_type: str, original: str, sanitized: str) -> None:
        self.samples.append({
            "type": pii_type,
            "original": original,
            "sanitized": sanitized,
        })


# 预编译的 detect 正则 (基于 sanitize.py 的 pattern, 用于计数)
# 身份证 (18 位): 1[非零] + 5 地区 + 年月日 + 3 序号 + 校验位
# 用 (?:^|[^\d]) / (?=[^\d]|$) 模拟 \b, 兼容中文/英文边界
_ID_CARD_DETECT = re.compile(
    r'(?:^|[^\d])([1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?=[^\d]|$)'
)
# 改写为不带 capture 的版本, 匹配完整数字
_ID_CARD_DETECT = re.compile(
    r'(?<![0-9])([1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?![0-9])'
)
_MOBILE_DETECT = re.compile(r'(?<![0-9])(1[3-9]\d{9})(?![0-9])')
_BANK_DETECT = re.compile(r'(?<![0-9])(\d{16,19})(?![0-9])')
_EMAIL_DETECT = re.compile(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})')
# 地址: (省/直辖市) + (市) + 区/县 + 详细 (允许数字/字母/中文混合)
# 兼容: "北京市朝阳区..." (直辖市为省级), "广东省深圳市南山区..." (省+市+区)
# 严格: 必须含 "路/街/道/号/楼/室/栋" 等具体地址标识, 避免误吞 "上海市浦东新区的房屋"
_ADDRESS_DETECT = re.compile(
    r'(?:[\u4e00-\u9fa5]{2,8}(?:省|自治区|直辖市))?'
    r'[\u4e00-\u9fa5]{2,20}市'
    r'[\u4e00-\u9fa5]{2,20}(?:区|县)'
    r'[\u4e00-\u9fa5A-Za-z0-9\s]{0,40}'
    r'(?:路|街|道|巷|弄|号|室|楼|栋|座|单元|层|院|园|苑|村|镇|乡|里|城|幢|号院)'
)

# 人名启发 (上下文): 角色 + 冒号/括号 + 2-4 字姓名
# 兼容中文冒号 (:) 和 ASCII 冒号 (:)
_NAME_CONTEXT = re.compile(
    r'(?:甲方|乙方|丙方|出借人|借款人|委托方|受托方|用人单位|劳动者|卖方|买方|姓名|当事人|律师|代理人|经办人)'
    r'[\s::()（【]*'
    r'([\u4e00-\u9fa5]{2,4})'
    r'(?=[\s,,,。;;、]|$)',
    re.UNICODE,
)


def _count(pattern: re.Pattern, text: str) -> int:
    return len(pattern.findall(text))


def _replace_with_capture(
    text: str, pattern: re.Pattern, replacer
) -> tuple[str, list]:
    """替换 pattern.group(1) 形式的匹配, 保留前后字符不变

    Args:
        text: 原文本
        pattern: 含 1 个 capture group 的正则
        replacer: callable(original_match_str) -> masked_str

    Returns:
        (new_text, list_of_originals)
    """
    originals: list = []
    def _sub(m: re.Match) -> str:
        original = m.group(1)
        originals.append(original)
        return m.group(0).replace(original, replacer(original), 1)
    new_text = pattern.sub(_sub, text)
    return new_text, originals


def sanitize_for_review(text: str) -> tuple[str, PiiReport]:
    """OCR 文本 PII 脱敏 (供 reviewer.run_skill 入参使用)

    Args:
        text: OCR 识别的原始文本

    Returns:
        (sanitized_text, report) 报告含各类 PII 数量 + 样例

    Note:
        - 银行卡 pattern 会和身份证重叠 (18 位), 优先匹配身份证
        - 邮箱和人名不重叠
        - 地址用更宽泛的 pattern, 包含路/号等
    """
    if not text:
        return text, PiiReport()

    report = PiiReport()
    sanitized = text

    # 1) 身份证 (优先, 避免被银行卡 regex 误吞)
    sanitized, originals = _replace_with_capture(
        sanitized, _ID_CARD_DETECT,
        lambda s: s[:4] + "********" + s[-4:],
    )
    report.id_card_count = len(originals)
    for o in originals[:3]:
        report.add("id_card", o, o[:4] + "********" + o[-4:])

    # 2) 手机号
    sanitized, originals = _replace_with_capture(
        sanitized, _MOBILE_DETECT,
        lambda s: s[:3] + "****" + s[-4:],
    )
    report.mobile_count = len(originals)
    for o in originals[:3]:
        report.add("mobile", o, o[:3] + "****" + o[-4:])

    # 3) 银行卡 (排除已被识别为身份证的)
    sanitized, originals = _replace_with_capture(
        sanitized, _BANK_DETECT,
        lambda s: s[:4] + "********" + s[-4:],
    )
    report.bank_card_count = len(originals)
    for o in originals[:3]:
        report.add("bank_card", o, o[:4] + "********" + o[-4:])

    # 4) 邮箱
    sanitized, originals = _replace_with_capture(
        sanitized, _EMAIL_DETECT,
        lambda s: "***@" + s.split("@", 1)[1] if "@" in s else "***",
    )
    report.email_count = len(originals)
    for o in originals[:3]:
        report.add("email", o, "***@" + o.split("@", 1)[1])

    # 5) 地址
    def _addr_repl(m: re.Match) -> str:
        original = m.group(0)
        return sanitize_address(original, level="district")
    addr_matches = list(_ADDRESS_DETECT.finditer(sanitized))
    report.address_count = len(addr_matches)
    for m in addr_matches[:5]:
        report.add("address", m.group(0), sanitize_address(m.group(0), level="district"))
    sanitized = _ADDRESS_DETECT.sub(_addr_repl, sanitized)

    # 6) 人名 (上下文启发)
    name_matches = list(_NAME_CONTEXT.finditer(sanitized))
    report.person_name_count = len(name_matches)
    for m in name_matches[:10]:
        original_name = m.group(1)
        masked = sanitize_person_name(original_name)
        # 替换 group(1) 为 masked, group(0) 整体不变
        sanitized = sanitized.replace(
            m.group(0),
            m.group(0).replace(original_name, masked, 1),
            1,
        )
        report.add("person_name", original_name, masked)

    report.total = (
        report.id_card_count
        + report.mobile_count
        + report.bank_card_count
        + report.email_count
        + report.address_count
        + report.person_name_count
    )
    return sanitized, report


# ===== 单元自测 =====

if __name__ == "__main__":
    cases = [
        "张三的身份证是110101199003078811",
        "联系电话: 13812345678, 备用 13987654321",
        "银行卡号 6222600012345678901",
        "邮箱 zhang.san@example.com",
        "地址: 北京市朝阳区建国路 88 号 SOHO 现代城 A 座 1501 室",
        "甲方: 张三, 身份证号 110101199003078811",
        "乙方 (受托方): 李四四",
    ]
    for c in cases:
        san, rep = sanitize_for_review(c)
        print(f"\n>> IN:  {c}")
        print(f"   OUT: {san}")
        print(f"   RPT: total={rep.total} "
              f"(id={rep.id_card_count}, mob={rep.mobile_count}, "
              f"bank={rep.bank_card_count}, email={rep.email_count}, "
              f"addr={rep.address_count}, name={rep.person_name_count})")
