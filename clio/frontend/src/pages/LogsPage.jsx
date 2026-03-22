import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const seconds = Math.floor((now - date) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

function LogModal({ log, onClose, onSave }) {
  const [form, setForm] = useState({
    hostname: log?.hostname || '',
    ip_address: log?.ip_address || '',
    action: log?.action || '',
    command: log?.command || '',
    output: log?.output || '',
    status: log?.status || 'success',
    notes: log?.notes || '',
    tags: log?.tags?.map((t) => t.name || t).join(', ') || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  // Close on Escape
  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    const payload = {
      ...form,
      tags: form.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    }

    try {
      if (log?.id) {
        await client.put(`/logs/logs/${log.id}/`, payload)
      } else {
        await client.post('/logs/logs/', payload)
      }
      onSave()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          'Failed to save log entry'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{log?.id ? 'Edit Log Entry' : 'New Log Entry'}</h2>
          <button className="btn btn-ghost" onClick={onClose}>
            &#10005;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label>Hostname</label>
              <input
                name="hostname"
                value={form.hostname}
                onChange={handleChange}
                placeholder="target-host"
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>IP Address</label>
              <input
                name="ip_address"
                value={form.ip_address}
                onChange={handleChange}
                placeholder="10.0.0.1"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Action</label>
              <input
                name="action"
                value={form.action}
                onChange={handleChange}
                placeholder="e.g., lateral_movement"
                required
              />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select name="status" value={form.status} onChange={handleChange}>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="in_progress">In Progress</option>
                <option value="blocked">Blocked</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Command</label>
            <textarea
              name="command"
              value={form.command}
              onChange={handleChange}
              placeholder="Command executed..."
              rows={3}
              className="mono"
            />
          </div>

          <div className="form-group">
            <label>Output</label>
            <textarea
              name="output"
              value={form.output}
              onChange={handleChange}
              placeholder="Command output..."
              rows={4}
              className="mono"
            />
          </div>

          <div className="form-group">
            <label>Notes</label>
            <textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              placeholder="Additional notes..."
              rows={2}
            />
          </div>

          <div className="form-group">
            <label>Tags (comma-separated)</label>
            <input
              name="tags"
              value={form.tags}
              onChange={handleChange}
              placeholder="persistence, privilege-escalation"
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Saving...' : log?.id ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [modalLog, setModalLog] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [filters, setFilters] = useState({
    hostname: '',
    ip_address: '',
    status: '',
  })

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page }
      if (filters.hostname) params.hostname = filters.hostname
      if (filters.ip_address) params.ip_address = filters.ip_address
      if (filters.status) params.status = filters.status

      const response = await client.get('/logs/logs/', { params })
      const data = response.data

      if (Array.isArray(data)) {
        setLogs(data)
        setTotalPages(1)
      } else {
        setLogs(data.results || [])
        setTotalPages(Math.ceil((data.count || 0) / (data.page_size || 25)))
      }
    } catch (err) {
      setError('Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }, [page, filters])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  // Keyboard shortcut: N to create new log
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'n' && !showModal && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'SELECT') {
        e.preventDefault()
        handleNewLog()
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [showModal])

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value })
    setPage(1)
  }

  const handleNewLog = () => {
    setModalLog(null)
    setShowModal(true)
  }

  const handleEditLog = (log) => {
    setModalLog(log)
    setShowModal(true)
  }

  const handleModalClose = () => {
    setShowModal(false)
    setModalLog(null)
  }

  const handleModalSave = () => {
    setShowModal(false)
    setModalLog(null)
    fetchLogs()
  }

  const statusClass = (status) => {
    switch (status) {
      case 'success':
        return 'status-success'
      case 'failure':
        return 'status-error'
      case 'in_progress':
        return 'status-info'
      case 'blocked':
        return 'status-warning'
      default:
        return ''
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Log Entries</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Press <kbd style={{ padding: '1px 5px', background: 'var(--bg-tertiary)', borderRadius: '3px', border: '1px solid var(--border-color)', fontSize: '11px' }}>N</kbd> to create
          </span>
          <button className="btn btn-primary" onClick={handleNewLog}>
            + New Log
          </button>
        </div>
      </div>

      <div className="filters-bar">
        <input
          name="hostname"
          placeholder="Filter by hostname..."
          value={filters.hostname}
          onChange={handleFilterChange}
          className="filter-input"
        />
        <input
          name="ip_address"
          placeholder="Filter by IP..."
          value={filters.ip_address}
          onChange={handleFilterChange}
          className="filter-input"
        />
        <select
          name="status"
          value={filters.status}
          onChange={handleFilterChange}
          className="filter-input"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="in_progress">In Progress</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-inline">
          <div className="loading-spinner" />
          <span>Loading logs...</span>
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: '36px', marginBottom: '12px', opacity: 0.3 }}>&#9776;</div>
          <p>{filters.hostname || filters.ip_address || filters.status
            ? 'No logs match your current filters.'
            : 'No log entries found.'}</p>
          {!filters.hostname && !filters.ip_address && !filters.status && (
            <button className="btn btn-primary" onClick={handleNewLog}>
              Create your first log
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Hostname</th>
                  <th>IP Address</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Tags</th>
                  <th>Operator</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    onClick={() => handleEditLog(log)}
                    className="clickable-row"
                  >
                    <td className="mono td-timestamp" title={new Date(log.created_at || log.timestamp).toLocaleString()}>
                      {timeAgo(log.created_at || log.timestamp)}
                    </td>
                    <td className="mono">{log.hostname}</td>
                    <td className="mono">{log.ip_address}</td>
                    <td>{log.action}</td>
                    <td>
                      <span className={`status-badge ${statusClass(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                    <td>
                      <div className="tag-list">
                        {(log.tags || []).map((tag, i) => (
                          <span
                            key={i}
                            className="tag"
                            style={tag.color ? {
                              background: `${tag.color}18`,
                              color: tag.color,
                              borderColor: `${tag.color}33`,
                            } : undefined}
                          >
                            {tag.name || tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>{log.operator?.username || log.analyst || log.operator || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-sm btn-ghost"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-sm btn-ghost"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showModal && (
        <LogModal
          log={modalLog}
          onClose={handleModalClose}
          onSave={handleModalSave}
        />
      )}
    </div>
  )
}
