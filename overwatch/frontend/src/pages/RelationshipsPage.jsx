import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'

const RELATION_TYPES = [
  { key: 'host', label: 'Host' },
  { key: 'ip', label: 'IP' },
  { key: 'domain', label: 'Domain' },
  { key: 'user_command', label: 'User Commands' },
]

function RelationTypeFilter({ activeType, onChange }) {
  return (
    <div className="rel-tabs">
      {RELATION_TYPES.map((t) => (
        <button
          key={t.key}
          className={`rel-tab ${activeType === t.key ? 'rel-tab-active' : ''}`}
          onClick={() => onChange(t.key)}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

function RelationSummary({ nodes, edges }) {
  return (
    <div className="rel-summary">
      {edges.length} relation{edges.length !== 1 ? 's' : ''} found | {nodes.length} node{nodes.length !== 1 ? 's' : ''}
    </div>
  )
}

function RelationTree({ nodes, edges }) {
  const [expanded, setExpanded] = useState(new Set())

  // Build adjacency: for each node, collect edges where it's source or target
  const adjacency = {}
  for (const node of nodes) {
    adjacency[node.id] = []
  }
  for (const edge of edges) {
    if (adjacency[edge.source]) {
      adjacency[edge.source].push({ ...edge, peer: edge.target })
    }
    if (adjacency[edge.target]) {
      adjacency[edge.target].push({ ...edge, peer: edge.source })
    }
  }

  // Sort nodes by connections descending
  const sorted = [...nodes].sort((a, b) => (b.connections || 0) - (a.connections || 0))

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  if (nodes.length === 0) {
    return <div className="rel-empty">No relations found for this type.</div>
  }

  return (
    <div className="rel-tree">
      {sorted.map((node) => {
        const isExpanded = expanded.has(node.id)
        const nodeEdges = adjacency[node.id] || []
        return (
          <div key={node.id} className="rel-tree-node">
            <div
              className="rel-tree-row"
              onClick={() => toggle(node.id)}
            >
              <span className="rel-tree-arrow">{isExpanded ? '\u25BC' : '\u25B6'}</span>
              <span className="rel-tree-value">{node.value}</span>
              <span className="rel-tree-count">
                ({node.connections || nodeEdges.length} link{(node.connections || nodeEdges.length) !== 1 ? 's' : ''})
              </span>
            </div>
            {isExpanded && nodeEdges.length > 0 && (
              <div className="rel-tree-children">
                {nodeEdges.map((edge, i) => {
                  const peerValue = edge.peer.split(':').slice(1).join(':')
                  return (
                    <div key={i} className="rel-tree-edge">
                      <span className="rel-tree-branch">
                        {i === nodeEdges.length - 1 ? '\u2514\u2500' : '\u251C\u2500'}
                      </span>
                      <span className="rel-tree-peer">{peerValue}</span>
                      <span className="rel-tree-strength">strength:{edge.strength}</span>
                      {edge.operation_tags && edge.operation_tags.length > 0 && (
                        <span className="rel-tree-tags">
                          {edge.operation_tags.map((tag, j) => (
                            <span key={j} className="rel-tree-tag">[{tag}]</span>
                          ))}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function RelationshipsPage() {
  const [activeType, setActiveType] = useState('host')
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchGraph = useCallback(async (type) => {
    setLoading(true)
    setError('')
    try {
      const res = await client.get('/relations/relations/graph/', {
        params: { relationship_type: type },
      })
      setGraphData(res.data)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to load relations'
      )
      setGraphData({ nodes: [], edges: [] })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchGraph(activeType)
  }, [activeType, fetchGraph])

  const handleTabChange = (type) => {
    setActiveType(type)
  }

  const handleRefresh = () => {
    fetchGraph(activeType)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Relationships</h1>
        <button
          className="btn btn-sm btn-ghost"
          onClick={handleRefresh}
          disabled={loading}
        >
          &#8635; Refresh
        </button>
      </div>

      <RelationTypeFilter activeType={activeType} onChange={handleTabChange} />

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="rel-loading">Loading relations...</div>
      ) : (
        <>
          <RelationSummary nodes={graphData.nodes} edges={graphData.edges} />
          <RelationTree nodes={graphData.nodes} edges={graphData.edges} />
        </>
      )}
    </div>
  )
}
