import { useState } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

function ChangePasswordSection() {
  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [message, setMessage] = useState({ type: '', text: '' })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })

    if (form.new_password !== form.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match.' })
      return
    }
    if (form.new_password.length < 8) {
      setMessage({
        type: 'error',
        text: 'Password must be at least 8 characters.',
      })
      return
    }

    setSaving(true)
    try {
      await client.post('/accounts/change-password/', {
        current_password: form.current_password,
        new_password: form.new_password,
      })
      setMessage({ type: 'success', text: 'Password changed successfully.' })
      setForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      setMessage({
        type: 'error',
        text:
          err.response?.data?.detail ||
          err.response?.data?.message ||
          'Failed to change password.',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="settings-section">
      <h2>Change Password</h2>
      <form onSubmit={handleSubmit}>
        {message.text && (
          <div className={`alert alert-${message.type}`}>{message.text}</div>
        )}
        <div className="form-group">
          <label>Current Password</label>
          <input
            type="password"
            value={form.current_password}
            onChange={(e) =>
              setForm({ ...form, current_password: e.target.value })
            }
            required
            autoComplete="current-password"
          />
        </div>
        <div className="form-group">
          <label>New Password</label>
          <input
            type="password"
            value={form.new_password}
            onChange={(e) =>
              setForm({ ...form, new_password: e.target.value })
            }
            required
            autoComplete="new-password"
          />
        </div>
        <div className="form-group">
          <label>Confirm New Password</label>
          <input
            type="password"
            value={form.confirm_password}
            onChange={(e) =>
              setForm({ ...form, confirm_password: e.target.value })
            }
            required
            autoComplete="new-password"
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Changing...' : 'Change Password'}
        </button>
      </form>
    </div>
  )
}

function ApiKeySection() {
  const [apiKey, setApiKey] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const generateKey = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await client.post('/accounts/api-keys/')
      setApiKey(response.data.key || response.data.api_key || response.data.token)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to generate API key.'
      )
    } finally {
      setLoading(false)
    }
  }

  const revokeKeys = async () => {
    if (!window.confirm('Revoke all API keys? This cannot be undone.')) return
    setLoading(true)
    setError('')
    try {
      await client.delete('/accounts/api-keys/')
      setApiKey(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to revoke keys.')
    } finally {
      setLoading(false)
    }
  }

  const copyKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="settings-section">
      <h2>API Keys</h2>
      {error && <div className="alert alert-error">{error}</div>}

      {apiKey && (
        <div className="api-key-display">
          <code className="api-key-value">{apiKey}</code>
          <button className="btn btn-sm btn-ghost" onClick={copyKey}>
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <p className="api-key-warning">
            Store this key securely. It will not be shown again.
          </p>
        </div>
      )}

      <div className="btn-group">
        <button
          className="btn btn-primary"
          onClick={generateKey}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate New Key'}
        </button>
        <button
          className="btn btn-danger"
          onClick={revokeKeys}
          disabled={loading}
        >
          Revoke All Keys
        </button>
      </div>
    </div>
  )
}

function SessionSection() {
  const { logout } = useAuth()
  const [loading, setLoading] = useState(false)

  const handleLogoutAll = async () => {
    if (!window.confirm('Log out of all sessions?')) return
    setLoading(true)
    try {
      await client.post('/accounts/logout-all/')
    } catch {
      // continue with local logout
    }
    logout()
  }

  return (
    <div className="settings-section">
      <h2>Sessions</h2>
      <p className="settings-description">
        Manage your active sessions across all devices.
      </p>
      <div className="btn-group">
        <button className="btn btn-danger" onClick={logout}>
          Logout
        </button>
        <button
          className="btn btn-danger"
          onClick={handleLogoutAll}
          disabled={loading}
        >
          {loading ? 'Logging out...' : 'Logout All Sessions'}
        </button>
      </div>
    </div>
  )
}

function ExportSection() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleExport = async (format) => {
    setLoading(true)
    setError('')
    try {
      const response = await client.get(`/logs/export/`, {
        params: { format },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `clio-export.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to export data.')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      await client.post('/logs/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      alert('Import completed successfully.')
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to import data.'
      )
    } finally {
      setLoading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="settings-section">
      <h2>Export / Import</h2>
      {error && <div className="alert alert-error">{error}</div>}
      <p className="settings-description">
        Export log data for reporting or import from a previous export.
      </p>
      <div className="btn-group">
        <button
          className="btn btn-primary"
          onClick={() => handleExport('json')}
          disabled={loading}
        >
          Export JSON
        </button>
        <button
          className="btn btn-primary"
          onClick={() => handleExport('csv')}
          disabled={loading}
        >
          Export CSV
        </button>
        <label className="btn btn-ghost file-input-label">
          Import File
          <input
            type="file"
            accept=".json,.csv"
            onChange={handleImport}
            style={{ display: 'none' }}
          />
        </label>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="page">
      <div className="page-header">
        <h1>Settings</h1>
        <span className="settings-user-info">
          Signed in as <strong>{user?.username || 'User'}</strong>
          {user?.is_admin && (
            <span className="badge badge-admin">Admin</span>
          )}
        </span>
      </div>

      <div className="settings-grid">
        <ChangePasswordSection />
        <ApiKeySection />
        <SessionSection />
        <ExportSection />
      </div>
    </div>
  )
}
