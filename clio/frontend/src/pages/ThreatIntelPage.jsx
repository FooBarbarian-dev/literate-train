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

const DOMAIN_LABELS = {
  'enterprise-attack': 'Enterprise',
  'mobile-attack': 'Mobile',
  'ics-attack': 'ICS',
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

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
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

// ---------------------------------------------------------------------------
// MultiSelectFilter — Excel-style checkbox dropdown attached to a column header
// ---------------------------------------------------------------------------

function MultiSelectFilter({ label, options, selected, onChange, alignRight = false }) {
  const [open, setOpen] = useState(false)
  const [localSearch, setLocalSearch] = useState('')
  const ref = useRef(null)
  const active = selected.length > 0
  // Deduplicate options by value
  const uniqueOptions = options.filter((o, i, arr) => arr.findIndex((x) => x.value === o.value) === i)

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggle = (val) =>
    onChange(selected.includes(val) ? selected.filter((v) => v !== val) : [...selected, val])

  const filtered = localSearch
    ? uniqueOptions.filter((o) => o.label.toLowerCase().includes(localSearch.toLowerCase()))
    : uniqueOptions

  return (
    <span className={`ti-msf${alignRight ? ' ti-msf-right' : ''}`} ref={ref}>
      <button
        className={`ti-msf-btn${active ? ' ti-msf-active' : ''}`}
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o) }}
        title={`Filter ${label}`}
      >
        ▾
      </button>
      {open && (
        <div className="ti-msf-dropdown">
          <div className="ti-msf-header">
            <span className="ti-msf-title">Filter: {label}</span>
            {active && <button className="ti-msf-clear" onClick={() => onChange([])}>Clear</button>}
          </div>
          {uniqueOptions.length > 8 && (
            <input
              className="ti-msf-search"
              placeholder="Search…"
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              autoFocus
            />
          )}
          <div className="ti-msf-list">
            {filtered.length === 0
              ? <span className="ti-muted" style={{ padding: '6px 10px', display: 'block' }}>No matches</span>
              : filtered.map((opt) => (
                <label key={opt.value} className="ti-msf-item">
                  <input type="checkbox" checked={selected.includes(opt.value)} onChange={() => toggle(opt.value)} />
                  {opt.icon && <span className={opt.icon} />}
                  <span>{opt.label}</span>
                  {opt.badge && <span className={`ti-cvss-badge ${opt.badge} ti-msf-badge`}>{opt.value}</span>}
                </label>
              ))}
          </div>
        </div>
      )}
    </span>
  )
}

// ---------------------------------------------------------------------------
// DateFilter — preset date ranges for the Published column
// ---------------------------------------------------------------------------

const DATE_PRESETS = [
  { label: 'All time', value: '' },
  { label: 'Last 30 days', value: '30d' },
  { label: 'Last 90 days', value: '90d' },
  { label: 'Last year', value: '1y' },
  { label: 'Last 2 years', value: '2y' },
  { label: 'Custom range', value: 'custom' },
]

function dateFromPreset(preset) {
  const now = new Date()
  if (preset === '30d') { const d = new Date(now); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10) }
  if (preset === '90d') { const d = new Date(now); d.setDate(d.getDate() - 90); return d.toISOString().slice(0, 10) }
  if (preset === '1y')  { const d = new Date(now); d.setFullYear(d.getFullYear() - 1); return d.toISOString().slice(0, 10) }
  if (preset === '2y')  { const d = new Date(now); d.setFullYear(d.getFullYear() - 2); return d.toISOString().slice(0, 10) }
  return ''
}

function DateFilter({ dateFilter, onChange, alignRight = false }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const active = !!(dateFilter.preset && dateFilter.preset !== '')

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const setPreset = (preset) => {
    if (preset === 'custom') {
      onChange({ preset: 'custom', after: dateFilter.after || '', before: dateFilter.before || '' })
    } else {
      onChange({ preset, after: dateFromPreset(preset), before: '' })
    }
  }

  return (
    <span className={`ti-msf${alignRight ? ' ti-msf-right' : ''}`} ref={ref}>
      <button
        className={`ti-msf-btn${active ? ' ti-msf-active' : ''}`}
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o) }}
        title="Filter by date"
      >
        ▾
      </button>
      {open && (
        <div className="ti-msf-dropdown ti-date-dropdown">
          <div className="ti-msf-header">
            <span className="ti-msf-title">Published</span>
            {active && <button className="ti-msf-clear" onClick={() => onChange({ preset: '', after: '', before: '' })}>Clear</button>}
          </div>
          <div className="ti-msf-list">
            {DATE_PRESETS.map((p) => (
              <label key={p.value} className="ti-msf-item">
                <input
                  type="radio"
                  name="date-preset"
                  checked={dateFilter.preset === p.value}
                  onChange={() => setPreset(p.value)}
                />
                <span>{p.label}</span>
              </label>
            ))}
          </div>
          {dateFilter.preset === 'custom' && (
            <div className="ti-date-custom">
              <label className="ti-date-label">From
                <input
                  type="date"
                  className="filter-input"
                  value={dateFilter.after}
                  onChange={(e) => onChange({ ...dateFilter, after: e.target.value })}
                />
              </label>
              <label className="ti-date-label">To
                <input
                  type="date"
                  className="filter-input"
                  value={dateFilter.before}
                  onChange={(e) => onChange({ ...dateFilter, before: e.target.value })}
                />
              </label>
            </div>
          )}
        </div>
      )}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Column header: sort + optional filter
// ---------------------------------------------------------------------------

function FilterSortTh({ col, label, sort, onSort, filter, style }) {
  const active = sort.col === col
  return (
    <th style={style} className="ti-filter-sort-th">
      <div className="ti-th-inner">
        <span
          className={`ti-sortable-th${active ? ' ti-sort-active' : ''}`}
          onClick={() => onSort(col)}
        >
          {label}
          <span className="ti-sort-icon">{active ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ' ↕'}</span>
        </span>
        {filter}
      </div>
    </th>
  )
}

// ---------------------------------------------------------------------------
// MITRE ATT&CK tab
// ---------------------------------------------------------------------------

const CVSS_SEVERITY_OPTIONS = [
  { value: 'critical', label: 'Critical (9.0+)', badge: 'cvss-critical' },
  { value: 'high',     label: 'High (7.0–8.9)',  badge: 'cvss-high' },
  { value: 'medium',   label: 'Medium (4.0–6.9)', badge: 'cvss-medium' },
  { value: 'low',      label: 'Low (0–3.9)',      badge: 'cvss-low' },
  { value: 'none',     label: 'No score',         badge: null },
]

function MitreTab() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [domains, setDomains] = useState([])   // selected domain values
  const [tactics, setTactics] = useState([])   // selected tactic values
  const [sort, setSort] = useState({ col: 'external_id', dir: 'asc' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const [facets, setFacets] = useState({ domains: [], tactics: [] })
  const debouncedSearch = useDebounce(search)
  const pageSize = 50

  // Load facets once
  useEffect(() => {
    client.get('/threat-intel/mitre/facets/').then(({ data }) => setFacets(data)).catch(() => {})
  }, [])

  const fetchData = useCallback(async (pg, q, doms, tacs, s) => {
    setLoading(true)
    setError('')
    try {
      const ordering = s.dir === 'desc' ? `-${s.col}` : s.col
      const params = new URLSearchParams({ page: pg, ordering })
      if (q) params.set('search', q)
      doms.forEach((d) => params.append('domain', d))
      tacs.forEach((t) => params.append('tactic', t))
      const { data } = await client.get(`/threat-intel/mitre/?${params}`)
      setItems(data.results ?? data)
      setTotal(data.count ?? (data.results ?? data).length)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load MITRE techniques.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setPage(1); setExpanded(null)
    fetchData(1, debouncedSearch, domains, tactics, sort)
  }, [debouncedSearch, domains, tactics, sort, fetchData])

  const handleSort = (col) =>
    setSort((prev) => ({ col, dir: prev.col === col && prev.dir === 'asc' ? 'desc' : 'asc' }))

  const goPage = (pg) => { setPage(pg); setExpanded(null); fetchData(pg, debouncedSearch, domains, tactics, sort) }
  const totalPages = Math.ceil(total / pageSize)

  const domainOptions = facets.domains.map((d) => ({ value: d, label: DOMAIN_LABELS[d] || d }))
  const tacticOptions = facets.tactics.map((t) => ({ value: t, label: t }))

  return (
    <div>
      <div className="ti-toolbar">
        <input
          className="filter-input filter-input-wide"
          placeholder="Search ID, name, or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && <button className="btn btn-ghost btn-sm" onClick={() => setSearch('')}>Clear</button>}
        {(domains.length > 0 || tactics.length > 0) && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setDomains([]); setTactics([]) }}>
            Clear filters
          </button>
        )}
        <span className="filter-count">{total.toLocaleString()} technique{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

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
                <FilterSortTh col="external_id" label="ID" sort={sort} onSort={handleSort} style={{ width: 90 }} />
                <FilterSortTh col="name" label="Name" sort={sort} onSort={handleSort} />
                <FilterSortTh
                  col="domain" label="Domain" sort={sort} onSort={handleSort} style={{ width: 130 }}
                  filter={<MultiSelectFilter label="Domain" options={domainOptions} selected={domains} onChange={setDomains} />}
                />
                <FilterSortTh
                  col="tactics" label="Tactics" sort={sort} onSort={handleSort} style={{ width: 280 }}
                  filter={<MultiSelectFilter label="Tactics" options={tacticOptions} selected={tactics} onChange={setTactics} />}
                />
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
                      <span className={`ti-domain-badge ti-domain-${item.domain}`}>
                        {DOMAIN_LABELS[item.domain] || item.domain}
                      </span>
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
                            <span className={`ti-domain-badge ti-domain-${item.domain}`}>
                              {DOMAIN_LABELS[item.domain] || item.domain}
                            </span>
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
  const [cvssFilter, setCvssFilter] = useState([])
  const [dateFilter, setDateFilter] = useState({ preset: '', after: '', before: '' })
  const [sort, setSort] = useState({ col: 'published_date', dir: 'desc' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const debouncedSearch = useDebounce(search)
  const pageSize = 50

  const fetchData = useCallback(async (pg, q, cvss, date, s) => {
    setLoading(true)
    setError('')
    try {
      const ordering = s.dir === 'desc' ? `-${s.col}` : s.col
      const params = new URLSearchParams({ page: pg, ordering })
      if (q) params.set('search', q)
      cvss.forEach((v) => params.append('cvss_severity', v))
      if (date.after) params.set('published_after', date.after)
      if (date.before) params.set('published_before', date.before)
      const { data } = await client.get(`/threat-intel/cves/?${params}`)
      setItems(data.results ?? data)
      setTotal(data.count ?? (data.results ?? data).length)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load CVEs.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setPage(1); setExpanded(null)
    fetchData(1, debouncedSearch, cvssFilter, dateFilter, sort)
  }, [debouncedSearch, cvssFilter, dateFilter, sort, fetchData])

  const handleSort = (col) =>
    setSort((prev) => ({ col, dir: prev.col === col && prev.dir === 'asc' ? 'desc' : 'asc' }))

  const goPage = (pg) => { setPage(pg); setExpanded(null); fetchData(pg, debouncedSearch, cvssFilter, dateFilter, sort) }
  const totalPages = Math.ceil(total / pageSize)

  const filtersActive = cvssFilter.length > 0 || (dateFilter.preset && dateFilter.preset !== '')

  return (
    <div>
      <div className="ti-toolbar">
        <input
          className="filter-input filter-input-wide"
          placeholder="Search CVE ID, description, or product…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && <button className="btn btn-ghost btn-sm" onClick={() => setSearch('')}>Clear</button>}
        {filtersActive && (
          <button className="btn btn-ghost btn-sm" onClick={() => { setCvssFilter([]); setDateFilter({ preset: '', after: '', before: '' }) }}>
            Clear filters
          </button>
        )}
        <span className="filter-count">{total.toLocaleString()} CVE{total !== 1 ? 's' : ''}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

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
                <FilterSortTh col="cve_id" label="CVE ID" sort={sort} onSort={handleSort} style={{ width: 160 }} />
                <th>Description</th>
                <FilterSortTh
                  col="cvss_score" label="CVSS" sort={sort} onSort={handleSort} style={{ width: 100 }}
                  filter={<MultiSelectFilter label="CVSS" options={CVSS_SEVERITY_OPTIONS} selected={cvssFilter} onChange={setCvssFilter} alignRight />}
                />
                <FilterSortTh
                  col="published_date" label="Published" sort={sort} onSort={handleSort} style={{ width: 140 }}
                  filter={<DateFilter dateFilter={dateFilter} onChange={setDateFilter} alignRight />}
                />
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
    <div className="ti-chat-tab">
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
  { id: 'cves',  label: 'CVEs' },
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
        {activeTab === 'cves'  && <CveTab />}
        {activeTab === 'assistant' && <AssistantTab />}
      </div>
    </div>
  )
}
