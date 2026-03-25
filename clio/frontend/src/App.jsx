import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import LogsPage from './pages/LogsPage'
import OperationsPage from './pages/OperationsPage'
import TagsPage from './pages/TagsPage'
import SettingsPage from './pages/SettingsPage'
import ThreatIntelPage from './pages/ThreatIntelPage'
import ChatPage from './pages/ChatPage'
import ExportPage from './pages/ExportPage'

function NavBar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  if (!user) return null

  const navItems = [
    { path: '/logs', label: 'Logs' },
    { path: '/operations', label: 'Operations' },
    { path: '/tags', label: 'Tags' },
    { path: '/threat-intel', label: 'Threat Intel' },
    { path: '/export', label: 'Export' },
    { path: '/settings', label: 'Settings' },
  ]

  const adminItems = [
    { href: '/admin/', label: 'Admin' },
    { href: '/api/schema/swagger-ui/', label: 'API Docs' },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/logs" className="navbar-logo">
          <span className="logo-icon">&#9678;</span> CLIO
        </Link>
        <span className="navbar-subtitle">Security Operations Logger</span>
      </div>
      <div className="navbar-links">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`navbar-link ${location.pathname === item.path ? 'active' : ''}`}
          >
            {item.label}
          </Link>
        ))}
        {user.is_admin && (
          <>
            <span className="navbar-divider" />
            {adminItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="navbar-link navbar-link-admin"
                target="_blank"
                rel="noopener noreferrer"
              >
                {item.label} &#8599;
              </a>
            ))}
          </>
        )}
      </div>
      <div className="navbar-user">
        <span className="navbar-username">{user.username || user.email || 'User'}</span>
        {user.is_admin && <span className="badge badge-admin">Admin</span>}
        <button className="btn btn-sm btn-ghost" onClick={logout}>
          Logout
        </button>
      </div>
    </nav>
  )
}

function AppRoutes() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Initializing Clio...</p>
      </div>
    )
  }

  return (
    <>
      <NavBar />
      <div className="main-content">
        <Routes>
          <Route
            path="/"
            element={<Navigate to={user ? '/logs' : '/login'} replace />}
          />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/logs"
            element={
              <ProtectedRoute>
                <LogsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/operations"
            element={
              <ProtectedRoute>
                <OperationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tags"
            element={
              <ProtectedRoute>
                <TagsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/threat-intel"
            element={
              <ProtectedRoute>
                <ThreatIntelPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/export"
            element={
              <ProtectedRoute>
                <ExportPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
