import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'

const ALL_FIELDS = [
  { key: 'internal_ip',    label: 'Internal IP',     section: 'network' },
  { key: 'external_ip',    label: 'External IP',     section: 'network' },
  { key: 'mac_address',    label: 'MAC Address',     section: 'network' },
  { key: 'hostname',       label: 'Hostname',        section: 'network' },
  { key: 'domain',         label: 'Domain',          section: 'network' },
  { key: 'username',       label: 'User',            section: 'command' },
  { key: 'command',        label: 'Command',         section: 'command' },
  { key: 'notes',          label: 'Notes',           section: 'command' },
  { key: 'secrets',        label: 'Secrets',         section: 'command' },
  { key: 'analyst',        label: 'Analyst',         section: 'command' },
  { key: 'filename',       label: 'Filename',        section: 'file' },
  { key: 'hash_algorithm', label: 'Hash Algorithm',  section: 'file' },
  { key: 'hash_value',     label: 'Hash Value',      section: 'file' },
  { key: 'pid',            label: 'PID',             section: 'file' },
  { key: 'status',         label: 'Status',          section: 'file' },
]

const SECTIONS = [
  { key: 'network', label: 'Network Information' },
  { key: 'command', label: 'Command Information' },
  { key: 'file',    label: 'File & Status Information' },
]

const DEFAULT_VISIBLE = ALL_FIELDS.map((f) => f.key)

function loadColumnConfig() {
  try {
    const stored = localStorage.getItem('clio-card-fields')
    if (stored) return JSON.parse(stored)
  } catch {}
  return DEFAULT_VISIBLE
}

function saveColumnConfig(config) {
  localStorage.setItem('clio-card-fields', JSON.stringify(config))
}

function tagStyle(tag) {
  const color = tag.color || '#3b82f6'
  return {
    backgroundColor: color + '22',
    color,
    borderColor: color + '55',
  }
}

function statusClass(status) {
  switch (status) {
    case 'success':    return 'status-success'
    case 'failure':    return 'status-error'
    case 'in_progress': return 'status-info'
    case 'blocked':    return 'status-warning'
    default:           return ''
  }
}

/* ---- Card Fields Config Modal ---- */
function CardFieldsModal({ visibleFields, onSave, onClose }) {
  const [local, setLocal] = useState(visibleFields)

  const toggle = (key) =>
    setLocal((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Card Fields</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>&#10005;</button>
        </div>
        <div className="modal-body">
          <p className="settings-description">
            Choose which fields appear in the expanded card view.
          </p>
          {SECTIONS.map((section) => (
            <div key={section.key} className="card-fields-section">
              <div className="card-fields-section-title">{section.label}</div>
              {ALL_FIELDS.filter((f) => f.section === section.key).map((field) => (
                <label key={field.key} className="card-fields-checkbox">
                  <input
                    type="checkbox"
                    checked={local.includes(field.key)}
                    onChange={() => toggle(field.key)}
                  />
                  {field.label}
                </label>
              ))}
            </div>
          ))}
        </div>
        <div className="modal-actions" style={{ padding: '0 22px 22px' }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={() => { onSave(local); onClose() }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}

/* ---- Individual log card row ---- */
function LogCardRow({ log, expanded, onToggle, onEdit, onDelete, visibleFields }) {
  const ts = log.timestamp || log.created_at
  const formattedTs = ts
    ? new Date(ts).toISOString().replace('T', ' ').slice(0, 19) + 'Z'
    : '—'

  const cmd = log.command
    ? log.command.slice(0, 50) + (log.command.length > 50 ? '…' : '')
    : null

  const visibleSections = SECTIONS.filter((section) =>
    ALL_FIELDS.some((f) => f.section === section.key && visibleFields.includes(f.key))
  )

  return (
    <div className={`log-card-entry${expanded ? ' log-card-entry-expanded' : ''}`}>
      {/* Row header */}
      <div className="log-card-row" onClick={onToggle}>
        <span className={`log-card-chevron${expanded ? ' expanded' : ''}`}>&#8250;</span>
        <span className="log-card-icon">&#128274;</span>
        <span className="log-card-icon">&#128196;</span>
        <span className="log-card-ts mono">{formattedTs}</span>
        <div className="log-card-badges">
          {log.hostname && (
            <span className="log-badge log-badge-host">Host: {log.hostname}</span>
          )}
          {log.username && (
            <span className="log-badge log-badge-user">User: {log.username}</span>
          )}
          {cmd && (
            <span className="log-badge log-badge-cmd">Cmd: {cmd}</span>
          )}
        </div>
        <div className="log-card-row-actions" onClick={(e) => e.stopPropagation()}>
          <button
            className="btn btn-ghost btn-sm log-card-delete"
            onClick={onDelete}
            title="Delete"
          >
            &#128465;
          </button>
        </div>
      </div>

      {/* Tag row */}
      <div className="log-card-tag-row">
        <button
          className="btn btn-ghost btn-sm log-card-add-tag"
          onClick={(e) => { e.stopPropagation(); onEdit(log) }}
        >
          + Add Tag
        </button>
        <div className="tag-list">
          {(log.tags || []).map((tag, i) => (
            <span key={i} className="tag" style={tagStyle(tag)}>
              {tag.name || tag}
            </span>
          ))}
        </div>
      </div>

      {/* Expanded card sections */}
      {expanded && (
        <div
          className="log-card-expanded"
          style={{ gridTemplateColumns: `repeat(${visibleSections.length || 1}, 1fr)` }}
        >
          {visibleSections.map((section) => {
            const fields = ALL_FIELDS.filter(
              (f) => f.section === section.key && visibleFields.includes(f.key)
            )
            return (
              <div key={section.key} className="log-card-section">
                <div className="log-card-section-title">{section.label}</div>
                {fields.map((field) => (
                  <div key={field.key} className="log-card-field">
                    <span className="log-card-field-label">{field.label}:</span>
                    <span
                      className={`log-card-field-value${
                        field.key === 'command' || field.key === 'hash_value' ? ' mono' : ''
                      }`}
                    >
                      {field.key === 'status' && log[field.key] ? (
                        <span className={`status-badge ${statusClass(log[field.key])}`}>
                          {log[field.key]}
                        </span>
                      ) : (
                        log[field.key] || ''
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )
          })}
          <div className="log-card-expanded-actions">
            <button className="btn btn-ghost btn-sm" onClick={() => onEdit(log)}>
              Edit
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/* ---- Edit / Create panel ---- */
function LogPanel({ log, onClose, onSave }) {
  const [form, setForm] = useState({
    hostname:       log?.hostname       || '',
    internal_ip:    log?.internal_ip    || '',
    external_ip:    log?.external_ip    || '',
    mac_address:    log?.mac_address    || '',
    domain:         log?.domain         || '',
    username:       log?.username       || '',
    command:        log?.command        || '',
    notes:          log?.notes          || '',
    secrets:        log?.secrets        || '',
    filename:       log?.filename       || '',
    status:         log?.status         || 'success',
    hash_algorithm: log?.hash_algorithm || '',
    hash_value:     log?.hash_value     || '',
    pid:            log?.pid            || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (log?.id) {
        await client.put(`/logs/logs/${log.id}/`, form)
      } else {
        await client.post('/logs/logs/', form)
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

        <div className="log-panel-section-title">Network</div>
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
            <label>Domain</label>
            <input
              name="domain"
              value={form.domain}
              onChange={handleChange}
              placeholder="corp.local"
            />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Internal IP</label>
            <input
              name="internal_ip"
              value={form.internal_ip}
              onChange={handleChange}
              placeholder="10.0.0.1"
            />
          </div>
          <div className="form-group">
            <label>External IP</label>
            <input
              name="external_ip"
              value={form.external_ip}
              onChange={handleChange}
              placeholder="1.2.3.4"
            />
          </div>
        </div>
        <div className="form-group">
          <label>MAC Address</label>
          <input
            name="mac_address"
            value={form.mac_address}
            onChange={handleChange}
            placeholder="AA:BB:CC:DD:EE:FF"
          />
        </div>

        <div className="log-panel-section-title">Command</div>
        <div className="form-row">
          <div className="form-group">
            <label>Username</label>
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="DOMAIN\user"
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
          <label>Secrets</label>
          <textarea
            name="secrets"
            value={form.secrets}
            onChange={handleChange}
            placeholder="Captured credentials..."
            rows={2}
            className="mono"
          />
        </div>

        <div className="log-panel-section-title">File &amp; Status</div>
        <div className="form-row">
          <div className="form-group">
            <label>Filename</label>
            <input
              name="filename"
              value={form.filename}
              onChange={handleChange}
              placeholder="malware.exe"
            />
          </div>
          <div className="form-group">
            <label>PID</label>
            <input
              name="pid"
              value={form.pid}
              onChange={handleChange}
              placeholder="1234"
            />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Hash Algorithm</label>
            <input
              name="hash_algorithm"
              value={form.hash_algorithm}
              onChange={handleChange}
              placeholder="SHA256"
            />
          </div>
          <div className="form-group">
            <label>Hash Value</label>
            <input
              name="hash_value"
              value={form.hash_value}
              onChange={handleChange}
              placeholder="abc123..."
              className="mono"
            />
          </div>
        </div>

        <div className="log-panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : log?.id ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  )
}

/* ---- Page ---- */
export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [modalLog, setModalLog] = useState(null)
  const [showPanel, setShowPanel] = useState(false)
  const [expandedIds, setExpandedIds] = useState(new Set())
  const [activeOperation, setActiveOperation] = useState(null)
  const [filters, setFilters] = useState({ hostname: '', status: '' })
  const [showCardFields, setShowCardFields] = useState(false)
  const [visibleFields, setVisibleFields] = useState(loadColumnConfig)

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
      if (filters.status)   params.status   = filters.status

      const response = await client.get('/logs/logs/', { params })
      const data = response.data
      if (Array.isArray(data)) {
        setLogs(data)
        setTotalPages(1)
      } else {
        setLogs(data.results || [])
        setTotalPages(Math.ceil((data.count || 0) / (data.page_size || 25)))
      }
    } catch {
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

  const toggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleEditLog = (log) => {
    setModalLog(log)
    setShowPanel(true)
  }

  const handleNewLog = () => {
    setModalLog(null)
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

  const handleDelete = async (logId, e) => {
    e.stopPropagation()
    if (!window.confirm('Delete this log entry?')) return
    try {
      await client.delete(`/logs/logs/${logId}/`)
      fetchLogs()
    } catch {
      setError('Failed to delete log entry')
    }
  }

  const handleSaveCardFields = (fields) => {
    setVisibleFields(fields)
    saveColumnConfig(fields)
  }

  return (
    <div className={`page logs-page${showPanel ? ' panel-open' : ''}`}>
      <div className="page-header">
        <div className="logs-view-tabs">
          <button className="btn btn-primary btn-sm">Card View</button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setShowCardFields(true)}
          >
            Card Fields
          </button>
        </div>
        <button className="btn btn-primary" onClick={handleNewLog}>
          + Add Row
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
            <div className="log-cards-list">
              {logs.map((log) => (
                <LogCardRow
                  key={log.id}
                  log={log}
                  expanded={expandedIds.has(log.id)}
                  onToggle={() => toggleExpand(log.id)}
                  onEdit={handleEditLog}
                  onDelete={(e) => handleDelete(log.id, e)}
                  visibleFields={visibleFields}
                />
              ))}
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

      {showCardFields && (
        <CardFieldsModal
          visibleFields={visibleFields}
          onSave={handleSaveCardFields}
          onClose={() => setShowCardFields(false)}
        />
      )}
    </div>
  )
}
