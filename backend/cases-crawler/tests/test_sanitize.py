"""
数据脱敏模块单元测试
测试 core/sanitize.py 中的所有脱敏函数
"""
import pytest

from core.sanitize import (
    sanitize_id_card,
    sanitize_mobile,
    sanitize_bank_card,
    sanitize_email,
    sanitize_address,
    sanitize_person_name,
    sanitize_full_text,
    html_to_plain,
    classify_cause,
    extract_year,
)


class TestSanitizeIdCard:
    """身份证脱敏测试"""

    def test_valid_id_card(self):
        """有效身份证脱敏"""
        result = sanitize_id_card("110101199003078811")
        assert result == "110101********8811"
        assert len(result) == 18

    def test_id_card_in_text(self):
        """文本中的身份证（英文边界）"""
        text = "ID: 110101199003078811 is valid"
        result = sanitize_id_card(text)
        assert "110101********8811" in result
        assert "110101199003078811" not in result

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_id_card("") == ""

    def test_none(self):
        """None 输入"""
        assert sanitize_id_card(None) is None

    def test_no_id_card(self):
        """没有身份证的文本"""
        text = "这是一段普通文本"
        assert sanitize_id_card(text) == text


class TestSanitizeMobile:
    """手机号脱敏测试"""

    def test_valid_mobile(self):
        """有效手机号脱敏"""
        result = sanitize_mobile("13812345678")
        assert result == "138****5678"
        assert len(result) == 11

    def test_mobile_in_text(self):
        """文本中的手机号"""
        text = "联系电话: 13812345678 欢迎来电"
        result = sanitize_mobile(text)
        assert "138****5678" in result
        assert "13812345678" not in result

    def test_multiple_mobiles(self):
        """多个手机号"""
        text = "手机1: 13812345678, 手机2: 13987654321"
        result = sanitize_mobile(text)
        assert "138****5678" in result
        assert "139****4321" in result

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_mobile("") == ""

    def test_no_mobile(self):
        """没有手机号的文本"""
        text = "这是一段普通文本"
        assert sanitize_mobile(text) == text


class TestSanitizeBankCard:
    """银行卡脱敏测试"""

    def test_valid_bank_card_16(self):
        """16位银行卡号"""
        result = sanitize_bank_card("6222600012345678")
        assert result == "6222********5678"
        assert len(result) == 16

    def test_valid_bank_card_19(self):
        """19位银行卡号（固定8个星号）"""
        result = sanitize_bank_card("6222600012345678901")
        assert result == "6222********8901"
        assert result.startswith("6222")
        assert result.endswith("8901")

    def test_bank_card_in_text(self):
        """文本中的银行卡号"""
        text = "银行卡号: 6222600012345678901"
        result = sanitize_bank_card(text)
        assert "6222********8901" in result

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_bank_card("") == ""


class TestSanitizeEmail:
    """邮箱脱敏测试"""

    def test_valid_email(self):
        """有效邮箱脱敏"""
        result = sanitize_email("zhangsan@example.com")
        assert result == "***@example.com"
        assert "@" in result

    def test_email_in_text(self):
        """文本中的邮箱"""
        text = "请发送到 zhang.san@test.com 谢谢"
        result = sanitize_email(text)
        assert "***@test.com" in result
        assert "zhang.san@test.com" not in result

    def test_email_keep_false(self):
        """keep=False 不脱敏"""
        text = "email: test@example.com"
        result = sanitize_email(text, keep=False)
        assert result == text

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_email("") == ""


class TestSanitizeAddress:
    """地址脱敏测试"""

    def test_full_address_district(self):
        """完整地址 - 区县级"""
        addr = "北京市朝阳区建国路88号SOHO现代城A座1501室"
        result = sanitize_address(addr, level="district")
        assert "北京市朝阳区" in result

    def test_address_city_level(self):
        """地址 - 市级"""
        addr = "广东省深圳市南山区科技园路1号"
        result = sanitize_address(addr, level="city")
        assert "广东省深圳市" in result
        assert "南山区" not in result

    def test_address_province_level(self):
        """地址 - 省级"""
        addr = "浙江省杭州市西湖区文三路100号"
        result = sanitize_address(addr, level="province")
        assert "浙江省" in result
        assert "杭州市" not in result

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_address("") == ""

    def test_short_address(self):
        """短地址"""
        addr = "北京市"
        result = sanitize_address(addr)
        assert result is not None


class TestSanitizePersonName:
    """人名脱敏测试"""

    def test_two_char_name(self):
        """两字姓名"""
        assert sanitize_person_name("张三") == "张*"

    def test_three_char_name(self):
        """三字姓名"""
        assert sanitize_person_name("张三丰") == "张*丰"

    def test_four_char_name(self):
        """四字姓名"""
        assert sanitize_person_name("欧阳锋") == "欧*锋"
        assert sanitize_person_name("司马相如") == "司**如"

    def test_single_char(self):
        """单字"""
        assert sanitize_person_name("张") == "张"

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_person_name("") == ""


class TestSanitizeFullText:
    """全文脱敏测试"""

    def test_full_text_sanitize(self):
        """包含多种 PII 的全文"""
        text = """
        ID: 110101199003078811
        联系电话: 13812345678
        银行卡号: 6222600012345678901
        """
        result = sanitize_full_text(text)
        assert "110101********8811" in result
        assert "138****5678" in result
        assert "6222********8901" in result

    def test_empty_string(self):
        """空字符串"""
        assert sanitize_full_text("") == ""


class TestHtmlToPlain:
    """HTML 转纯文本测试"""

    def test_simple_html(self):
        """简单 HTML"""
        html = "<p>Hello World</p>"
        result = html_to_plain(html)
        assert "Hello World" in result

    def test_html_with_br(self):
        """带 br 的 HTML"""
        html = "第一行<br>第二行"
        result = html_to_plain(html)
        assert "第一行" in result
        assert "第二行" in result

    def test_html_with_tags(self):
        """多种标签"""
        html = "<div><p>段落1</p><p>段落2</p></div>"
        result = html_to_plain(html)
        assert "段落1" in result
        assert "段落2" in result

    def test_empty_string(self):
        """空字符串"""
        assert html_to_plain("") == ""

    def test_html_entities(self):
        """HTML 实体解码"""
        html = "&lt;p&gt;Hello&lt;/p&gt;"
        result = html_to_plain(html)
        assert "<p>Hello</p>" in result


class TestClassifyCause:
    """案由分类测试"""

    def test_contract_dispute(self):
        """合同纠纷"""
        category, color = classify_cause("买卖合同纠纷")
        assert category == "合同纠纷"
        assert color == "blue"

    def test_marriage_family(self):
        """婚姻家事"""
        category, color = classify_cause("离婚纠纷")
        assert category == "婚姻家事"
        assert color == "pink"

    def test_tort_liability(self):
        """侵权责任"""
        category, color = classify_cause("机动车交通事故责任纠纷")
        assert category == "侵权责任"
        assert color == "orange"

    def test_criminal(self):
        """刑事"""
        category, color = classify_cause("诈骗罪")
        assert category == "刑事"
        assert color == "red"

    def test_administrative(self):
        """行政"""
        category, color = classify_cause("行政处罚")
        assert category == "行政"
        assert color == "purple"

    def test_ip(self):
        """知识产权"""
        category, color = classify_cause("商标专用权纠纷")
        assert category == "知识产权"
        assert color == "indigo"

    def test_execution(self):
        """执行"""
        category, color = classify_cause("失信被执行人")
        assert category == "执行"
        assert color == "gray"

    def test_other(self):
        """其他"""
        category, color = classify_cause("不知名的纠纷")
        assert category == "其他"
        assert color == "gray"

    def test_empty_string(self):
        """空字符串"""
        category, color = classify_cause("")
        assert category == "其他"
        assert color == "gray"


class TestExtractYear:
    """年份提取测试"""

    def test_standard_date(self):
        """标准日期格式"""
        assert extract_year("2024-05-15") == 2024

    def test_chinese_date(self):
        """中文日期"""
        assert extract_year("2023年10月1日") == 2023

    def test_year_only(self):
        """仅年份"""
        assert extract_year("2025") == 2025

    def test_no_year(self):
        """没有年份"""
        assert extract_year("没有日期") is None

    def test_empty_string(self):
        """空字符串"""
        assert extract_year("") is None
