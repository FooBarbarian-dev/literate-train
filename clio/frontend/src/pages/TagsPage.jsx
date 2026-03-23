import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

function CreateTagModal({ onClose, onSave }) {
  const [form, setForm] = useState({ name: '', description: '', color: '#3b82f6' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await client.post('/tags/tags/', form)
      onSave()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          'Failed to create tag'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Tag</h2>
          <button className="btn btn-ghost" onClick={onClose}>
            &#10005;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label>Tag Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., privilege-escalation"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <input
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="Tag description..."
            />
          </div>

          <div className="form-group">
            <label>Color</label>
            <div className="color-input-row">
              <input
                type="color"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                className="color-picker"
              />
              <input
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                placeholder="#3b82f6"
                className="color-text"
              />
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Creating...' : 'Create Tag'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TagsPage() {
  const { user } = useAuth()
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const fetchTags = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await client.get('/tags/tags/')
      const data = response.data
      setTags(Array.isArray(data) ? data : data.results || [])
    } catch {
      setError('Failed to fetch tags')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTags()
  }, [fetchTags])

  const filteredTags = tags.filter(
    (tag) =>
      tag.name?.toLowerCase().includes(search.toLowerCase()) ||
      tag.description?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="page">
      <div className="page-header">
        <h1>Tags</h1>
        {user?.is_admin && (
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + New Tag
          </button>
        )}
      </div>

      <div className="filters-bar">
        <input
          placeholder="Search tags..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="filter-input filter-input-wide"
        />
        <span className="filter-count">
          {filteredTags.length} tag{filteredTags.length !== 1 ? 's' : ''}
        </span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-inline">
          <div className="loading-spinner" />
          <span>Loading tags...</span>
        </div>
      ) : filteredTags.length === 0 ? (
        <div className="empty-state">
          <p>{search ? 'No tags match your search.' : 'No tags found.'}</p>
          {user?.is_admin && !search && (
            <button
              className="btn btn-primary"
              onClick={() => setShowCreate(true)}
            >
              Create your first tag
            </button>
          )}
        </div>
      ) : (
        <div className="tags-grid">
          {filteredTags.map((tag) => (
            <div key={tag.id || tag.name} className="tag-card">
              <div className="tag-card-header">
                <span
                  className="tag-dot"
                  style={{ backgroundColor: tag.color || '#3b82f6' }}
                />
                <span className="tag-name">{tag.name}</span>
              </div>
              {tag.description && (
                <p className="tag-description">{tag.description}</p>
              )}
              <div className="tag-card-meta">
                {tag.log_count !== undefined && (
                  <span className="tag-usage">
                    Used in {tag.log_count} log{tag.log_count !== 1 ? 's' : ''}
                  </span>
                )}
                {tag.usage_count !== undefined && (
                  <span className="tag-usage">
                    Used {tag.usage_count} time
                    {tag.usage_count !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateTagModal
          onClose={() => setShowCreate(false)}
          onSave={() => {
            setShowCreate(false)
            fetchTags()
          }}
        />
      )}
    </div>
  )
}
