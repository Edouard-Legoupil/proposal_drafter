import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import store from './store';
import ProtectedRoute from './components/ProtectedRoute';

// Import your components
import Login from './screens/Login';
import Dashboard from './screens/Dashboard';
import Proposals from './screens/Proposals';
import KnowledgeCards from './screens/KnowledgeCards';
import MetricsDashboard from './screens/Dashboard/components/MetricsDashboard/MetricsDashboard';
import DonorTemplateDetail from './screens/DonorTemplateDetail/DonorTemplateDetail';
import DonorTemplateRequest from './screens/DonorTemplateRequest/DonorTemplateRequest';
import QualityGate from './screens/QualityGate/QualityGate';
import IncidentAnalysis from './screens/IncidentAnalysis';
import UnauthorizedAccess from './components/UnauthorizedAccess';
import SidebarLayout from './components/SidebarLayout';

function App() {
  return (
    <Provider store={store}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Main application with sidebar */}
          <Route path="/" element={<SidebarLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="proposals" element={<Proposals />} />
            <Route path="knowledge-cards" element={<KnowledgeCards />} />

            {/* Protected routes with role requirements */}
            <Route path="dashboard/metrics" element={
              <ProtectedRoute permission="access_metrics">
                <MetricsDashboard />
              </ProtectedRoute>
            } />

            <Route path="templates" element={
              <ProtectedRoute permission="access_template">
                <DonorTemplateDetail />
              </ProtectedRoute>
            } />

            <Route path="templates/request" element={
              <ProtectedRoute permission="access_template">
                <DonorTemplateRequest />
              </ProtectedRoute>
            } />

            <Route path="quality-gate" element={
              <ProtectedRoute permission="access_quality_gate">
                <QualityGate />
              </ProtectedRoute>
            } />

            <Route path="incidents" element={
              <ProtectedRoute permission="access_incident">
                <IncidentAnalysis />
              </ProtectedRoute>
            } />
          </Route>

          {/* Fallback for unauthorized access */}
          <Route path="/unauthorized" element={<UnauthorizedAccess />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </Provider>
  );
}

export default App;