import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'

function CreateOperationModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    name: '',
    description: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await client.post('/operations/operations/', form)
      onSave()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          'Failed to create operation'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Operation</h2>
          <button className="btn btn-ghost" onClick={onClose}>
            &#10005;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label>Operation Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Operation Thunderstrike"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              placeholder="Operation details..."
              rows={3}
            />
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
              {saving ? 'Creating...' : 'Create Operation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function OperationsPage() {
  const { user } = useAuth()
  const [operations, setOperations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [activeOpId, setActiveOpId] = useState(null)

  const fetchOperations = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const response = await client.get('/operations/operations/')
      const data = response.data
      const ops = Array.isArray(data) ? data : data.results || []
      setOperations(ops)

      const active = ops.find((op) => op.is_active)
      if (active) setActiveOpId(active.id)
    } catch {
      setError('Failed to fetch operations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchOperations()
  }, [fetchOperations])

  const handleSetActive = async (opId) => {
    try {
      await client.post('/operations/operations/set-active/', { operation_id: opId })
      setActiveOpId(opId)
      fetchOperations()
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to set active operation'
      )
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Operations</h1>
        {user?.is_admin && (
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + New Operation
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-inline">
          <div className="loading-spinner" />
          <span>Loading operations...</span>
        </div>
      ) : operations.length === 0 ? (
        <div className="empty-state">
          <p>No operations found.</p>
          {user?.is_admin && (
            <button
              className="btn btn-primary"
              onClick={() => setShowCreate(true)}
            >
              Create your first operation
            </button>
          )}
        </div>
      ) : (
        <div className="cards-grid">
          {operations.map((op) => (
            <div
              key={op.id}
              className={`card ${op.id === activeOpId ? 'card-active' : ''}`}
            >
              <div className="card-header">
                <h3>{op.name}</h3>
                {op.id === activeOpId && (
                  <span className="badge badge-active">Active</span>
                )}
              </div>
              <p className="card-description">
                {op.description || 'No description'}
              </p>
              <div className="card-meta">
                <span>
                  Created:{' '}
                  {new Date(op.created_at || op.created).toLocaleDateString()}
                </span>
                {op.users && (
                  <span>
                    {op.users.length} user{op.users.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              {op.users && op.users.length > 0 && (
                <div className="card-users">
                  {op.users.map((u, i) => (
                    <span key={i} className="badge badge-user">
                      {u.username || u}
                    </span>
                  ))}
                </div>
              )}
              <div className="card-actions">
                {op.id !== activeOpId && (
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleSetActive(op.id)}
                  >
                    Set Active
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateOperationModal
          onClose={() => setShowCreate(false)}
          onSave={() => {
            setShowCreate(false)
            fetchOperations()
          }}
        />
      )}
    </div>
  )
}
