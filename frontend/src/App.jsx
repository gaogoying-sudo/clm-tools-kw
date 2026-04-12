import { useState, useEffect } from 'react'
import { HashRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { SearchPage } from './pages/SearchPage'
import { QARecordsPage } from './pages/QARecordsPage'
import { InsightsPage } from './pages/InsightsPage'
import { SettingsPage } from './pages/SettingsPage'
import './index.css'

// Protected route wrapper
function ProtectedRoute({ children, requireRole }) {
  const token = localStorage.getItem('clm_auth_token')
  const role = localStorage.getItem('clm_role') || 'admin'

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (requireRole && role !== requireRole) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

// Layout with sidebar
function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

function AppContent() {
  const location = useLocation()
  const isLogin = location.pathname === '/login'

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout><DashboardPage /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="/search" element={
        <ProtectedRoute>
          <AppLayout><SearchPage /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="/qa-records" element={
        <ProtectedRoute>
          <AppLayout><QARecordsPage /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="/insights" element={
        <ProtectedRoute>
          <AppLayout><InsightsPage /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="/settings" element={
        <ProtectedRoute requireRole="superadmin">
          <AppLayout><SettingsPage /></AppLayout>
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <HashRouter>
      <AppContent />
    </HashRouter>
  )
}
