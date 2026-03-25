import { useState, useEffect, useCallback, useRef } from 'react'
import client from '../api/client'

/* ---- Card field configuration ---- */
const ALL_FIELDS = [
  { key: 'internal_ip',    label: 'Internal IP',    section: 'network' },
  { key: 'external_ip',   label: 'External IP',    section: 'network' },
  { key: 'mac_address',   label: 'MAC Address',    section: 'network' },
  { key: 'hostname',      label: 'Hostname',       section: 'network' },
  { key: 'domain',        label: 'Domain',         section: 'network' },
  { key: 'username',      label: 'User',           section: 'command' },
  { key: 'command',       label: 'Command',        section: 'command' },
  { key: 'notes',         label: 'Notes',          section: 'command' },
  { key: 'secrets',       label: 'Secrets',        section: 'command' },
  { key: 'analyst',       label: 'Analyst',        section: 'command' },
  { key: 'filename',      label: 'Filename',       section: 'file' },
  { key: 'hash_algorithm',label: 'Hash Algorithm', section: 'file' },
  { key: 'hash_value',    label: 'Hash Value',     section: 'file' },
  { key: 'pid',           label: 'PID',            section: 'file' },
  { key: 'status',        label: 'Status',         section: 'file' },
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

/* ---- Helpers ---- */
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
    case 'success':     return 'status-success'
    case 'failure':     return 'status-error'
    case 'in_progress': return 'status-info'
    case 'blocked':     return 'status-warning'
    default:            return ''
  }
}

/* ---- TagInput: autocomplete tag selector with pill display ---- */
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
      if (last.category !== 'operation') onRemove(last.id)
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
    e?.preventDefault()
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
      <div className="tag-input-area" onClick={() => inputRef.current?.focus()}>
        {selectedTags.map((tag) => (
          <span key={tag.id} className="tag-pill" style={tagStyle(tag)}>
            {tag.name}
            {tag.category !== 'operation' && (
              <button
                type="button"
                className="tag-pill-remove"
                onClick={(e) => { e.stopPropagation(); onRemove(tag.id) }}
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
                  onMouseDown={(e) => { e.preventDefault(); selectTag(tag) }}
                >
                  <span className="tag-dot" style={{ backgroundColor: tag.color || '#3b82f6' }} />
                  <span>{tag.name}</span>
                  {tag.category === 'operation' && (
                    <span className="tag-dropdown-badge">op</span>
                  )}
                </div>
              ))
            : <div className="tag-dropdown-empty">No matching tags</div>
          }
          <div
            className="tag-dropdown-create"
            onMouseDown={(e) => { e.preventDefault(); openCreate() }}
          >
            + Create tag{query.trim() ? ` "${query}"` : ''}
          </div>
        </div>
      )}

      {showCreate && (
        <div className="tag-create-form">
          <div className="tag-create-form-header">
            <span>Create new tag</span>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>
              ×
            </button>
          </div>
          {createError && (
            <div className="alert alert-error" style={{ marginBottom: 8 }}>{createError}</div>
          )}
          <div>
            <input
              value={createForm.name}
              onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSubmit(e)}
              placeholder="Tag name"
              autoFocus
              className="tag-create-input"
            />
            <input
              value={createForm.description}
              onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))}
              placeholder="Description (optional)"
              className="tag-create-input"
            />
            <div className="color-input-row" style={{ marginTop: 6 }}>
              <input
                type="color"
                value={createForm.color}
                onChange={(e) => setCreateForm((f) => ({ ...f, color: e.target.value }))}
                className="color-picker"
              />
              <input
                value={createForm.color}
                onChange={(e) => setCreateForm((f) => ({ ...f, color: e.target.value }))}
                placeholder="#3b82f6"
                className="color-text"
              />
            </div>
            <div className="tag-create-actions">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary btn-sm" disabled={creating} onClick={handleCreateSubmit}>
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ---- TagFilterInput: tag autocomplete for the filter bar ---- */
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
        const res = await client.get(`/tags/tags/autocomplete/?q=${encodeURIComponent(query)}`)
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
        <span className="tag" style={tagStyle(value)}>{value.name}</span>
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
              onMouseDown={(e) => { e.preventDefault(); selectTag(tag) }}
            >
              <span className="tag-dot" style={{ backgroundColor: tag.color || '#3b82f6' }} />
              <span>{tag.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
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
          Edit
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
  const [selectedTags, setSelectedTags] = useState(log?.tags || [])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const originalTags = log?.tags || []

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value })

  const handleAddTag = (tag) =>
    setSelectedTags((prev) =>
      prev.some((t) => t.id === tag.id) ? prev : [...prev, tag]
    )

  const handleRemoveTag = (tagId) =>
    setSelectedTags((prev) => prev.filter((t) => t.id !== tagId))

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
          await client.post('/tags/tags/log-tag/', { log_id: logId, tag_id: tag.id })
        }
      }

      // Remove deselected tags (skip protected operation tags)
      for (const tag of originalTags) {
        if (
          !selectedTags.some((t) => t.id === tag.id) &&
          tag.category !== 'operation'
        ) {
          await client.delete('/tags/tags/log-tag/', {
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
            <input name="domain" value={form.domain} onChange={handleChange} placeholder="corp.local" />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Internal IP</label>
            <input name="internal_ip" value={form.internal_ip} onChange={handleChange} placeholder="10.0.0.1" />
          </div>
          <div className="form-group">
            <label>External IP</label>
            <input name="external_ip" value={form.external_ip} onChange={handleChange} placeholder="1.2.3.4" />
          </div>
        </div>
        <div className="form-group">
          <label>MAC Address</label>
          <input name="mac_address" value={form.mac_address} onChange={handleChange} placeholder="AA:BB:CC:DD:EE:FF" />
        </div>

        <div className="log-panel-section-title">Command</div>
        <div className="form-row">
          <div className="form-group">
            <label>Username</label>
            <input name="username" value={form.username} onChange={handleChange} placeholder="DOMAIN\user" />
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
          <textarea name="notes" value={form.notes} onChange={handleChange} placeholder="Additional notes..." rows={2} />
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
            <input name="filename" value={form.filename} onChange={handleChange} placeholder="malware.exe" />
          </div>
          <div className="form-group">
            <label>PID</label>
            <input name="pid" value={form.pid} onChange={handleChange} placeholder="1234" />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Hash Algorithm</label>
            <input name="hash_algorithm" value={form.hash_algorithm} onChange={handleChange} placeholder="SHA256" />
          </div>
          <div className="form-group">
            <label>Hash Value</label>
            <input name="hash_value" value={form.hash_value} onChange={handleChange} placeholder="abc123..." className="mono" />
          </div>
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
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
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
  const [filters, setFilters] = useState({
    hostname: '',
    ip_address: '',
    status: '',
    tag: null, // {id, name, color} or null
  })
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
      if (filters.hostname)   params.hostname   = filters.hostname
      if (filters.ip_address) params.internal_ip = filters.ip_address
      if (filters.status)     params.status     = filters.status
      if (filters.tag)        params.tag        = filters.tag.name

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
          <button className="btn btn-ghost btn-sm" onClick={() => setShowCardFields(true)}>
            Card Fields
          </button>
        </div>
        <button className="btn btn-primary" onClick={handleNewLog}>+ Add Row</button>
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
        <TagFilterInput value={filters.tag} onChange={handleTagFilterChange} />
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
                <span className="pagination-info">Page {page} of {totalPages}</span>
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
          <LogPanel log={modalLog} onClose={handlePanelClose} onSave={handlePanelSave} />
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
