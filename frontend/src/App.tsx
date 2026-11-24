import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { SupplyChain } from './pages/SupplyChain';
import { Revenue } from './pages/Revenue';
import { Recommendations } from './pages/Recommendations';
import { Approvals } from './pages/Approvals';
import { Simulations } from './pages/Simulations';
import { DataSources } from './pages/DataSources';
import { Entities } from './pages/Entities';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white font-sans">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Loading BusinessPulse AI Session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Authenticated Workspace Routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Overview />} />
            <Route path="/supply-chain" element={<SupplyChain />} />
            <Route path="/revenue" element={<Revenue />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/simulations" element={<Simulations />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/entities" element={<Entities />} />
          </Route>

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
