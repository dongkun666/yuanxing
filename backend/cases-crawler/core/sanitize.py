"""
LexPrime 数据脱敏工具
2026-06-28 · 严格遵循自建战略的合规边界

合规原则:
1. 只爬取/存储公开数据
2. 自动脱敏: 身份证 / 手机号 / 详细住址 / 银行卡 / 邮箱 (部分场景)
3. 标注数据来源 + 抓取时间
4. 律所数据隔离 (multi-tenant)
"""
import re
from typing import Optional


# 脱敏正则
ID_CARD_PATTERN = re.compile(r'\b[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b')
MOBILE_PATTERN = re.compile(r'\b1[3-9]\d{9}\b')
BANK_CARD_PATTERN = re.compile(r'\b\d{16,19}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# 地址脱敏: 详细住址 → 保留到区/县
ADDRESS_DETAIL_PATTERN = re.compile(r'([\u4e00-\u9fa5]{2,8}(?:省|自治区|直辖市))[\u4e00-\u9fa5]{0,30}(?:市|区|县)[\u4e00-\u9fa50-9a-zA-Z]+')


def sanitize_id_card(text: str) -> str:
    """脱敏身份证号: 保留前 6 位 + **** + 后 4 位"""
    if not text:
        return text
    return ID_CARD_PATTERN.sub(lambda m: m.group()[:6] + '********' + m.group()[-4:], text)


def sanitize_mobile(text: str) -> str:
    """脱敏手机号: 保留前 3 位 + **** + 后 4 位"""
    if not text:
        return text
    return MOBILE_PATTERN.sub(lambda m: m.group()[:3] + '****' + m.group()[-4:], text)


def sanitize_bank_card(text: str) -> str:
    """脱敏银行卡号"""
    if not text:
        return text
    return BANK_CARD_PATTERN.sub(lambda m: m.group()[:4] + '********' + m.group()[-4:], text)


def sanitize_email(text: str, keep: bool = True) -> str:
    """脱敏邮箱: 保留域名, 用户名脱敏"""
    if not text or not keep:
        return text
    return EMAIL_PATTERN.sub(lambda m: '***@' + m.group().split('@')[1], text)


def sanitize_address(address: str, level: str = "district") -> str:
    """
    脱敏地址: 保留到区/县级
    level: 'province' / 'city' / 'district'
    """
    if not address:
        return address
    # 简化处理: 截断到区县级
    m = re.match(r'([\u4e00-\u9fa5]{2,8}(?:省|自治区|直辖市))?([\u4e00-\u9fa5]{2,30}(?:市))?([\u4e00-\u9fa5]{2,30}(?:区|县))?', address)
    if not m:
        return address[:12] + '***' if len(address) > 12 else address

    if level == "province":
        return m.group(1) or address[:6]
    elif level == "city":
        return (m.group(1) or '') + (m.group(2) or '')
    else:  # district
        return (m.group(1) or '') + (m.group(2) or '') + (m.group(3) or '')


def sanitize_person_name(name: str) -> str:
    """脱敏人名: 姓 + * (如 张*明)"""
    if not name or len(name) < 2:
        return name
    if len(name) == 2:
        return name[0] + '*'
    return name[0] + '*' * (len(name) - 2) + name[-1]


def sanitize_full_text(html: str) -> str:
    """
    全文脱敏入口: 对 HTML 文本进行 PII 脱敏
    """
    if not html:
        return html
    text = html
    text = sanitize_id_card(text)
    text = sanitize_mobile(text)
    text = sanitize_bank_card(text)
    return text


def html_to_plain(html: str) -> str:
    """
    HTML → 纯文本 (去除标签, 保留段落结构)
    """
    if not html:
        return ''
    # 替换段落/换行为 \n
    text = re.sub(r'</?p[^>]*>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # 去除其他标签
    text = re.sub(r'<[^>]+>', '', text)
    # 解码 HTML entities
    import html as html_lib
    text = html_lib.unescape(text)
    # 压缩空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def classify_cause(cause: str) -> tuple[str, str]:
    """
    案由自动分类 → (cause_category, cause_color)
    8 大分类: 合同/婚姻家事/侵权/刑事/行政/知产/执行/其他
    """
    if not cause:
        return "其他", "gray"

    cause_lower = cause.lower()

    if any(kw in cause for kw in ['合同', '买卖', '借款', '租赁', '承揽', '担保', '保险', '金融']):
        return "合同纠纷", "blue"
    if any(kw in cause for kw in ['婚姻', '离婚', '继承', '抚养', '赡养', '收养']):
        return "婚姻家事", "pink"
    if any(kw in cause for kw in ['侵权', '损害', '人身', '产品责任', '医疗', '交通']):
        return "侵权责任", "orange"
    if any(kw in cause for kw in ['刑事', '诈骗', '盗窃', '抢劫', '故意伤害', '毒品', '贪污', '受贿']):
        return "刑事", "red"
    if any(kw in cause for kw in ['行政', '行政复议', '国家赔偿', '行政处罚']):
        return "行政", "purple"
    if any(kw in cause for kw in ['专利', '商标', '著作权', '商业秘密', '知识产权']):
        return "知识产权", "indigo"
    if any(kw in cause for kw in ['执行', '失信', '限高', '终结']):
        return "执行", "gray"

    return "其他", "gray"


def extract_year(date_str: str) -> Optional[int]:
    """从日期字符串提取年份"""
    if not date_str:
        return None
    m = re.search(r'(\d{4})', date_str)
    return int(m.group(1)) if m else None


# 单元测试
if __name__ == "__main__":
    print(sanitize_id_card("张三的身份证是110101199003078811"))
    print(sanitize_mobile("联系电话: 13812345678"))
    print(sanitize_address("北京市朝阳区建国路88号SOHO现代城A座1501室"))
    print(sanitize_person_name("张明"))
    print(classify_cause("买卖合同纠纷"))
    print(classify_cause("故意伤害罪"))
    print(extract_year("2024-05-15"))
    print(html_to_plain("<p>这是<p>第一段</p>这是第二段</p>"))
