import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import useStore from './store/useStore';

// Pages
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import ProjectPage from './pages/ProjectPage';
import AgentWorkspacePage from './pages/AgentWorkspacePage';
import MemoryPage from './pages/MemoryPage';

// Layout
import Shell from './components/layout/Shell';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { user, token } = useStore();
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        
        {/* Protected Routes inside Shell */}
        <Route path="/" element={
          <ProtectedRoute>
            <Shell />
          </ProtectedRoute>
        }>
          <Route index element={<DashboardPage />} />
          <Route path="project/:projectId" element={<ProjectPage />} />
          <Route path="project/:projectId/workspace" element={<AgentWorkspacePage />} />
          <Route path="project/:projectId/memory" element={<MemoryPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
