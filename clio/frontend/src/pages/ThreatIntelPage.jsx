import { useState, useRef, useEffect, useCallback } from 'react'
import client from '../api/client'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function cvssColor(score) {
  if (score == null) return 'cvss-none'
  if (score >= 9.0) return 'cvss-critical'
  if (score >= 7.0) return 'cvss-high'
  if (score >= 4.0) return 'cvss-medium'
  return 'cvss-low'
}

function domainLabel(domain) {
  return { 'enterprise-attack': 'Enterprise', 'mobile-attack': 'Mobile', 'ics-attack': 'ICS' }[domain] || domain
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function PillList({ items, className, max = 3 }) {
  if (!items) return <span className="ti-muted">—</span>
  const parts = items.split(',').map((s) => s.trim()).filter(Boolean)
  const shown = parts.slice(0, max)
  const rest = parts.length - max
  return (
    <div className="ti-pills-cell">
      {shown.map((p) => <span key={p} className={`ti-pill ${className}`}>{p}</span>)}
      {rest > 0 && <span className="ti-pill-more">+{rest}</span>}
    </div>
  )
}

function SortTh({ col, label, sort, onSort, style }) {
  const active = sort.col === col
  return (
    <th style={style} className={`ti-sortable-th${active ? ' ti-sort-active' : ''}`} onClick={() => onSort(col)}>
      {label}
      <span className="ti-sort-icon">{active ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ' ↕'}</span>
    </th>
  )
}

function Pagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null
  return (
    <div className="ti-pagination">
      <button className="btn btn-ghost btn-sm" onClick={() => onPage(page - 1)} disabled={page === 1}>← Prev</button>
      <span className="pagination-info">Page {page} of {totalPages}</span>
      <button className="btn btn-ghost btn-sm" onClick={() => onPage(page + 1)} disabled={page === totalPages}>Next →</button>
    </div>
  )
}

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
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
  const [sort, setSort] = useState({ col: 'external_id', dir: 'asc' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const debouncedSearch = useDebounce(search)
  const pageSize = 50

  const fetchData = useCallback(async (pg, q, dom, s) => {
    setLoading(true)
    setError('')
    try {
      const ordering = s.dir === 'desc' ? `-${s.col}` : s.col
      const params = { page: pg, ordering }
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

  // Re-fetch when search, domain, or sort changes
  useEffect(() => {
    setPage(1)
    setExpanded(null)
    fetchData(1, debouncedSearch, domain, sort)
  }, [debouncedSearch, domain, sort, fetchData])

  const handleSort = (col) => {
    setSort((prev) => ({ col, dir: prev.col === col && prev.dir === 'asc' ? 'desc' : 'asc' }))
  }

  const goPage = (pg) => { setPage(pg); setExpanded(null); fetchData(pg, debouncedSearch, domain, sort) }
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="ti-tab-content">
      <div className="ti-toolbar">
        <input
          className="filter-input filter-input-wide"
          placeholder="Search ID, name, or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="filter-input" value={domain} onChange={(e) => setDomain(e.target.value)}>
          <option value="">All Domains</option>
          <option value="enterprise-attack">Enterprise</option>
          <option value="mobile-attack">Mobile</option>
          <option value="ics-attack">ICS</option>
        </select>
        {search && (
          <button className="btn btn-ghost btn-sm" onClick={() => setSearch('')}>Clear</button>
        )}
        <span className="filter-count">{total.toLocaleString()} technique{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error" style={{ flexShrink: 0 }}>{error}</div>}

      <div className="ti-table-wrap">
        {loading ? (
          <div className="loading-inline"><div className="loading-spinner" /> Loading…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <p>No MITRE techniques found.</p>
            <p style={{ fontSize: 12 }}>Run <code className="mono">clio-manage ingest_threat_data</code> to populate.</p>
          </div>
        ) : (
          <table className="data-table ti-table">
            <thead>
              <tr>
                <SortTh col="external_id" label="ID" sort={sort} onSort={handleSort} style={{ width: 90 }} />
                <SortTh col="name" label="Name" sort={sort} onSort={handleSort} />
                <SortTh col="domain" label="Domain" sort={sort} onSort={handleSort} style={{ width: 110 }} />
                <SortTh col="tactics" label="Tactics" sort={sort} onSort={handleSort} style={{ width: 260 }} />
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
                    <td><span className="mono ti-technique-id">{item.external_id}</span></td>
                    <td className="ti-technique-name">{item.name}</td>
                    <td>
                      <span className={`ti-domain-badge ti-domain-${item.domain}`}>{domainLabel(item.domain)}</span>
                    </td>
                    <td><PillList items={item.tactics} className="ti-pill-tactic" max={3} /></td>
                  </tr>
                  {expanded === item.id && (
                    <tr key={`${item.id}-d`} className="ti-detail-row">
                      <td colSpan={4}>
                        <div className="ti-detail-panel">
                          <div className="ti-detail-header">
                            <span className="mono ti-technique-id">{item.external_id}</span>
                            <strong>{item.name}</strong>
                            <span className={`ti-domain-badge ti-domain-${item.domain}`}>{domainLabel(item.domain)}</span>
                          </div>
                          {item.tactics && (
                            <div className="ti-detail-meta">
                              <span className="ti-detail-label">Tactics</span>
                              <PillList items={item.tactics} className="ti-pill-tactic" max={99} />
                            </div>
                          )}
                          {item.platforms && (
                            <div className="ti-detail-meta">
                              <span className="ti-detail-label">Platforms</span>
                              <PillList items={item.platforms} className="ti-pill-platform" max={99} />
                            </div>
                          )}
                          {item.description && (
                            <div className="ti-detail-description">{item.description}</div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPage={goPage} />
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
  const [sort, setSort] = useState({ col: 'published_date', dir: 'desc' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const debouncedSearch = useDebounce(search)
  const pageSize = 50

  const fetchData = useCallback(async (pg, q, min, s) => {
    setLoading(true)
    setError('')
    try {
      const ordering = s.dir === 'desc' ? `-${s.col}` : s.col
      const params = { page: pg, ordering }
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
    setPage(1)
    setExpanded(null)
    fetchData(1, debouncedSearch, minCvss, sort)
  }, [debouncedSearch, minCvss, sort, fetchData])

  const handleSort = (col) => {
    setSort((prev) => ({ col, dir: prev.col === col && prev.dir === 'asc' ? 'desc' : 'asc' }))
  }

  const goPage = (pg) => { setPage(pg); setExpanded(null); fetchData(pg, debouncedSearch, minCvss, sort) }
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="ti-tab-content">
      <div className="ti-toolbar">
        <input
          className="filter-input filter-input-wide"
          placeholder="Search CVE ID, description, or product…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="filter-input" value={minCvss} onChange={(e) => setMinCvss(e.target.value)}>
          <option value="">Any CVSS</option>
          <option value="4.0">4.0+ Medium</option>
          <option value="7.0">7.0+ High</option>
          <option value="9.0">9.0+ Critical</option>
        </select>
        {search && (
          <button className="btn btn-ghost btn-sm" onClick={() => setSearch('')}>Clear</button>
        )}
        <span className="filter-count">{total.toLocaleString()} CVE{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error" style={{ flexShrink: 0 }}>{error}</div>}

      <div className="ti-table-wrap">
        {loading ? (
          <div className="loading-inline"><div className="loading-spinner" /> Loading…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <p>No CVEs found.</p>
            <p style={{ fontSize: 12 }}>Run <code className="mono">clio-manage ingest_threat_data</code> to populate.</p>
          </div>
        ) : (
          <table className="data-table ti-table">
            <thead>
              <tr>
                <SortTh col="cve_id" label="CVE ID" sort={sort} onSort={handleSort} style={{ width: 160 }} />
                <th>Description</th>
                <SortTh col="cvss_score" label="CVSS" sort={sort} onSort={handleSort} style={{ width: 90 }} />
                <SortTh col="published_date" label="Published" sort={sort} onSort={handleSort} style={{ width: 120 }} />
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
                    <td><span className="mono ti-cve-id">{item.cve_id}</span></td>
                    <td className="ti-cve-desc">
                      {item.description
                        ? item.description.length > 110 ? item.description.slice(0, 110) + '…' : item.description
                        : <span className="ti-muted">No description</span>}
                    </td>
                    <td>
                      {item.cvss_score != null
                        ? <span className={`ti-cvss-badge ${cvssColor(item.cvss_score)}`}>{item.cvss_score.toFixed(1)}</span>
                        : <span className="ti-muted">N/A</span>}
                    </td>
                    <td className="td-timestamp">{formatDate(item.published_date)}</td>
                  </tr>
                  {expanded === item.id && (
                    <tr key={`${item.id}-d`} className="ti-detail-row">
                      <td colSpan={4}>
                        <div className="ti-detail-panel">
                          <div className="ti-detail-header">
                            <span className="mono ti-cve-id">{item.cve_id}</span>
                            {item.cvss_score != null && (
                              <span className={`ti-cvss-badge ${cvssColor(item.cvss_score)}`}>CVSS {item.cvss_score.toFixed(1)}</span>
                            )}
                            <span className="ti-muted" style={{ fontSize: 12 }}>Published {formatDate(item.published_date)}</span>
                          </div>
                          {item.description && (
                            <div className="ti-detail-description">{item.description}</div>
                          )}
                          {item.affected_products && (
                            <div className="ti-detail-meta">
                              <span className="ti-detail-label">Affected</span>
                              <div className="ti-affected-products">
                                {item.affected_products.split('\n').filter(Boolean).map((p) => (
                                  <span key={p} className="ti-cpe-entry mono">{p}</span>
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
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPage={goPage} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Assistant (chat) tab
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
    setInput(''); setError('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const { data } = await client.post('/chat/', { message: text, thread_id: threadId })
      setThreadId(data.thread_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get a response. Check that the LLM service is running.')
    } finally {
      setLoading(false)
    }
  }, [input, loading, threadId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="ti-tab-content ti-chat-wrap">
      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">&#x1F6E1;</div>
            <p>Ask about CVEs, MITRE ATT&amp;CK techniques, or your logged operations.</p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chat-suggestion" onClick={() => setInput(s)}>{s}</button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${msg.role}`}>
                <div className="chat-bubble-label">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
                <div className="chat-bubble-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble chat-bubble-assistant">
                <div className="chat-bubble-label">Assistant</div>
                <div className="chat-thinking"><span /><span /><span /></div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      {error && <div className="alert alert-error chat-alert">{error}</div>}
      <div className="chat-input-bar">
        {messages.length > 0 && (
          <button
            className="btn btn-ghost btn-sm"
            style={{ flexShrink: 0 }}
            onClick={() => { setMessages([]); setThreadId(null); setError('') }}
          >
            New
          </button>
        )}
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
        <button className="btn btn-primary" onClick={send} disabled={loading || !input.trim()}>Send</button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const TABS = [
  { id: 'mitre', label: 'MITRE ATT\u0026CK' },
  { id: 'cves', label: 'CVEs' },
  { id: 'assistant', label: 'AI Assistant' },
]

export default function ThreatIntelPage() {
  const [activeTab, setActiveTab] = useState('mitre')

  return (
    <div className="ti-page">
      <div className="ti-page-header">
        <h1>Threat Intelligence</h1>
        <p className="ti-page-sub">Browse MITRE ATT&amp;CK techniques and NVD CVEs, or query the AI assistant</p>
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
