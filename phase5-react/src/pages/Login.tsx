/**
 * Login 页面 - W3 login.html 重构为 React 组件 + TypeScript
 *
 * 保留功能 (5 大价值主张 + 6 大模块保持不变):
 *  - 登录 / 注册 Tab 切换
 *  - 邮箱 + 密码 + (注册姓名)
 *  - Demo 模式 (MVP_USER_ID=u-1 免登录)
 *  - 全屏 fixed 盖住 sidebar
 *
 * 重构点:
 *  - HTML 静态 + inline onclick → React state + onChange/onClick
 *  - DOM ID 选择器 → useState hooks
 *  - 全局 switchView → React Router useNavigate
 */
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

type Tab = 'login' | 'register';

export default function Login() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('login');

  // 登录表单
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // 注册表单
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerError, setRegisterError] = useState('');

  function handleLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoginError('');

    if (!loginEmail || !loginPassword) {
      setLoginError('请填写邮箱和密码');
      return;
    }

    // Phase 5.1 placeholder: 走 FastAPI /api/auth/login (W7 已就位, lex-coder W3)
    // 此处保留登录接口契约, 真实 fetch 留给 W20 接入
    console.info('[Phase 5.1] 登录请求:', { email: loginEmail });
    navigate('/workstation');
  }

  function handleRegister(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setRegisterError('');

    if (!registerName || !registerEmail || !registerPassword) {
      setRegisterError('请填写姓名 / 邮箱 / 密码');
      return;
    }
    if (registerPassword.length < 6) {
      setRegisterError('密码至少 6 位');
      return;
    }

    // Phase 5.1 placeholder: 走 FastAPI /api/auth/register
    console.info('[Phase 5.1] 注册请求:', { name: registerName, email: registerEmail });
    navigate('/workstation');
  }

  function handleDemoLogin() {
    // Demo 模式 (MVP_USER_ID=u-1) — 跟 vanilla 版一致
    console.info('[Phase 5.1] Demo 模式进入');
    navigate('/workstation');
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-subtle">
      <div className="w-full max-w-md px-4">
        {/* Logo + 品牌 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand text-white text-3xl mb-4">
            ⚖
          </div>
          <h1 className="text-2xl font-bold">
            <span className="text-fg-primary">LexPrime</span>
            <span className="text-brand ml-1">元枢法智</span>
          </h1>
          <p className="text-sm text-fg-tertiary mt-2">
            律师的第二大脑 · LLM Wiki 持续维护
          </p>
        </div>

        {/* 登录卡片 */}
        <div className="bg-white rounded-2xl border border-bg-border p-8 shadow-xl shadow-fg-primary/5">
          {/* Tab 切换 */}
          <div className="flex items-center gap-1 mb-6 bg-bg-subtle rounded-xl p-1">
            <button
              type="button"
              onClick={() => setTab('login')}
              aria-pressed={tab === 'login'}
              className={
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all ' +
                (tab === 'login'
                  ? 'bg-white text-brand shadow-sm'
                  : 'text-fg-secondary hover:text-fg-primary')
              }
            >
              登录
            </button>
            <button
              type="button"
              onClick={() => setTab('register')}
              aria-pressed={tab === 'register'}
              className={
                'flex-1 py-2 rounded-lg text-sm font-medium transition-all ' +
                (tab === 'register'
                  ? 'bg-white text-brand shadow-sm'
                  : 'text-fg-secondary hover:text-fg-primary')
              }
            >
              注册
            </button>
          </div>

          {/* 登录表单 */}
          {tab === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4" aria-label="登录表单">
              <div>
                <label htmlFor="login-email" className="block text-xs text-fg-secondary font-medium mb-1.5">
                  邮箱
                </label>
                <input
                  type="email"
                  id="login-email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="input-base"
                  placeholder="you@lawfirm.com"
                  autoComplete="email"
                />
              </div>
              <div>
                <label htmlFor="login-password" className="block text-xs text-fg-secondary font-medium mb-1.5">
                  密码
                </label>
                <input
                  type="password"
                  id="login-password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="input-base"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
              {loginError && (
                <div className="text-xs text-danger" role="alert">{loginError}</div>
              )}
              <button type="submit" className="btn-primary w-full">
                登录
              </button>
            </form>
          )}

          {/* 注册表单 */}
          {tab === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4" aria-label="注册表单">
              <div>
                <label htmlFor="register-name" className="block text-xs text-fg-secondary font-medium mb-1.5">
                  姓名
                </label>
                <input
                  type="text"
                  id="register-name"
                  required
                  value={registerName}
                  onChange={(e) => setRegisterName(e.target.value)}
                  className="input-base"
                  placeholder="张律师"
                />
              </div>
              <div>
                <label htmlFor="register-email" className="block text-xs text-fg-secondary font-medium mb-1.5">
                  邮箱
                </label>
                <input
                  type="email"
                  id="register-email"
                  required
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  className="input-base"
                  placeholder="you@lawfirm.com"
                  autoComplete="email"
                />
              </div>
              <div>
                <label htmlFor="register-password" className="block text-xs text-fg-secondary font-medium mb-1.5">
                  密码
                </label>
                <input
                  type="password"
                  id="register-password"
                  required
                  minLength={6}
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  className="input-base"
                  placeholder="至少 6 位"
                  autoComplete="new-password"
                />
              </div>
              {registerError && (
                <div className="text-xs text-danger" role="alert">{registerError}</div>
              )}
              <button type="submit" className="btn-primary w-full">
                注册并登录
              </button>
            </form>
          )}

          {/* 分隔线 */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-bg-border" />
            <span className="text-xs text-fg-tertiary">或</span>
            <div className="flex-1 h-px bg-bg-border" />
          </div>

          {/* Demo 模式 */}
          <button
            type="button"
            onClick={handleDemoLogin}
            className="w-full py-3 border border-bg-border text-fg-secondary font-medium rounded-lg hover:bg-bg-subtle transition-colors text-sm"
          >
            🚀 以 Demo 模式进入 (免登录)
          </button>
          <p className="text-xs text-fg-tertiary text-center mt-3">
            Demo 模式使用模拟用户 (MVP_USER_ID=u-1), 无需后端 auth。
          </p>
        </div>

        {/* 底部 */}
        <p className="text-xs text-fg-tertiary text-center mt-6">
          © 2026 LexPrime 元枢法智 · AI 辅助, 不替代律师
        </p>
      </div>
    </div>
  );
}