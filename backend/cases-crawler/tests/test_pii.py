"""
W5 Track B: PII 脱敏测试 (lex-ai)

10 case 覆盖:
- 身份证 / 手机 / 银行卡 / 邮箱 / 地址 / 人名 各 1 case
- 多 PII 混合 / 无 PII / 边界 / OCR 模拟
- PiiReport 字段正确性

PRD B-ocr Track · 验收: "PII 自动脱敏 100% (10 case 验证)"
"""
from __future__ import annotations

from core.pii import sanitize_for_review, PiiReport


# ===== 10 case 必过 =====

class TestPiiSanitize:

    def test_case_1_id_card(self):
        """case 1: 身份证 18 位 (前 4 后 4 保留)"""
        text = "张三的身份证号是 110101199003078811"
        out, rpt = sanitize_for_review(text)
        assert "1101********8811" in out
        assert rpt.id_card_count == 1
        assert rpt.total == 1

    def test_case_2_mobile(self):
        """case 2: 手机号"""
        text = "联系电话: 13812345678"
        out, rpt = sanitize_for_review(text)
        assert "138****5678" in out
        assert rpt.mobile_count == 1
        assert "13812345678" not in out

    def test_case_3_bank_card(self):
        """case 3: 银行卡 19 位"""
        text = "收款卡号: 6222600012345678901"
        out, rpt = sanitize_for_review(text)
        assert "6222********8901" in out
        assert rpt.bank_card_count == 1

    def test_case_4_email(self):
        """case 4: 邮箱"""
        text = "邮箱: zhang.san@example.com"
        out, rpt = sanitize_for_review(text)
        assert "***@example.com" in out
        assert "zhang.san" not in out
        assert rpt.email_count == 1

    def test_case_5_address(self):
        """case 5: 地址 (直辖市)"""
        text = "送达地址: 北京市朝阳区建国路 88 号 SOHO 现代城 A 座 1501 室"
        out, rpt = sanitize_for_review(text)
        # 详细地址 (路/号/座/室) 已被 mask, 保留 "北京市朝阳区"
        assert "北京市朝阳区" in out
        assert "1501" not in out
        assert rpt.address_count >= 1

    def test_case_6_person_name(self):
        """case 6: 人名 (上下文启发)"""
        text = "甲方: 张三, 乙方: 李四"
        out, rpt = sanitize_for_review(text)
        # 2-字姓名 → 姓 + "*"
        assert "张*" in out
        assert "李*" in out
        assert rpt.person_name_count == 2

    def test_case_7_mixed_pii(self):
        """case 7: 多 PII 混合 (合同审查常见)"""
        text = (
            "甲方: 张三 (身份证 110101199003078811)\n"
            "乙方: 李四 (手机 13812345678)\n"
            "邮箱: contract@example.com\n"
            "地址: 上海市浦东新区张江路 100 号"
        )
        out, rpt = sanitize_for_review(text)
        assert rpt.id_card_count == 1
        assert rpt.mobile_count == 1
        assert rpt.email_count == 1
        assert rpt.address_count >= 1
        assert rpt.person_name_count == 2
        assert rpt.total >= 5
        # 原始字符串不应再出现
        assert "110101199003078811" not in out
        assert "13812345678" not in out
        assert "zhang.san@".replace("zhang.san", "contract") not in out  # contract 没被识别
        # 但 contract@example.com 应被 mask
        assert "***@example.com" in out

    def test_case_8_no_pii(self):
        """case 8: 无 PII (纯合同条款, 避免甲方/乙方等人名触发)"""
        text = (
            "第一条 租赁标的\n"
            "出租方将位于上海市浦东新区的房屋交付给承租方使用。\n"
            "第二条 租赁期限\n"
            "租赁期限为 12 个月。\n"
        )
        out, rpt = sanitize_for_review(text)
        assert out == text  # 无 PII, 不变
        assert rpt.total == 0

    def test_case_9_ocr_realistic(self):
        """case 9: OCR 识别典型输出 (含断行/换行)"""
        text = (
            "借款合同\n\n"
            "出借人: 王五\n"
            "借款人: 赵六\n"
            "身份证号: 110108198506152233\n"
            "手机: 13987654321\n"
            "借款金额: 500000 元\n"
            "借款期限: 2026 年 1 月至 2027 年 1 月\n"
            "年利率: 18%\n"
        )
        out, rpt = sanitize_for_review(text)
        assert rpt.id_card_count == 1
        assert rpt.mobile_count == 1
        assert rpt.person_name_count >= 1
        # 关键金额和期限保留
        assert "500000" in out
        assert "18%" in out

    def test_case_10_boundary(self):
        """case 10: 边界 - 空文本 / 长文本"""
        # 空
        out, rpt = sanitize_for_review("")
        assert out == ""
        assert rpt.total == 0
        # 长文本 (>5000 字, 不 break)
        text = "借款合同\n甲方: 张三\n身份证 110101199003078811\n手机 13812345678\n" * 100
        out, rpt = sanitize_for_review(text)
        assert rpt.id_card_count == 100
        assert rpt.mobile_count == 100


# ===== PiiReport =====

class TestPiiReport:

    def test_to_dict_fields(self):
        rpt = PiiReport(id_card_count=2, mobile_count=1, total=3)
        d = rpt.to_dict()
        assert d["id_card_count"] == 2
        assert d["total"] == 3
        assert "samples" in d

    def test_samples_capped_at_5(self):
        rpt = PiiReport()
        for i in range(10):
            rpt.add("mobile", f"1381234567{i}", f"138****567{i}")
        d = rpt.to_dict()
        assert len(d["samples"]) == 5  # to_dict 截断

    def test_add_increments(self):
        rpt = PiiReport()
        rpt.add("id_card", "110101199003078811", "1101********8811")
        assert len(rpt.samples) == 1
        assert rpt.samples[0]["type"] == "id_card"
