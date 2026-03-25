import { useState, useRef, useEffect, useCallback } from 'react'
import client from '../api/client'

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function cvssColor(score) {
  if (score === null || score === undefined) return 'cvss-none'
  if (score >= 9.0) return 'cvss-critical'
  if (score >= 7.0) return 'cvss-high'
  if (score >= 4.0) return 'cvss-medium'
  return 'cvss-low'
}

function domainLabel(domain) {
  const map = {
    'enterprise-attack': 'Enterprise',
    'mobile-attack': 'Mobile',
    'ics-attack': 'ICS',
  }
  return map[domain] || domain
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// ---------------------------------------------------------------------------
// MITRE ATT&CK tab
// ---------------------------------------------------------------------------

function MitreTab() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const searchRef = useRef(null)
  const pageSize = 50

  const fetchData = useCallback(async (pg, q, dom) => {
    setLoading(true)
    setError('')
    try {
      const params = { page: pg }
      if (q) params.search = q
      if (dom) params.domain = dom
      const { data } = await client.get('/threat-intel/mitre/', { params })
      setItems(data.results ?? data)
      setTotal(data.count ?? (data.results ?? data).length)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load MITRE techniques.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(1, '', '')
  }, [fetchData])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setExpanded(null)
    fetchData(1, search, domain)
  }

  const handleDomainChange = (e) => {
    const val = e.target.value
    setDomain(val)
    setPage(1)
    setExpanded(null)
    fetchData(1, search, val)
  }

  const goPage = (pg) => {
    setPage(pg)
    setExpanded(null)
    fetchData(pg, search, domain)
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="ti-tab-content">
      <div className="filters-bar">
        <form onSubmit={handleSearch} style={{ display: 'contents' }}>
          <input
            ref={searchRef}
            className="filter-input filter-input-wide"
            placeholder="Search by ID, name, or description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className="btn btn-primary btn-sm" type="submit">
            Search
          </button>
        </form>
        <select
          className="filter-input"
          value={domain}
          onChange={handleDomainChange}
        >
          <option value="">All Domains</option>
          <option value="enterprise-attack">Enterprise</option>
          <option value="mobile-attack">Mobile</option>
          <option value="ics-attack">ICS</option>
        </select>
        <span className="filter-count">{total} technique{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-inline">
          <div className="loading-spinner" />
          Loading techniques…
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <p>No MITRE techniques found.</p>
          <p style={{ fontSize: 12 }}>
            Run <code className="mono">clio-manage ingest_threat_data</code> to populate.
          </p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 100 }}>ID</th>
                  <th>Name</th>
                  <th>Domain</th>
                  <th>Tactics</th>
                  <th>Platforms</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <>
                    <tr
                      key={item.id}
                      className={`clickable-row${expanded === item.id ? ' row-selected' : ''}`}
                      onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                    >
                      <td>
                        <span className="mono ti-technique-id">{item.external_id}</span>
                      </td>
                      <td className="ti-technique-name">{item.name}</td>
                      <td>
                        <span className={`ti-domain-badge ti-domain-${item.domain}`}>
                          {domainLabel(item.domain)}
                        </span>
                      </td>
                      <td className="ti-pills-cell">
                        {item.tactics
                          ? item.tactics.split(',').map((t) => (
                              <span key={t} className="ti-pill ti-pill-tactic">
                                {t.trim()}
                              </span>
                            ))
                          : <span className="ti-muted">—</span>}
                      </td>
                      <td className="ti-pills-cell">
                        {item.platforms
                          ? item.platforms.split(',').slice(0, 4).map((p) => (
                              <span key={p} className="ti-pill ti-pill-platform">
                                {p.trim()}
                              </span>
                            ))
                          : <span className="ti-muted">—</span>}
                        {item.platforms && item.platforms.split(',').length > 4 && (
                          <span className="ti-pill-more">
                            +{item.platforms.split(',').length - 4}
                          </span>
                        )}
                      </td>
                    </tr>
                    {expanded === item.id && (
                      <tr key={`${item.id}-detail`} className="ti-detail-row">
                        <td colSpan={5}>
                          <div className="ti-detail-panel">
                            <div className="ti-detail-header">
                              <span className="mono ti-technique-id">{item.external_id}</span>
                              <strong>{item.name}</strong>
                              <span className={`ti-domain-badge ti-domain-${item.domain}`}>
                                {domainLabel(item.domain)}
                              </span>
                            </div>
                            {item.tactics && (
                              <div className="ti-detail-row-meta">
                                <span className="ti-detail-label">Tactics</span>
                                <div className="ti-pills-cell">
                                  {item.tactics.split(',').map((t) => (
                                    <span key={t} className="ti-pill ti-pill-tactic">
                                      {t.trim()}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {item.platforms && (
                              <div className="ti-detail-row-meta">
                                <span className="ti-detail-label">Platforms</span>
                                <div className="ti-pills-cell">
                                  {item.platforms.split(',').map((p) => (
                                    <span key={p} className="ti-pill ti-pill-platform">
                                      {p.trim()}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {item.description && (
                              <div className="ti-detail-description">
                                {item.description}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => goPage(page - 1)}
                disabled={page === 1}
              >
                ← Prev
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => goPage(page + 1)}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// CVE tab
// ---------------------------------------------------------------------------

function CveTab() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [minCvss, setMinCvss] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const pageSize = 50

  const fetchData = useCallback(async (pg, q, min) => {
    setLoading(true)
    setError('')
    try {
      const params = { page: pg }
      if (q) params.search = q
      if (min) params.min_cvss = min
      const { data } = await client.get('/threat-intel/cves/', { params })
      setItems(data.results ?? data)
      setTotal(data.count ?? (data.results ?? data).length)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load CVEs.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(1, '', '')
  }, [fetchData])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setExpanded(null)
    fetchData(1, search, minCvss)
  }

  const handleMinCvssChange = (e) => {
    const val = e.target.value
    setMinCvss(val)
    setPage(1)
    setExpanded(null)
    fetchData(1, search, val)
  }

  const goPage = (pg) => {
    setPage(pg)
    setExpanded(null)
    fetchData(pg, search, minCvss)
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="ti-tab-content">
      <div className="filters-bar">
        <form onSubmit={handleSearch} style={{ display: 'contents' }}>
          <input
            className="filter-input filter-input-wide"
            placeholder="Search by CVE ID, description, or product…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className="btn btn-primary btn-sm" type="submit">
            Search
          </button>
        </form>
        <select
          className="filter-input"
          value={minCvss}
          onChange={handleMinCvssChange}
        >
          <option value="">Any CVSS</option>
          <option value="4.0">4.0+ (Medium)</option>
          <option value="7.0">7.0+ (High)</option>
          <option value="9.0">9.0+ (Critical)</option>
        </select>
        <span className="filter-count">{total} CVE{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-inline">
          <div className="loading-spinner" />
          Loading CVEs…
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <p>No CVEs found.</p>
          <p style={{ fontSize: 12 }}>
            Run <code className="mono">clio-manage ingest_threat_data</code> to populate.
          </p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 160 }}>CVE ID</th>
                  <th>Description</th>
                  <th style={{ width: 100 }}>CVSS</th>
                  <th style={{ width: 130 }}>Published</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <>
                    <tr
                      key={item.id}
                      className={`clickable-row${expanded === item.id ? ' row-selected' : ''}`}
                      onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                    >
                      <td>
                        <span className="mono ti-cve-id">{item.cve_id}</span>
                      </td>
                      <td className="ti-cve-desc">
                        {item.description
                          ? item.description.length > 140
                            ? item.description.slice(0, 140) + '…'
                            : item.description
                          : <span className="ti-muted">No description</span>}
                      </td>
                      <td>
                        {item.cvss_score !== null && item.cvss_score !== undefined ? (
                          <span className={`ti-cvss-badge ${cvssColor(item.cvss_score)}`}>
                            {item.cvss_score.toFixed(1)}
                          </span>
                        ) : (
                          <span className="ti-muted">N/A</span>
                        )}
                      </td>
                      <td className="td-timestamp">{formatDate(item.published_date)}</td>
                    </tr>
                    {expanded === item.id && (
                      <tr key={`${item.id}-detail`} className="ti-detail-row">
                        <td colSpan={4}>
                          <div className="ti-detail-panel">
                            <div className="ti-detail-header">
                              <span className="mono ti-cve-id">{item.cve_id}</span>
                              {item.cvss_score !== null && item.cvss_score !== undefined && (
                                <span className={`ti-cvss-badge ${cvssColor(item.cvss_score)}`}>
                                  CVSS {item.cvss_score.toFixed(1)}
                                </span>
                              )}
                              <span className="ti-muted" style={{ fontSize: 12 }}>
                                Published {formatDate(item.published_date)}
                              </span>
                            </div>
                            {item.description && (
                              <div className="ti-detail-description">
                                {item.description}
                              </div>
                            )}
                            {item.affected_products && (
                              <div className="ti-detail-row-meta">
                                <span className="ti-detail-label">Affected Products</span>
                                <div className="ti-affected-products">
                                  {item.affected_products
                                    .split('\n')
                                    .filter(Boolean)
                                    .map((p) => (
                                      <span key={p} className="ti-cpe-entry mono">
                                        {p}
                                      </span>
                                    ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => goPage(page - 1)}
                disabled={page === 1}
              >
                ← Prev
              </button>
              <span className="pagination-info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => goPage(page + 1)}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Assistant (chat) tab — inlined from ChatPage
// ---------------------------------------------------------------------------

const SUGGESTIONS = [
  'What MITRE techniques are commonly used in ransomware attacks?',
  'Find CVEs with a CVSS score above 9.0 affecting Windows',
  'Summarize recent log activity across all operations',
]

function AssistantTab() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [threadId, setThreadId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [input])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const { data } = await client.post('/chat/', { message: text, thread_id: threadId })
      setThreadId(data.thread_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setError(
        err.response?.data?.error ||
          'Failed to get a response. Check that the LLM service is running.'
      )
    } finally {
      setLoading(false)
    }
  }, [input, loading, threadId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const newThread = () => {
    setMessages([])
    setThreadId(null)
    setError('')
    textareaRef.current?.focus()
  }

  return (
    <div className="chat-page ti-chat-embed">
      <div className="ti-chat-toolbar">
        {messages.length > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={newThread}>
            New Conversation
          </button>
        )}
      </div>
      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">&#x1F6E1;</div>
            <p>Ask about CVEs, MITRE ATT&amp;CK techniques, or your logged operations.</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chat-suggestion" onClick={() => setInput(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${msg.role}`}>
                <div className="chat-bubble-label">
                  {msg.role === 'user' ? 'You' : 'Assistant'}
                </div>
                <div className="chat-bubble-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble chat-bubble-assistant">
                <div className="chat-bubble-label">Assistant</div>
                <div className="chat-thinking">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      {error && <div className="alert alert-error chat-alert">{error}</div>}
      <div className="chat-input-bar">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about CVEs, ATT&CK techniques, or your operation logs… (Enter to send)"
          rows={1}
          disabled={loading}
        />
        <button
          className="btn btn-primary"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main ThreatIntelPage with tabs
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'mitre', label: 'MITRE ATT\u0026CK' },
  { id: 'cves', label: 'CVEs' },
  { id: 'assistant', label: 'AI Assistant' },
]

export default function ThreatIntelPage() {
  const [activeTab, setActiveTab] = useState('mitre')

  return (
    <div className="page ti-page">
      <div className="page-header">
        <div>
          <h1>Threat Intelligence</h1>
          <p className="ti-page-sub">
            Browse MITRE ATT&amp;CK techniques, NVD CVEs, and query the AI assistant
          </p>
        </div>
      </div>

      <div className="ti-tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`ti-tab${activeTab === tab.id ? ' ti-tab-active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="ti-tab-panel">
        {activeTab === 'mitre' && <MitreTab />}
        {activeTab === 'cves' && <CveTab />}
        {activeTab === 'assistant' && <AssistantTab />}
      </div>
    </div>
  )
}
