# W14 first-paid-triggers-729 — 5 律师邮箱列表

**任务**: W15 w14-followup-fixes · lex-coder · 2026-06-30
**触发时间**: 2026-07-23 09:00 CST (提前 6 天, scripts/trigger-paid-email-723.sh cron)
**配套 JSON**: `scripts/lawyer-emails.json` (邮箱 → 邀请码 mapping)
**配套 SMTP**: `scripts/smtp-credentials.env.example` → 7/22 总指挥填实

---

## 1. 5 律师邮箱名单 (公测前 7/22 总指挥填实)

> ⚠️ **当前所有邮箱为 placeholder (`l{1-5}.founding@lexprime.cn`)**.
> 公测前 7/22 总指挥用真实律师邮箱替换, 同时更新 `scripts/lawyer-emails.json` 的 `email` 字段.
> 邀请码 (`BETA2025-0001 ~ 0005`) 已固化, 不需修改.

| Slot | 律师姓名 (placeholder) | 律师背景 | 律所/公司 | 邮箱 (placeholder → 待填实) | 邀请码 | 试用起 | 试用止 | 触发通道 | 优先级 |
|------|-----------------------|---------|----------|--------------------------|--------|--------|--------|----------|--------|
| L1   | `<公测前填实 - 主办律师>` | 主办律师 | `<公测前填实>` | `l1.founding@lexprime.cn` | `BETA2025-0001` | 2026-07-26 | 2026-07-29 | email | P0 |
| L2   | `<公测前填实 - 小型合伙人>` | 小型合伙人 | `<公测前填实>` | `l2.founding@lexprime.cn` | `BETA2025-0002` | 2026-07-26 | 2026-07-29 | email | P0 |
| L3   | `<公测前填实 - 独立青年律师>` | 独立青年律师 | `<公测前填实>` | `l3.founding@lexprime.cn` | `BETA2025-0003` | 2026-07-26 | 2026-07-29 | email | P0 |
| L4   | `<公测前填实 - 高级合伙人>` | 高级合伙人 (W12 重跑) | `<公测前填实 - 中所>` | `l4.founding@lexprime.cn` | `BETA2025-0004` | 2026-07-26 | 2026-08-25 | email | P1 |
| L5   | `<公测前填实 - 企业法务>` | 企业法务 (W12 重跑) | `<公测前填实 - 公司>` | `l5.founding@lexprime.cn` | `BETA2025-0005` | 2026-07-26 | 2026-08-25 | email | P1 |

> **批次说明**:
> - L1/L2/L3 = 首批 5 律师 (W6 评审期, 2026-07-29 试用到期) — 7/23 cron 触发提前 6 天邮件
> - L4/L5 = W12 重跑律师 (2026-08-25 试用到期) — 8/19 cron 触发提前 6 天邮件 (W15 l4l5-triggers-825 落地)

---

## 2. 公测前 7/22 总指挥填实 Checklist

- [ ] 联系 L1 律师 (评审律师 W6 主办律师) → 拿真实邮箱 + 确认 7/29 试用到期
- [ ] 联系 L2 律师 (W6 小型合伙人) → 拿真实邮箱 + 确认 7/29 试用到期
- [ ] 联系 L3 律师 (W6 独立青年律师) → 拿真实邮箱 + 确认 7/29 试用到期
- [ ] 联系 L4 律师 (W12 重跑高级合伙人) → 拿真实邮箱 + 确认 8/25 试用到期
- [ ] 联系 L5 律师 (W12 重跑企业法务) → 拿真实邮箱 + 确认 8/25 试用到期
- [ ] 编辑 `scripts/lawyer-emails.json` 替换 `email` / `name` / `firm` 5 个字段
- [ ] 编辑 `scripts/smtp-credentials.env` 填实 SMTP_USER + SMTP_PASSWORD (从 `.env.example` 复制)
- [ ] 跑 `bash scripts/trigger-paid-email-723.sh --dry-run` 验证 5 律师全部能解析
- [ ] 跑 `python scripts/send_email.py --to <真实邮箱> --subject "测试" --body scripts/lawyer-emails.json --invite-code BETA2025-0001 --trigger-time 2026-07-23T09:00:00+08:00 --dry-run` 验证 SMTP dry-run 路径
- [ ] 删除本文件 / JSON 里的 `<公测前填实>` placeholder 字符串 (避免误导)

---

## 3. 触发链路 (cron → JSON → SMTP → 邮件)

```
mavis cron self lex-bd first-paid-email-723 \
  --every "1d" --start "2026-07-22T09:00:00+08:00" \
  --prompt "7/23 09:00 提前 6 天转化邮件待触发 (5 律师 L1-L5)"

  ↓ 7/23 09:00 CST 自动 fire

bash scripts/trigger-paid-email-723.sh --commit

  ↓ 读取 JSON
  scripts/lawyer-emails.json (5 律师邮箱 + 邀请码)
  scripts/smtp-credentials.env (SMTP_USER + SMTP_PASSWORD, .gitignore 排除)

  ↓ 真发邮件 (--commit 模式)
python scripts/send_email.py \
  --to l1.founding@lexprime.cn \
  --subject "您的 LexPrime 试用即将到期 - 创史体验官特别优惠" \
  --body docs/marketing/first-paid-triggers-runbook.md \
  --body-section "### 3.1" \
  --invite-code BETA2025-0001 \
  --trigger-id first-paid-triggers-729 \
  --trigger-time 2026-07-23T09:00:00+08:00

  ↓ SMTP 发邮件
  smtp.exmail.qq.com:465 (SSL)
  SMTP_USER=founder@lexprime.cn
  SMTP_PASSWORD=<公测前填实>

  ↓ 写 dashboard 触达日志
python scripts/log_trigger.py \
  --trigger-id first-paid-triggers-729 \
  --trigger-time 2026-07-23T09:00:00+08:00 \
  --trigger-channel email \
  --trigger-target 5-lawyers \
  --trigger-success 5 \
  --trigger-fail 0 \
  --log-file docs/marketing/dashboard-paid-triggers.md
```

---

## 4. 跟踪指标

| 指标 | 目标 | 监控位置 |
|------|------|----------|
| 触达率 | 100% (5/5 律师收到邮件) | `docs/marketing/dashboard-paid-triggers.md § 2` |
| 邮件打开率 | 80% (4/5 律师 7 天内打开) | SMTP 服务商 dashboard |
| 转化率 | 60% (3/5 律师 7/29 前付费) | 邀请码 redeem + 支付系统 |
| 营收 | L1/L2/L3 个人版 99 × 3 = ¥297, L4/L5 ¥449 × 2 = ¥898, 总 ¥1,195 | dashboard § 1 |
| 朋友圈扩散 | 5 律师各自推 3 名朋友 = 15 名新邀请码 | 公测期 day 8-15 dashboard |

---

## 5. 占位符规范

W15 w14-followup-fixes 严格遵守:
- ✅ **邮箱 placeholder**: `l{1-5}.founding@lexprime.cn` (l1.l2.l3.l4.l5 占位, 公测前替换)
- ✅ **律师姓名 placeholder**: `<公测前填实 - {title}>` (尖括号, 醒目标记)
- ✅ **律所/公司 placeholder**: `<公测前填实 - {type}>` (同上)
- ✅ **SMTP 凭证 placeholder**: `<公测前 7/22 总指挥填实 - QQ 企业邮箱 app-specific password>`
- ✅ **不 commit 真实凭证**: `.gitignore` 排除 `scripts/smtp-credentials.env` 和 `**/.env`
- ✅ **不 fabricate 报告**: 5 律师姓名 / 邮箱 / 律所均明确标注 `<placeholder>`, 公测前填实

---

**Status**: ✅ W15 w14-followup-fixes v1.0 落地 (2026-06-30)
**Next**: 7/22 总指挥填实邮箱 + SMTP, 7/23 09:00 cron 自动触发 5 律师转化邮件