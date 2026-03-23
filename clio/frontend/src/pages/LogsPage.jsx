import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'

function tagStyle(tag) {
  const color = tag.color || '#3b82f6'
  return {
    backgroundColor: color + '22',
    color: color,
    borderColor: color + '55',
  }
}

function LogPanel({ log, onClose, onSave }) {
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
    <div className="log-panel">
      <div className="log-panel-header">
        <div className="log-panel-title">
          {log?.id ? (
            <>
              <span className="log-panel-title-label">Edit Entry</span>
              <span className="mono log-panel-title-host">{log.hostname}</span>
            </>
          ) : (
            <span className="log-panel-title-label">New Log Entry</span>
          )}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onClose} title="Close">
          &#10005;
        </button>
      </div>

      <form onSubmit={handleSubmit} className="log-panel-body">
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

        <div className="log-panel-actions">
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
  )
}

export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [modalLog, setModalLog] = useState(null)
  const [showPanel, setShowPanel] = useState(false)
  const [activeOperation, setActiveOperation] = useState(null)
  const [filters, setFilters] = useState({
    hostname: '',
    ip_address: '',
    status: '',
  })

  useEffect(() => {
    client
      .get('/operations/operations/my-operations/')
      .then((res) => {
        const active = (res.data || []).find((op) => op.is_active)
        setActiveOperation(active || null)
      })
      .catch(() => {})
  }, [])

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

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value })
    setPage(1)
  }

  const handleNewLog = () => {
    setModalLog(null)
    setShowPanel(true)
  }

  const handleEditLog = (log) => {
    setModalLog(log)
    setShowPanel(true)
  }

  const handlePanelClose = () => {
    setShowPanel(false)
    setModalLog(null)
  }

  const handlePanelSave = () => {
    setShowPanel(false)
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
    <div className={`page logs-page${showPanel ? ' panel-open' : ''}`}>
      <div className="page-header">
        <h1>Log Entries</h1>
        <button className="btn btn-primary" onClick={handleNewLog}>
          + New Log
        </button>
      </div>

      {activeOperation ? (
        <div className="operation-banner">
          <span className="operation-banner-label">Operation:</span>
          <strong>{activeOperation.operation_name}</strong>
          {activeOperation.tag_name && (
            <span
              className="tag"
              style={{
                backgroundColor: (activeOperation.tag_color || '#3B82F6') + '22',
                color: activeOperation.tag_color || '#3B82F6',
                borderColor: (activeOperation.tag_color || '#3B82F6') + '55',
                marginLeft: '0.5rem',
              }}
            >
              {activeOperation.tag_name}
            </span>
          )}
        </div>
      ) : (
        <div className="operation-banner operation-banner-warn">
          No active operation set &mdash; showing all logs.
          <a href="/operations" style={{ marginLeft: '0.5rem' }}>Select one</a>
        </div>
      )}

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

      <div className="logs-content">
        {loading ? (
          <div className="loading-inline">
            <div className="loading-spinner" />
            <span>Loading logs...</span>
          </div>
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <p>No log entries found.</p>
            <button className="btn btn-primary" onClick={handleNewLog}>
              Create your first log
            </button>
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
                      className={`clickable-row${modalLog?.id === log.id && showPanel ? ' row-selected' : ''}`}
                    >
                      <td className="mono td-timestamp">
                        {new Date(log.created_at || log.timestamp).toLocaleString()}
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
                              style={tagStyle(tag)}
                            >
                              {tag.name || tag}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>{log.operator?.username || log.operator || '-'}</td>
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

        {showPanel && (
          <LogPanel
            log={modalLog}
            onClose={handlePanelClose}
            onSave={handlePanelSave}
          />
        )}
      </div>
    </div>
  )
}
