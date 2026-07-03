import { useEffect } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import Workstation from './pages/Workstation';
import ContractReview from './pages/ContractReview';
import CaseList from './pages/CaseList';
import { useUserStore } from './store';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loadFromStorage } = useUserStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/workstation"
        element={
          <ProtectedRoute>
            <Workstation />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cases"
        element={
          <ProtectedRoute>
            <CaseList />
          </ProtectedRoute>
        }
      />
      <Route
        path="/contract-review"
        element={
          <ProtectedRoute>
            <ContractReview />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/workstation" replace />} />
      <Route path="*" element={<Navigate to="/workstation" replace />} />
    </Routes>
  );
}