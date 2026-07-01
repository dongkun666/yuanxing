/**
 * App 根组件 - W19 Phase 5.1 入口
 *
 * 路由结构:
 *   /                  → 重定向到 /login
 *   /login             → Login.tsx (W3 login.html 重构)
 *   /workstation       → Workstation.tsx (W5 workstation.html 重构)
 *   /contract-review   → ContractReview.tsx (W5 contract-review.js + templates 重构)
 *
 * Phase 5.1 仅迁移 3 模块, 完整 6 模块路由待 W20+ 增量
 */
import { Navigate, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import Workstation from './pages/Workstation';
import ContractReview from './pages/ContractReview';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/workstation" element={<Workstation />} />
      <Route path="/contract-review" element={<ContractReview />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}