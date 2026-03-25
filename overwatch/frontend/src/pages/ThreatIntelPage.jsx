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

// BUG 4: column definitions for the MITRE table.
// The source of truth for default visibility is this Set.  "ai_assist" is
// included so it is visible on initial page load — no localStorage override
// needed when there is no stored preference.
const MITRE_ALL_COLS = ['external_id', 'name', 'domain', 'tactics', 'ai_assist']
const MITRE_DEFAULT_VISIBLE = new Set(MITRE_ALL_COLS)

const MITRE_COL_LABELS = {
  external_id: 'ID',
  name: 'Name',
  domain: 'Domain',
  tactics: 'Tactics',
  ai_assist: 'AI Assist',
}

// BUG 4: accepts onAskAI callback from parent ThreatIntelPage.
function MitreTab({ onAskAI }) {
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

  // BUG 4: column visibility — persisted to localStorage so user prefs survive
  // refreshes.  Absence of a stored key → use MITRE_DEFAULT_VISIBLE (which
  // includes ai_assist).  This is the source of truth; no setTimeout needed.
  const [visibleCols, setVisibleCols] = useState(() => {
    try {
      const stored = localStorage.getItem('ti_mitre_visible_cols')
      if (stored) {
        const parsed = JSON.parse(stored)
        // Validate: only keep known column names; reject corrupt data
        if (Array.isArray(parsed) && parsed.every((c) => MITRE_ALL_COLS.includes(c))) {
          return new Set(parsed)
        }
      }
    } catch (_) {}
    return new Set(MITRE_DEFAULT_VISIBLE)
  })

  const toggleCol = (col) => {
    setVisibleCols((prev) => {
      const next = new Set(prev)
      if (next.has(col)) next.delete(col)
      else next.add(col)
      try {
        localStorage.setItem('ti_mitre_visible_cols', JSON.stringify([...next]))
      } catch (_) {}
      return next
    })
  }

  const [colToggleOpen, setColToggleOpen] = useState(false)
  const colToggleRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (colToggleRef.current && !colToggleRef.current.contains(e.target)) {
        setColToggleOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

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

        {/* BUG 4: column visibility toggle — source of truth is visibleCols state
            initialised from localStorage (or MITRE_DEFAULT_VISIBLE which includes
            ai_assist).  No setTimeout, no DOM mutation — pure React state. */}
        <span className="ti-col-toggle-wrap" ref={colToggleRef}>
          <button
            className="btn btn-ghost btn-sm ti-col-toggle-btn"
            onClick={() => setColToggleOpen((o) => !o)}
            title="Show/hide columns"
          >
            Columns ▾
          </button>
          {colToggleOpen && (
            <div className="ti-col-toggle-dropdown">
              {MITRE_ALL_COLS.map((col) => (
                <label key={col} className="ti-col-toggle-item">
                  <input
                    type="checkbox"
                    checked={visibleCols.has(col)}
                    onChange={() => toggleCol(col)}
                  />
                  <span>{MITRE_COL_LABELS[col]}</span>
                </label>
              ))}
            </div>
          )}
        </span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="ti-table-wrap">
        {loading ? (
          <div className="loading-inline"><div className="loading-spinner" /> Loading…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">
            <p>No MITRE techniques found.</p>
            <p style={{ fontSize: 12 }}>Run <code className="mono">overwatch-manage ingest_threat_data</code> to populate.</p>
          </div>
        ) : (
          <table className="data-table ti-table">
            <thead>
              <tr>
                {visibleCols.has('external_id') && (
                  <FilterSortTh col="external_id" label="ID" sort={sort} onSort={handleSort} style={{ width: 90 }} />
                )}
                {visibleCols.has('name') && (
                  <FilterSortTh col="name" label="Name" sort={sort} onSort={handleSort} />
                )}
                {visibleCols.has('domain') && (
                  <FilterSortTh
                    col="domain" label="Domain" sort={sort} onSort={handleSort} style={{ width: 130 }}
                    filter={<MultiSelectFilter label="Domain" options={domainOptions} selected={domains} onChange={setDomains} />}
                  />
                )}
                {visibleCols.has('tactics') && (
                  <FilterSortTh
                    col="tactics" label="Tactics" sort={sort} onSort={handleSort} style={{ width: 280 }}
                    filter={<MultiSelectFilter label="Tactics" options={tacticOptions} selected={tactics} onChange={setTactics} />}
                  />
                )}
                {/* BUG 4: AI Assist column — visible by default (included in MITRE_DEFAULT_VISIBLE) */}
                {visibleCols.has('ai_assist') && (
                  <th style={{ width: 80 }} className="ti-filter-sort-th">
                    <div className="ti-th-inner">AI Assist</div>
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const colSpan = visibleCols.size
                return (
                <>
                  <tr
                    key={item.id}
                    className={`clickable-row${expanded === item.id ? ' row-selected' : ''}`}
                    onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                  >
                    {visibleCols.has('external_id') && (
                      <td><span className="mono ti-technique-id">{item.external_id}</span></td>
                    )}
                    {visibleCols.has('name') && (
                      <td className="ti-technique-name">{item.name}</td>
                    )}
                    {visibleCols.has('domain') && (
                      <td>
                        <span className={`ti-domain-badge ti-domain-${item.domain}`}>
                          {DOMAIN_LABELS[item.domain] || item.domain}
                        </span>
                      </td>
                    )}
                    {visibleCols.has('tactics') && (
                      <td><PillList items={item.tactics} className="ti-pill-tactic" max={3} /></td>
                    )}
                    {/* BUG 4: AI Assist column cell — clicking does not expand row */}
                    {visibleCols.has('ai_assist') && (
                      <td onClick={(e) => e.stopPropagation()}>
                        <button
                          className="ti-ask-ai-btn"
                          title={`Ask AI about ${item.external_id}`}
                          onClick={() => onAskAI?.(item)}
                        >
                          ⊙ Ask AI
                        </button>
                      </td>
                    )}
                  </tr>
                  {expanded === item.id && (
                    <tr key={`${item.id}-d`} className="ti-detail-row">
                      <td colSpan={colSpan}>
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
                )
              })}
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
            <p style={{ fontSize: 12 }}>Run <code className="mono">overwatch-manage ingest_threat_data</code> to populate.</p>
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
// Assistant (chat) tab — session sidebar + multi-turn thread + RAG panel
// ---------------------------------------------------------------------------

const SUGGESTIONS = [
  'What MITRE techniques are commonly used in ransomware attacks?',
  'Find CVEs with a CVSS score above 9.0 affecting Windows',
  'Summarize recent log activity across all operations',
]

// ---- Relative timestamp helper ----
function relativeTime(iso) {
  if (!iso) return ''
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)} hr ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function RelativeTime({ iso }) {
  const [label, setLabel] = useState(() => relativeTime(iso))
  useEffect(() => {
    const t = setInterval(() => setLabel(relativeTime(iso)), 60000)
    return () => clearInterval(t)
  }, [iso])
  return <span className="ti-msg-ts">{label}</span>
}

// ---- Auto-link CVE and ATT&CK IDs in assistant messages ----
const AUTO_LINK_RE = /(CVE-\d{4}-\d{4,})|(T\d{4}(?:\.\d{3})?)/g

function renderAutoLinks(text) {
  const parts = []
  let last = 0
  let m
  AUTO_LINK_RE.lastIndex = 0
  while ((m = AUTO_LINK_RE.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index))
    if (m[1]) {
      parts.push(
        <a key={m.index} href={`https://nvd.nist.gov/vuln/detail/${m[1]}`}
           target="_blank" rel="noopener noreferrer" className="ti-auto-link">{m[1]}</a>
      )
    } else {
      const techUrl = `https://attack.mitre.org/techniques/${m[2].replace('.', '/')}/`
      parts.push(
        <a key={m.index} href={techUrl}
           target="_blank" rel="noopener noreferrer" className="ti-auto-link">{m[2]}</a>
      )
    }
    last = m.index + m[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts.length ? parts : text
}

// ---- Simple code-block renderer (no syntax highlighting library) ----
const CODE_BLOCK_RE = /```[\s\S]*?```|`[^`\n]+`/g

function renderAssistantContent(content) {
  const segments = []
  let last = 0
  let m
  CODE_BLOCK_RE.lastIndex = 0
  while ((m = CODE_BLOCK_RE.exec(content)) !== null) {
    if (m.index > last) {
      segments.push({ type: 'text', value: content.slice(last, m.index) })
    }
    if (m[0].startsWith('```')) {
      // Strip optional language hint on the opening fence line
      const inner = m[0].slice(3, -3).replace(/^[^\n]*\n/, '')
      segments.push({ type: 'block', value: inner })
    } else {
      segments.push({ type: 'inline', value: m[0].slice(1, -1) })
    }
    last = m.index + m[0].length
  }
  if (last < content.length) segments.push({ type: 'text', value: content.slice(last) })

  return segments.map((seg, i) => {
    if (seg.type === 'block') {
      return <pre key={i} className="ti-code-block"><code>{seg.value}</code></pre>
    }
    if (seg.type === 'inline') {
      return <code key={i} className="ti-inline-code">{seg.value}</code>
    }
    return <span key={i} style={{ whiteSpace: 'pre-wrap' }}>{renderAutoLinks(seg.value)}</span>
  })
}

// ---- Message bubble ----
function MessageBubble({ msg }) {
  const isAssistant = msg.role === 'assistant'
  return (
    <div className={`chat-bubble chat-bubble-${msg.role}`}>
      <div className="chat-bubble-label">{isAssistant ? '⊙ OVERWATCH' : 'You'}</div>
      <div className="chat-bubble-content">
        {isAssistant ? renderAssistantContent(msg.content) : msg.content}
      </div>
      {/* TODO: citation links — see BUG 3 in agent prompt */}
      {msg.created_at && <RelativeTime iso={msg.created_at} />}
    </div>
  )
}

// ---- Session sidebar item ----
function SessionItem({ session, active, onClick, onRename, onDelete }) {
  const [renaming, setRenaming] = useState(false)
  const [nameVal, setNameVal] = useState(session.name || '')
  const inputRef = useRef(null)

  useEffect(() => { setNameVal(session.name || '') }, [session.name])

  const startRename = (e) => {
    e.stopPropagation()
    setRenaming(true)
    setTimeout(() => inputRef.current?.select(), 0)
  }

  const commitRename = () => {
    setRenaming(false)
    const trimmed = nameVal.trim()
    if (trimmed && trimmed !== session.name) onRename(trimmed)
    else setNameVal(session.name || '')
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    onDelete()
  }

  const displayName = session.name || 'New conversation'

  return (
    <div
      className={`ti-session-item${active ? ' ti-session-item-active' : ''}`}
      onClick={onClick}
      title={displayName}
    >
      {renaming ? (
        <input
          ref={inputRef}
          className="ti-session-rename-input"
          value={nameVal}
          onChange={(e) => setNameVal(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commitRename()
            if (e.key === 'Escape') { setRenaming(false); setNameVal(session.name || '') }
          }}
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="ti-session-name">{displayName}</span>
      )}
      <span className="ti-session-actions">
        <button className="ti-session-action-btn" title="Rename" onClick={startRename}>✎</button>
        <button className="ti-session-action-btn ti-session-delete-btn" title="Delete" onClick={handleDelete}>✕</button>
      </span>
    </div>
  )
}

// ---- RAG panel ----
// BUG 2 FIX: accepts sessionSources (per-session counts) alongside global status.
// Shows "In this session: N" / "Total indexed: N" for MITRE and NVD cards.
function RagPanel({ status, sessionSources }) {
  if (!status) {
    return (
      <div className="ti-rag-panel">
        <div className="ti-rag-title">Data Sources</div>
        <div className="ti-rag-loading">Loading…</div>
      </div>
    )
  }

  const { mitre, nvd, db_models, llm_online } = status

  const syncLabel = (iso) => {
    if (!iso) return 'Never synced'
    const d = new Date(iso)
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const total = (nvd?.cvss_distribution?.critical ?? 0) +
                (nvd?.cvss_distribution?.high ?? 0) +
                (nvd?.cvss_distribution?.medium ?? 0) +
                (nvd?.cvss_distribution?.low ?? 0)

  const pct = (n) => total > 0 ? Math.round((n / total) * 100) : 0

  const domainLabels = { 'enterprise-attack': 'Enterprise', 'mobile-attack': 'Mobile', 'ics-attack': 'ICS' }

  // Per-session counts (null when no session is active)
  const sessionMitre = sessionSources?.mitre ?? null
  const sessionNvd   = sessionSources?.nvd   ?? null

  return (
    <div className="ti-rag-panel">
      <div className="ti-rag-title">
        Data Sources
        {!llm_online && <span className="ti-llm-offline">LLM offline</span>}
      </div>

      {/* MITRE ATT&CK */}
      <div className="ti-rag-card">
        <div className="ti-rag-card-header">
          <span className={`ti-rag-dot ${mitre?.count > 0 ? 'ti-rag-dot-green' : 'ti-rag-dot-red'}`} />
          <span className="ti-rag-card-title">MITRE ATT&amp;CK</span>
        </div>
        {sessionMitre !== null && (
          <div className="ti-rag-session-row">
            <span className="ti-rag-session-label">In this session</span>
            <span className="ti-rag-session-count">{sessionMitre.count.toLocaleString()}</span>
          </div>
        )}
        <div className="ti-rag-session-row ti-rag-session-row-total">
          <span className="ti-rag-session-label">Total indexed</span>
          <span className="ti-rag-count">{(mitre?.count ?? 0).toLocaleString()}</span>
        </div>
        <div className="ti-rag-meta">{syncLabel(mitre?.last_sync)}</div>
        {mitre?.domains && Object.keys(mitre.domains).length > 0 && (
          <div className="ti-rag-domains">
            {Object.entries(mitre.domains).map(([d, c]) => (
              <span key={d} className="ti-rag-domain-pill">
                {domainLabels[d] || d}: {c.toLocaleString()}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* NVD CVEs */}
      <div className="ti-rag-card">
        <div className="ti-rag-card-header">
          <span className={`ti-rag-dot ${nvd?.count > 0 ? 'ti-rag-dot-green' : 'ti-rag-dot-red'}`} />
          <span className="ti-rag-card-title">NVD CVEs</span>
        </div>
        {sessionNvd !== null && (
          <div className="ti-rag-session-row">
            <span className="ti-rag-session-label">In this session</span>
            <span className="ti-rag-session-count">{sessionNvd.count.toLocaleString()}</span>
          </div>
        )}
        <div className="ti-rag-session-row ti-rag-session-row-total">
          <span className="ti-rag-session-label">Total indexed</span>
          <span className="ti-rag-count">{(nvd?.count ?? 0).toLocaleString()}</span>
        </div>
        <div className="ti-rag-meta">{syncLabel(nvd?.last_sync)}</div>
        {total > 0 && (
          <div className="ti-rag-cvss-bar" title={`Critical:${pct(nvd.cvss_distribution.critical)}% High:${pct(nvd.cvss_distribution.high)}% Med:${pct(nvd.cvss_distribution.medium)}%`}>
            <div className="ti-rag-cvss-seg ti-cvss-critical" style={{ width: `${pct(nvd.cvss_distribution.critical)}%` }} />
            <div className="ti-rag-cvss-seg ti-cvss-high"     style={{ width: `${pct(nvd.cvss_distribution.high)}%` }} />
            <div className="ti-rag-cvss-seg ti-cvss-medium"   style={{ width: `${pct(nvd.cvss_distribution.medium)}%` }} />
            <div className="ti-rag-cvss-seg ti-cvss-low"      style={{ width: `${pct(nvd.cvss_distribution.low)}%` }} />
          </div>
        )}
        {total > 0 && (
          <div className="ti-rag-cvss-legend">
            <span className="ti-cvss-label ti-cvss-label-critical">Crit {pct(nvd.cvss_distribution.critical)}%</span>
            <span className="ti-cvss-label ti-cvss-label-high">High {pct(nvd.cvss_distribution.high)}%</span>
            <span className="ti-cvss-label ti-cvss-label-medium">Med {pct(nvd.cvss_distribution.medium)}%</span>
          </div>
        )}
      </div>

      {/* Django DB models */}
      {db_models && db_models.length > 0 && (
        <div className="ti-rag-card">
          <div className="ti-rag-card-header">
            <span className="ti-rag-card-title">Django DB</span>
          </div>
          <div className="ti-rag-db-list">
            {db_models.map((m) => (
              <div key={m.name} className="ti-rag-db-row">
                <span className={`ti-rag-dot ${m.count > 0 ? 'ti-rag-dot-green' : 'ti-rag-dot-amber'}`} />
                <span className="ti-rag-db-name">{m.name}</span>
                <span className="ti-rag-db-count">{m.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ---- Main AssistantTab ----
// BUG 4: accepts preFill from parent (set when user clicks "Ask AI" in MITRE table)
function AssistantTab({ preFill = '', onClearPreFill }) {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [ragStatus, setRagStatus] = useState(null)
  const [ragOpen, setRagOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 768)
  // BUG 2 FIX: per-session source counts, updated whenever active session changes
  const [sessionSources, setSessionSources] = useState(null)
  const pollRef = useRef(null)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  // BUG 4: when parent sends a pre-fill question (from MITRE "Ask AI" button),
  // set it as the textarea value.
  useEffect(() => {
    if (preFill) {
      setInput(preFill)
      onClearPreFill?.()
      textareaRef.current?.focus()
    }
  }, [preFill, onClearPreFill])

  // Load sessions + RAG status on mount
  useEffect(() => {
    loadSessions()
    loadRagStatus()
    const ragInterval = setInterval(loadRagStatus, 5 * 60 * 1000)
    return () => clearInterval(ragInterval)
  }, [])

  // Load messages AND per-session sources when active session changes.
  // BUG 2 FIX: loadSessionSources is called here (not just on load) so counts
  // update correctly whenever the user switches sessions.
  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId)
      loadSessionSources(activeSessionId)
    } else {
      setMessages([])
      setSessionSources(null)
    }
  }, [activeSessionId])

  // Scroll to bottom on new messages / typing indicator
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [input])

  // Clean up any running poll on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const loadSessions = async () => {
    try {
      const { data } = await client.get('/chat/sessions/')
      setSessions(data)
    } catch (_) {}
  }

  const loadMessages = async (sessionId) => {
    try {
      const { data } = await client.get(`/chat/sessions/${sessionId}/messages/`)
      setMessages(data)
    } catch (_) {}
  }

  const loadRagStatus = async () => {
    try {
      const { data } = await client.get('/chat/rag-status/')
      setRagStatus(data)
    } catch (_) {}
  }

  // BUG 2 FIX: load per-session source citations from the new endpoint.
  const loadSessionSources = async (sessionId) => {
    try {
      const { data } = await client.get(`/chat/sessions/${sessionId}/sources/`)
      setSessionSources(data)
    } catch (_) {}
  }

  const createSession = async () => {
    try {
      const { data } = await client.post('/chat/sessions/')
      setSessions((prev) => [data, ...prev])
      setActiveSessionId(data.id)
      setMessages([])
      setError('')
    } catch (_) {
      setError('Failed to create session.')
    }
  }

  const renameSession = async (sessionId, newName) => {
    try {
      const { data } = await client.patch(`/chat/sessions/${sessionId}/`, { name: newName })
      setSessions((prev) => prev.map((s) => (s.id === sessionId ? { ...s, name: data.name } : s)))
    } catch (_) {}
  }

  const deleteSession = async (sessionId) => {
    try {
      await client.delete(`/chat/sessions/${sessionId}/`)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
        setMessages([])
      }
    } catch (_) {}
  }

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    // Auto-create session if none active
    let sessionId = activeSessionId
    if (!sessionId) {
      try {
        const { data } = await client.post('/chat/sessions/')
        setSessions((prev) => [data, ...prev])
        setActiveSessionId(data.id)
        sessionId = data.id
      } catch (_) {
        setError('Failed to create session.')
        return
      }
    }

    setInput('')
    setError('')
    const ts = new Date().toISOString()
    setMessages((prev) => [...prev, { role: 'user', content: text, created_at: ts }])
    setLoading(true)

    try {
      const { data } = await client.post('/chat/', { message: text, session_id: sessionId })
      const taskId = data.task_id

      // Update sidebar name if it was just set
      if (data.session_name) {
        setSessions((prev) =>
          prev.map((s) => (s.id === sessionId ? { ...s, name: data.session_name } : s))
        )
      }

      // Poll for task completion every 800ms
      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const { data: taskData } = await client.get(`/chat/tasks/${taskId}/`)
          if (taskData.status === 'complete') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setMessages((prev) => [
              ...prev,
              { role: 'assistant', content: taskData.reply, created_at: new Date().toISOString() },
            ])
            setLoading(false)
            // BUG 2 FIX: refresh per-session sources now that citations were stored
            loadSessionSources(sessionId)
          } else if (taskData.status === 'error') {
            clearInterval(pollRef.current)
            pollRef.current = null
            setError(taskData.error || 'The assistant encountered an error.')
            setLoading(false)
          }
          // status === "running" or "pending": keep polling
        } catch (_) {
          clearInterval(pollRef.current)
          pollRef.current = null
          setError('Lost connection while waiting for a response.')
          setLoading(false)
        }
      }, 800)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send message. Check that the LLM service is running.')
      setLoading(false)
    }
  }, [input, loading, activeSessionId])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const showSuggestions = activeSessionId && messages.length === 0

  return (
    <div className="ti-assistant-layout">
      {/* ---- Session Sidebar ---- */}
      <div className={`ti-session-sidebar${sidebarOpen ? '' : ' ti-session-sidebar-hidden'}`}>
        <div className="ti-session-sidebar-top">
          <button className="btn btn-primary btn-sm ti-new-chat-btn" onClick={createSession}>
            + New Chat
          </button>
          <button
            className="ti-sidebar-close-btn"
            title="Collapse sidebar"
            onClick={() => setSidebarOpen(false)}
          >
            ←
          </button>
        </div>
        <div className="ti-session-list" role="list">
          {sessions.length === 0 && (
            <p className="ti-session-empty">No sessions yet.</p>
          )}
          {sessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === activeSessionId}
              onClick={() => { setActiveSessionId(s.id); setError('') }}
              onRename={(name) => renameSession(s.id, name)}
              onDelete={() => deleteSession(s.id)}
            />
          ))}
        </div>
      </div>

      {/* ---- Chat Area ---- */}
      <div className="ti-chat-area">
        {/* Header row */}
        <div className="ti-chat-area-header">
          {!sidebarOpen && (
            <button
              className="ti-sidebar-open-btn"
              title="Open sessions"
              onClick={() => setSidebarOpen(true)}
            >
              ☰
            </button>
          )}
          <span className="ti-chat-session-label">
            {activeSession
              ? (activeSession.name || 'New conversation')
              : 'Select or create a session'}
          </span>
          <button
            className={`ti-rag-toggle-btn${ragOpen ? ' ti-rag-toggle-active' : ''}`}
            title={ragOpen ? 'Hide data sources' : 'Show data sources'}
            onClick={() => setRagOpen((o) => !o)}
          >
            {ragStatus && !ragStatus.llm_online
              ? <span className="ti-llm-offline-dot" title="LLM offline">⚠ LLM offline</span>
              : '⊙ Sources'}
          </button>
        </div>

        {/* Messages */}
        <div className="ti-chat-body" role="log" aria-live="polite">
          {!activeSessionId ? (
            <div className="chat-empty">
              <div className="chat-empty-icon">⊙</div>
              <p>Create a new session or select one from the sidebar to start chatting.</p>
              <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={createSession}>
                + New Chat
              </button>
            </div>
          ) : showSuggestions ? (
            <div className="chat-empty">
              <div className="chat-empty-icon">⊙</div>
              <p>Ask about CVEs, MITRE ATT&amp;CK techniques, or your logged operations.</p>
              <div className="chat-suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chat-suggestion" onClick={() => setInput(s)}>{s}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
              {loading && (
                <div className="chat-bubble chat-bubble-assistant">
                  <div className="chat-bubble-label">⊙ OVERWATCH</div>
                  <div className="chat-thinking"><span /><span /><span /></div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {error && <div className="alert alert-error chat-alert">{error}</div>}

        {/* Input bar — only shown when a session is active */}
        {activeSessionId && (
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
        )}
      </div>

      {/* ---- RAG Panel ---- */}
      {ragOpen && <RagPanel status={ragStatus} sessionSources={sessionSources} />}
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
  // BUG 4: when user clicks "Ask AI" on a MITRE technique, pre-fill the chat
  // input and switch to the assistant tab.  Lifted here so MitreTab can trigger
  // it without needing direct access to AssistantTab's state.
  const [assistantPreFill, setAssistantPreFill] = useState('')

  const handleAskAI = (technique) => {
    setAssistantPreFill(
      `Explain the MITRE ATT\u0026CK technique ${technique.external_id} (${technique.name}) — ` +
      `what does it do, how is it detected, and what mitigations exist?`
    )
    setActiveTab('assistant')
  }

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
        {activeTab === 'mitre' && <MitreTab onAskAI={handleAskAI} />}
        {activeTab === 'cves'  && <CveTab />}
        {activeTab === 'assistant' && (
          <AssistantTab
            preFill={assistantPreFill}
            onClearPreFill={() => setAssistantPreFill('')}
          />
        )}
      </div>
    </div>
  )
}
