import { useState } from 'react'
import client from '../api/client'

const ALL_FIELDS = [
  { name: 'id', type: 'integer' },
  { name: 'timestamp', type: 'timestamp with time zone' },
  { name: 'internal_ip', type: 'character varying' },
  { name: 'external_ip', type: 'character varying' },
  { name: 'mac_address', type: 'character varying' },
  { name: 'hostname', type: 'character varying' },
  { name: 'domain', type: 'character varying' },
  { name: 'username', type: 'character varying' },
  { name: 'command', type: 'text' },
  { name: 'notes', type: 'text' },
  { name: 'filename', type: 'character varying' },
  { name: 'status', type: 'character varying' },
  { name: 'hash_algorithm', type: 'character varying' },
  { name: 'hash_value', type: 'character varying' },
  { name: 'pid', type: 'character varying' },
  { name: 'analyst', type: 'character varying' },
  { name: 'locked', type: 'boolean' },
  { name: 'locked_by', type: 'character varying' },
  { name: 'created_at', type: 'timestamp with time zone' },
  { name: 'updated_at', type: 'timestamp with time zone' },
]

// Fields selected by default (mirrors what the backend considered "safe" defaults)
const DEFAULT_SELECTED = new Set([
  'id', 'timestamp', 'hostname', 'domain', 'username',
  'command', 'filename', 'status', 'analyst',
])

export default function ExportPage() {
  const [selected, setSelected] = useState(new Set(DEFAULT_SELECTED))
  const [format, setFormat] = useState('csv')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleField = (name) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }
      return next
    })
  }

  const selectAll = () => setSelected(new Set(ALL_FIELDS.map((f) => f.name)))
  const clearAll = () => setSelected(new Set())

  const handleExport = async () => {
    if (selected.size === 0) {
      setError('Select at least one column to export.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const fieldsParam = ALL_FIELDS.filter((f) => selected.has(f.name))
        .map((f) => f.name)
        .join(',')
      const response = await client.get(`/export/${format}/`, {
        params: { fields: fieldsParam },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `overwatch-export.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      setError('Export failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Split fields into two columns for the grid layout
  const half = Math.ceil(ALL_FIELDS.length / 2)
  const leftCol = ALL_FIELDS.slice(0, half)
  const rightCol = ALL_FIELDS.slice(half)

  return (
    <div className="page">
      <div className="page-header">
        <h1>Export Database</h1>
      </div>

      <div className="export-layout">
        {/* ── Left panel: column selector ─────────────────────────── */}
        <div className="export-panel">
          <div className="export-panel-header">
            <h2>Select Columns</h2>
            <div className="btn-group">
              <button className="btn btn-sm btn-ghost" onClick={selectAll}>
                Select All
              </button>
              <button className="btn btn-sm btn-ghost" onClick={clearAll}>
                Clear
              </button>
            </div>
          </div>

          {/* Export type */}
          <div className="export-type-row">
            <span className="export-type-label">Export Type:</span>
            <div className="btn-group export-type-toggle">
              <button
                className={`btn btn-sm ${format === 'csv' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setFormat('csv')}
              >
                CSV Only
              </button>
              <button
                className={`btn btn-sm ${format === 'json' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setFormat('json')}
              >
                JSON
              </button>
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          {/* Field checkboxes – two-column grid */}
          <div className="export-fields-grid">
            {[leftCol, rightCol].map((col, ci) => (
              <div key={ci} className="export-fields-col">
                {col.map((field) => (
                  <label key={field.name} className="export-field-row">
                    <input
                      type="checkbox"
                      checked={selected.has(field.name)}
                      onChange={() => toggleField(field.name)}
                      className="export-field-checkbox"
                    />
                    <span className="export-field-name">{field.name}</span>
                    <span className="export-field-type">{field.type}</span>
                  </label>
                ))}
              </div>
            ))}
          </div>

          <div className="export-actions">
            <button
              className="btn btn-primary"
              onClick={handleExport}
              disabled={loading || selected.size === 0}
            >
              {loading ? 'Exporting…' : `Export Selected Columns`}
            </button>
            <span className="export-count-hint">
              {selected.size} / {ALL_FIELDS.length} columns selected
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
