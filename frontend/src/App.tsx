import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { RequireAuth, RequireRole } from './components/auth/ProtectedRoute';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Scenarios from './pages/Scenarios';
import NewScenario from './pages/NewScenario';
import ScenarioResult from './pages/ScenarioResult';
import Materials from './pages/Materials';
import Recommendations from './pages/Recommendations';
import Reports from './pages/Reports';
import AuditLog from './pages/AuditLog';
import InverseSolver from './pages/InverseSolver';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60000, refetchOnWindowFocus: false } },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route element={<RequireAuth />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/inverse-solver" element={<InverseSolver />} />
              <Route path="/scenarios" element={<Scenarios />} />
              <Route path="/scenarios/new" element={<NewScenario />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/scenario/:id/results" element={<ScenarioResult />} />
              <Route path="/materials" element={<Materials />} />
              <Route path="/reports" element={<Reports />} />
            </Route>

            <Route element={<RequireRole roles={['admin', 'engineer']} />}>
              <Route path="/admin/audit" element={<AuditLog />} />
            </Route>
            
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
