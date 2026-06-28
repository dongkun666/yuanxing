"""
LexPrime Auth Module · W1 脚手架
2026-06-28

模块边界 (W1):
- User / LawyerProfile / Token / OTPLog 4 表
- FastAPI skeleton (无业务端点, 留给 W2 接入注册/登录)
- 复用 core/db.py 的 Database class (SQLite dev + PG prod)

W2+ 计划:
- bcrypt 密码哈希 (passlib[bcrypt])
- JWT 签发 (PyJWT) + Refresh Token 持久化
- 邮箱/手机 OTP 验证
- TOTP (pyotp) 多因素认证
- 律师执业证 OCR (对接 PaddleOCR)
"""
