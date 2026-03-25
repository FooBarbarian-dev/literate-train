import { useState, useEffect, useCallback, useRef } from 'react'
import client from '../api/client'

function tagStyle(tag) {
  const color = tag.color || '#3b82f6'
  return {
    backgroundColor: color + '22',
    color: color,
    borderColor: color + '55',
  }
}

// ---- TagInput: autocomplete tag selector with pill display ----
function TagInput({ selectedTags, onAdd, onRemove }) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [inputError, setInputError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ name: '', color: '#3b82f6', description: '' })
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')
  const containerRef = useRef(null)
  const inputRef = useRef(null)

  // Debounced autocomplete fetch
  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await client.get(`/tags/tags/autocomplete/?q=${encodeURIComponent(query)}`)
        const filtered = (res.data || []).filter(
          (t) => !selectedTags.some((s) => s.id === t.id)
        )
        setSuggestions(filtered)
        setShowDropdown(true)
      } catch {
        setSuggestions([])
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [query, selectedTags])

  // Close dropdown on outside click
  useEffect(() => {
    const handle = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false)
        setShowCreate(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const selectTag = (tag) => {
    onAdd(tag)
    setQuery('')
    setSuggestions([])
    setShowDropdown(false)
    setInputError('')
  }

  const handleKeyDown = (e) => {
    if (inputError) setInputError('')
    if (e.key === 'Enter') {
      e.preventDefault()
      if (suggestions.length > 0) {
        selectTag(suggestions[0])
      } else if (query.trim()) {
        setInputError(`Tag "${query}" does not exist. Select from the dropdown or create it.`)
        setShowDropdown(true)
      }
    } else if (e.key === 'Backspace' && !query && selectedTags.length > 0) {
      const last = selectedTags[selectedTags.length - 1]
      if (last.category !== 'operation') {
        onRemove(last.id)
      }
    } else if (e.key === 'Escape') {
      setShowDropdown(false)
      setShowCreate(false)
    }
  }

  const openCreate = () => {
    setShowCreate(true)
    setShowDropdown(false)
    setCreateError('')
    setCreateForm((f) => ({ ...f, name: query }))
  }

  const handleCreateSubmit = async (e) => {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      const res = await client.post('/tags/tags/', {
        ...createForm,
        name: createForm.name.trim().toLowerCase(),
      })
      selectTag(res.data)
      setShowCreate(false)
      setCreateForm({ name: '', color: '#3b82f6', description: '' })
    } catch (err) {
      const data = err.response?.data
      setCreateError(
        data?.name?.[0] || data?.detail || data?.message || 'Failed to create tag'
      )
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="tag-input-container" ref={containerRef}>
      <div
        className="tag-input-area"
        onClick={() => inputRef.current?.focus()}
      >
        {selectedTags.map((tag) => (
          <span key={tag.id} className="tag-pill" style={tagStyle(tag)}>
            {tag.name}
            {tag.category !== 'operation' && (
              <button
                type="button"
                className="tag-pill-remove"
                onClick={(e) => {
                  e.stopPropagation()
                  onRemove(tag.id)
                }}
                title="Remove tag"
              >
                ×
              </button>
            )}
          </span>
        ))}
        <input
          ref={inputRef}
          className="tag-input-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.trim() && setShowDropdown(true)}
          placeholder={selectedTags.length === 0 ? 'Type to search tags...' : ''}
          autoComplete="off"
        />
      </div>

      {inputError && <div className="tag-input-error">{inputError}</div>}

      {showDropdown && !showCreate && (
        <div className="tag-dropdown">
          {suggestions.length > 0
            ? suggestions.map((tag) => (
                <div
                  key={tag.id}
                  className="tag-dropdown-item"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    selectTag(tag)
                  }}
                >
                  <span
                    className="tag-dot"
                    style={{ backgroundColor: tag.color || '#3b82f6' }}
                  />
                  <span>{tag.name}</span>
                  {tag.category === 'operation' && (
                    <span className="tag-dropdown-badge">op</span>
                  )}
                </div>
              ))
            : (
                <div className="tag-dropdown-empty">No matching tags</div>
              )}
          <div
            className="tag-dropdown-create"
            onMouseDown={(e) => {
              e.preventDefault()
              openCreate()
            }}
          >
            + Create tag{query.trim() ? ` "${query}"` : ''}
          </div>
        </div>
      )}

      {showCreate && (
        <div className="tag-create-form">
          <div className="tag-create-form-header">
            <span>Create new tag</span>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setShowCreate(false)}
            >
              ×
            </button>
          </div>
          {createError && (
            <div className="alert alert-error" style={{ marginBottom: 8 }}>
              {createError}
            </div>
          )}
          <form onSubmit={handleCreateSubmit}>
            <input
              value={createForm.name}
              onChange={(e) =>
                setCreateForm((f) => ({ ...f, name: e.target.value }))
              }
              placeholder="Tag name"
              required
              autoFocus
              className="tag-create-input"
            />
            <input
              value={createForm.description}
              onChange={(e) =>
                setCreateForm((f) => ({ ...f, description: e.target.value }))
              }
              placeholder="Description (optional)"
              className="tag-create-input"
            />
            <div className="color-input-row" style={{ marginTop: 6 }}>
              <input
                type="color"
                value={createForm.color}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, color: e.target.value }))
                }
                className="color-picker"
              />
              <input
                value={createForm.color}
                onChange={(e) =>
                  setCreateForm((f) => ({ ...f, color: e.target.value }))
                }
                placeholder="#3b82f6"
                className="color-text"
              />
            </div>
            <div className="tag-create-actions">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setShowCreate(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-sm"
                disabled={creating}
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

// ---- TagFilterInput: tag autocomplete for the filter bar ----
function TagFilterInput({ value, onChange }) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await client.get(
          `/tags/tags/autocomplete/?q=${encodeURIComponent(query)}`
        )
        setSuggestions(res.data || [])
        setShowDropdown(true)
      } catch {
        setSuggestions([])
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    const handle = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const selectTag = (tag) => {
    onChange(tag)
    setQuery('')
    setShowDropdown(false)
  }

  if (value) {
    return (
      <div className="tag-filter-active" ref={containerRef}>
        <span className="tag-filter-label">Tag:</span>
        <span className="tag" style={tagStyle(value)}>
          {value.name}
        </span>
        <button
          type="button"
          className="tag-filter-clear"
          onClick={() => onChange(null)}
          title="Clear tag filter"
        >
          ×
        </button>
      </div>
    )
  }

  return (
    <div className="tag-filter-wrap" ref={containerRef}>
      <input
        placeholder="Filter by tag..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.trim() && setShowDropdown(true)}
        className="filter-input"
        autoComplete="off"
      />
      {showDropdown && suggestions.length > 0 && (
        <div className="tag-dropdown tag-dropdown-filter">
          {suggestions.map((tag) => (
            <div
              key={tag.id}
              className="tag-dropdown-item"
              onMouseDown={(e) => {
                e.preventDefault()
                selectTag(tag)
              }}
            >
              <span
                className="tag-dot"
                style={{ backgroundColor: tag.color || '#3b82f6' }}
              />
              <span>{tag.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---- LogPanel: create/edit a log entry ----
function LogPanel({ log, onClose, onSave }) {
  const [form, setForm] = useState({
    hostname: log?.hostname || '',
    ip_address: log?.ip_address || '',
    action: log?.action || '',
    command: log?.command || '',
    output: log?.output || '',
    status: log?.status || 'success',
    notes: log?.notes || '',
  })
  const [selectedTags, setSelectedTags] = useState(log?.tags || [])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const originalTags = log?.tags || []

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleAddTag = (tag) => {
    setSelectedTags((prev) =>
      prev.some((t) => t.id === tag.id) ? prev : [...prev, tag]
    )
  }

  const handleRemoveTag = (tagId) => {
    setSelectedTags((prev) => prev.filter((t) => t.id !== tagId))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    try {
      let logId = log?.id

      if (logId) {
        await client.patch(`/logs/logs/${logId}/`, form)
      } else {
        const res = await client.post('/logs/logs/', form)
        logId = res.data.id
      }

      // Add newly selected tags
      for (const tag of selectedTags) {
        if (!originalTags.some((t) => t.id === tag.id)) {
          await client.post('/tags/log-tag/', { log_id: logId, tag_id: tag.id })
        }
      }

      // Remove deselected tags (skip protected operation tags)
      for (const tag of originalTags) {
        if (
          !selectedTags.some((t) => t.id === tag.id) &&
          tag.category !== 'operation'
        ) {
          await client.delete('/tags/log-tag/', {
            data: { log_id: logId, tag_id: tag.id },
          })
        }
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
          <label>Tags</label>
          <TagInput
            selectedTags={selectedTags}
            onAdd={handleAddTag}
            onRemove={handleRemoveTag}
          />
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
    tag: null, // tag object {id, name, color} or null
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
      if (filters.tag) params.tag = filters.tag.name

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

  const handleTagFilterChange = (tag) => {
    setFilters((f) => ({ ...f, tag }))
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
                backgroundColor:
                  (activeOperation.tag_color || '#3B82F6') + '22',
                color: activeOperation.tag_color || '#3B82F6',
                borderColor:
                  (activeOperation.tag_color || '#3B82F6') + '55',
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
          <a href="/operations" style={{ marginLeft: '0.5rem' }}>
            Select one
          </a>
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
        <TagFilterInput
          value={filters.tag}
          onChange={handleTagFilterChange}
        />
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
                      className={`clickable-row${
                        modalLog?.id === log.id && showPanel
                          ? ' row-selected'
                          : ''
                      }`}
                    >
                      <td className="mono td-timestamp">
                        {new Date(
                          log.created_at || log.timestamp
                        ).toLocaleString()}
                      </td>
                      <td className="mono">{log.hostname}</td>
                      <td className="mono">{log.ip_address}</td>
                      <td>{log.action}</td>
                      <td>
                        <span
                          className={`status-badge ${statusClass(log.status)}`}
                        >
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
                      <td>
                        {log.operator?.username || log.operator || '-'}
                      </td>
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
