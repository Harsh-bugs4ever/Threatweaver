import { useEffect, useMemo, useRef, useState } from 'react'
import { Background, Controls, Handle, Position, ReactFlow, type Edge, type Node } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Activity, ArrowRight, Check, ChevronRight, CircleHelp, Database, ExternalLink,
  FileText, GitBranch, Globe2, Info, Layers3, LoaderCircle, Radar, Search, ShieldAlert,
  ShieldCheck, Sparkles, Waypoints, X, Download, SlidersHorizontal, CheckCheck, ArrowUpRight, Home, BookOpen } from 'lucide-react'

type Evidence = {
  id: string; predicate: string; object: string; source_time: string; fetched_at: string;
  evidence_id: string; source_id: string; source_url: string; neighbor_key: string | null
}
type GraphData = {
  nodes: { id: string; kind: string; label: string }[];
  edges: { id: string; source: string; target: string; kind: string; predicate: string; observation_id: string }[];
  paths: { nodes: string[]; observation_ids: string[]; type: string }[];
  depth: number; limit: number; truncated: boolean
}
type Result = {
  report: { indicator: string; status: string; data_freshness: string; observations: string[]; inferences: string[];
    unknowns: string[]; recommended_actions: string[]; confidence: string;
    observation_refs: { observation_id: string; evidence_id: string; source_id: string }[];
    evidence_count: number; warnings: string[]; generated_at: string };
  findings: { pulse_count?: number | null; pulse_names?: string[]; dns_count?: number;
    live_dns_count?: number; fetched_at?: string; live_dns_fetched_at?: string };
  pivot: { indicator: string; reason: string; lookup_status: string; error?: string } | null;
  graph: GraphData; evidence: Evidence[]; method: string;
  agent: { status: string; message: string; audit: { tool: string; status: string }[] }
}
type Health = { service: string; graph: string; otx_configured: boolean; llm_configured: boolean }
type HistoryItem = { id: string; indicator: string; created_at: string; status: string; method: string }

function IndicatorNode({ data }: { data: { label: string; kind: string; root: boolean } }) {
  return <div className={`indicator-node ${data.root ? 'root-node' : ''}`}>
    <Handle type="target" position={Position.Left} /><Handle type="source" position={Position.Right} />
    <span className="node-icon">{data.kind === 'domain' ? <Globe2 size={17} /> : <Database size={17} />}</span>
    <span className="node-copy"><strong>{data.label}</strong><small>{data.kind === 'domain' ? 'DOMAIN' : 'IP ADDRESS'}</small></span>
  </div>
}

const nodeTypes = { indicator: IndicatorNode }

function formatTime(value?: string) {
  if (!value) return 'Unknown'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export default function App() {
  const [input, setInput] = useState('')
  const [expand, setExpand] = useState(true)
  const [useAgent, setUseAgent] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'evidence'>('overview')
  const [evidenceQuery, setEvidenceQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [completedActions, setCompletedActions] = useState<string[]>([])
  const [storageWarning, setStorageWarning] = useState('')
  const drawerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!selectedEvidence) return
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const drawer = drawerRef.current
    drawer?.querySelector<HTMLButtonElement>('button')?.focus()
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setSelectedEvidence(null)
      if (event.key !== 'Tab' || !drawer) return
      const controls = drawer.querySelectorAll<HTMLElement>('button, a[href]')
      const first = controls[0], last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = previousOverflow
      previousFocus?.focus()
    }
  }, [selectedEvidence])

  useEffect(() => {
    setEvidenceQuery(''); setSourceFilter('all')
    setCompletedActions([]); setStorageWarning('')
    if (!result) return
    try {
      const saved: unknown = JSON.parse(localStorage.getItem(`threatweaver:actions:${result.report.indicator}`) ?? '[]')
      if (Array.isArray(saved)) setCompletedActions(saved.filter((item): item is string => typeof item === 'string'))
    } catch { setStorageWarning('Checklist storage is unavailable in this browser.') }
  }, [result])

  function toggleAction(action: string) {
    if (!result) return
    const next = completedActions.includes(action) ? completedActions.filter(item => item !== action) : [...completedActions, action]
    setCompletedActions(next)
    try { localStorage.setItem(`threatweaver:actions:${result.report.indicator}`, JSON.stringify(next)) }
    catch { setStorageWarning('Changes apply for this session only; browser storage is unavailable.') }
  }

  function downloadReport(format: 'json' | 'md') {
    if (!result) return
    const report = result.report
    const sections = [['Source observations', report.observations], ['Inferences', report.inferences],
      ['Unknowns', report.unknowns], ['Recommended actions', report.recommended_actions], ['Source warnings', report.warnings]] as const
    const markdown = `# ThreatWeaver: ${report.indicator}\n\nGenerated: ${report.generated_at}\nStatus: ${report.status}\nConfidence: ${report.confidence}\nFreshness: ${report.data_freshness}\n\n` +
      sections.map(([title, items]) => `## ${title}\n\n${items.map(item => `- ${item}`).join('\n') || 'None reported.'}\n`).join('\n') +
      `\n## Evidence\n\n${result.evidence.map(item => `- ${item.object} (${item.predicate})\n  Source: ${item.source_id}\n  URL: ${item.source_url}\n  Observation: ${item.id}\n  Evidence: ${item.evidence_id}\n  Source time: ${item.source_time}\n  Fetched: ${item.fetched_at}`).join('\n')}\n\nOTX associations and graph proximity do not establish compromise. Validate against internal telemetry before acting.\n`
    const url = URL.createObjectURL(new Blob([format === 'json' ? JSON.stringify(result, null, 2) : markdown], { type: format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url; link.download = `threatweaver-${report.indicator.replace(/[^a-zA-Z0-9.-]/g, '-')}.${format}`
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const filteredEvidence = result?.evidence.filter(item =>
    (sourceFilter === 'all' || item.source_id === sourceFilter) &&
    `${item.object} ${item.predicate} ${item.source_id} ${item.id}`.toLowerCase().includes(evidenceQuery.toLowerCase())) ?? []
  const actionCount = result?.report.recommended_actions.filter(action => completedActions.includes(action)).length ?? 0

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => setHealth(null))
    refreshHistory()
  }, [])

  function refreshHistory() {
    fetch('/api/investigations?limit=8').then(r => r.ok ? r.json() : null)
      .then(data => setHistory(data?.items ?? [])).catch(() => setHistory([]))
  }

  async function openHistory(id: string) {
    setError(''); setLoading(true); setSelectedEvidence(null)
    try {
      const response = await fetch(`/api/investigations/${id}`)
      if (!response.ok) throw new Error('Saved investigation could not be loaded.')
      const payload = await response.json() as Result
      setResult(payload); setInput(payload.report.indicator.split(':').slice(1).join(':')); setActiveTab('overview')
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'History unavailable.') }
    finally { setLoading(false) }
  }

  async function runInvestigation(event: React.FormEvent) {
    event.preventDefault()
    if (!input.trim()) return
    setLoading(true); setError(''); setResult(null); setSelectedEvidence(null)
    try {
      const response = await fetch('/api/investigations', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ indicator: input.trim(), expand, use_agent: useAgent }),
      })
      const payload = await response.json()
      if (!response.ok) {
        const detail = payload.detail
        throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail)
          ? detail.map(item => item.msg ?? 'Invalid input').join('; ')
          : 'Investigation failed. Enter a domain or public IPv4 address.')
      }
      setResult(payload as Result)
      setActiveTab('overview')
      refreshHistory()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The investigation could not be completed.')
    } finally { setLoading(false) }
  }

  const flow = useMemo(() => {
    if (!result) return { nodes: [] as Node[], edges: [] as Edge[] }
    const root = result.report.indicator
    const others = result.graph.nodes.filter(node => node.id !== root)
    const nodes: Node[] = [
      { id: root, type: 'indicator', position: { x: 250, y: 190 },
        data: { label: root.split(':').slice(1).join(':'), kind: root.split(':')[0], root: true } },
      ...others.map((node, index) => {
        const angle = (index / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2
        const radius = others.length > 6 ? 250 : 205
        return { id: node.id, type: 'indicator',
          position: { x: 250 + Math.cos(angle) * radius, y: 190 + Math.sin(angle) * radius },
          data: { label: node.label, kind: node.kind, root: false } }
      }),
    ]
    const edges: Edge[] = result.graph.edges.map(edge => ({
      id: edge.id, source: edge.source, target: edge.target,
      style: { stroke: '#15b8a6', strokeWidth: 2 },
      label: edge.predicate === 'current_dns_a' ? 'current DNS' : 'OTX passive DNS',
      labelStyle: { fill: '#8fa6b3', fontSize: 10 },
      labelBgStyle: { fill: '#0c1822' },
    }))
    return { nodes, edges }
  }, [result])

  async function inspectEdge(edgeId: string) {
    const cached = result?.evidence.find(e => e.id === edgeId)
    if (cached) { setSelectedEvidence(cached); return }
    try {
      const response = await fetch(`/api/observations/${edgeId}`)
      if (!response.ok) throw new Error('This graph observation could not be loaded.')
      setSelectedEvidence(await response.json() as Evidence)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Evidence unavailable.') }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Waypoints size={24} strokeWidth={2.4} /></div>
        <div><strong>ThreatWeaver</strong><span>INVESTIGATION WORKBENCH</span></div></div>
      <div className="sidebar-divider" />
      <div className="nav-label">WORKSPACE</div>
      <div className="nav-item active"><Radar size={18} /> Investigation <span className="nav-accent" /></div>
      <nav className="workbench-links" aria-label="Website navigation"><a href="/"><Home size={13} /> Overview</a><a href="/docs"><BookOpen size={13} /> Docs</a></nav>
      <div className="sidebar-section">
        <div className="nav-label">INVESTIGATION SCOPE</div>
        <div className="scope-item"><Globe2 size={16} /> Domains</div>
        <div className="scope-item"><Database size={16} /> Public IPv4</div>
        <div className="scope-item"><GitBranch size={16} /> 2-hop graph paths</div>
      </div>
      {history.length > 0 && <div className="sidebar-section history-section"><div className="nav-label">RECENT INVESTIGATIONS</div>
        {history.map(item => <button className="history-item" key={item.id} disabled={loading} onClick={() => openHistory(item.id)} title={`${item.indicator} · ${formatTime(item.created_at)}`}><FileText size={14} /><span>{item.indicator.split(':').slice(1).join(':')}</span><ChevronRight size={13} /></button>)}</div>}
      <div className="sidebar-bottom">
        <div className="system-card">
          <div className="system-head"><Activity size={16} /> System status</div>
          <div><span className={`status-dot ${health?.graph === 'ready' ? 'good' : 'bad'}`} /> FalkorDB <strong>{health?.graph ?? 'Unknown'}</strong></div>
          <div><span className={`status-dot ${health?.otx_configured ? 'good' : 'bad'}`} /> OTX key <strong>{health?.otx_configured ? 'Set' : 'Missing'}</strong></div>
        </div>
        <div className="sidebar-foot">Evidence first. Conclusions with context.</div>
      </div>
    </aside>

    <main className="main-content">
      <header className="topbar"><div className="breadcrumb"><a href="/">OVERVIEW</a> <ChevronRight size={14} /> <span>INVESTIGATION</span></div>
        <div className="topbar-right"><span className="live-badge"><span /> LOCAL WORKBENCH</span><a href="https://otx.alienvault.com/" target="_blank" rel="noreferrer" aria-label="Open OTX intelligence resources"><CircleHelp size={17} /></a></div></header>
      <div className="content-wrap">
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> THREAT INTELLIGENCE / GRAPH TRIAGE</div>
          <h1>Every connection tells a story<span>.</span></h1><p>Turn scattered signals into a clearer picture. Investigate, connect, and follow the evidence.</p></div>
          <div className="heading-graphic"><ShieldCheck size={40} /></div></div>

        <section className="search-panel">
          <div className="search-panel-head"><div className="panel-kicker"><Search size={16} /> START AN INVESTIGATION</div><span className="supported-badge">DOMAIN / IPv4</span></div>
          <form onSubmit={runInvestigation} className="search-form"><div className="input-wrap"><Globe2 size={19} />
            <input value={input} onChange={e => setInput(e.target.value)} placeholder="Enter a domain or public IPv4 address" aria-label="Indicator" />
            {input && <button type="button" className="clear-button" onClick={() => setInput('')} aria-label="Clear"><X size={16} /></button>}</div>
            <button className="primary-button" disabled={loading || !input.trim()}>{loading ? <LoaderCircle className="spin" size={18} /> : <Radar size={18} />}{loading ? 'Investigating' : 'Investigate'}<ArrowRight size={16} /></button></form>
          <div className="search-meta"><span><Info size={14} /> Example: example.com or 8.8.8.8. Omit https:// and paths.</span><label className="toggle-line"><input type="checkbox" checked={expand} onChange={e => setExpand(e.target.checked)} /><span className="switch" /> Follow one graph selected pivot</label>
            <label className="toggle-line"><input type="checkbox" checked={useAgent} onChange={e => setUseAgent(e.target.checked)} /><span className="switch" /> DeepSeek tool planner</label>
            <span><Info size={14} /> Live OTX lookup. No automated blocking.</span></div>
        </section>

        {error && <div className="error-banner" role="alert"><ShieldAlert size={20} /><div><strong>Investigation could not run</strong><span>{error}</span></div></div>}

        {!result && !loading && <div className="empty-state"><div className="empty-icon"><Layers3 size={32} /></div><h2>See the story behind an indicator</h2>
          <p>Enter a domain or public IP to collect OTX context, persist sourced observations in FalkorDB, and inspect related indicators.</p>
          <div className="example-buttons"><span>TRY AN INDICATOR</span>{['example.com', '8.8.8.8', '1.1.1.1'].map(value => <button key={value} onClick={() => setInput(value)}>{value}<ArrowUpRight size={13} /></button>)}</div>
          <div className="empty-steps"><span><b>01</b> LOOK UP</span><ChevronRight size={15} /><span><b>02</b> LINK EVIDENCE</span><ChevronRight size={15} /><span><b>03</b> TRIAGE</span></div></div>}

        {!result && !loading && <div className="capabilities"><article><span className="feature-icon"><Globe2 size={20} /></span><h3>Start with a signal</h3><p>Bring a domain or public IP. Gather live OTX context and current DNS observations.</p><small>01 / DISCOVER</small></article><article><span className="feature-icon"><GitBranch size={20} /></span><h3>Connect the evidence</h3><p>Explore sourced relationships across two graph hops, with provenance at every step.</p><small>02 / INVESTIGATE</small></article><article><span className="feature-icon"><CheckCheck size={20} /></span><h3>Make your next move</h3><p>Track recommended actions and export a source-backed report for your investigation.</p><small>03 / TAKE ACTION</small></article></div>}

        {loading && <div className="loading-state" role="status"><LoaderCircle className="spin" size={30} /><strong>Tracing the evidence</strong><span>Fetching OTX context and following bounded graph links…</span></div>}

        {result && <div className="results">
          <div className="result-header"><div><div className="eyebrow">INVESTIGATION RESULT <span className="small-separator">/</span> {result.report.status.toUpperCase()}</div>
            <h2>{result.report.indicator.split(':').slice(1).join(':')}</h2><div className="result-sub"><span>{result.report.indicator.split(':')[0].toUpperCase()}</span><span>Updated {formatTime(result.report.generated_at)}</span></div></div>
            <div className="result-tools"><span className={`result-status ${result.report.status}`}><span /> {result.report.status === 'complete' ? 'Analysis complete' : 'Partial analysis'}</span><div className="export-buttons"><button onClick={() => downloadReport('md')}><Download size={14} /> Report .md</button><button onClick={() => downloadReport('json')}><Download size={14} /> JSON</button></div></div></div>
          {result.report.warnings.length > 0 && <div className="warning-banner"><ShieldAlert size={18} /><div>{result.report.warnings.map((warning, index) => <p key={index}>{warning}</p>)}</div></div>}
          {useAgent && <div className="agent-banner"><Sparkles size={16} /><span>DeepSeek planner: {result.agent.status.replaceAll('_', ' ')} · {result.agent.audit.length} audited call(s). {result.agent.status === 'not_configured' ? result.agent.message : ''}</span></div>}
          <div className="stats-row"><div className="stat-card"><span>OTX PULSES</span><strong>{result.findings.pulse_count ?? '—'}</strong><small>{result.findings.pulse_count == null ? 'No verified count' : 'Source observation'}</small></div>
            <div className="stat-card"><span>GRAPH LINKS</span><strong>{result.graph.edges.length}</strong><small>Current DNS + OTX history</small></div>
            <div className="stat-card"><span>EVIDENCE ITEMS</span><strong>{result.report.evidence_count}</strong><small>Stored for this indicator</small></div>
            <div className="stat-card"><span>GRAPH PIVOT</span><strong className="stat-text">{result.pivot ? 'Selected' : 'None'}</strong><small>{result.pivot ? result.pivot.indicator : 'No observed neighbor'}</small></div></div>
          <div className="section-tabs"><button className={activeTab === 'overview' ? 'selected' : ''} onClick={() => setActiveTab('overview')}><Activity size={16} /> Overview</button>
            <button className={activeTab === 'evidence' ? 'selected' : ''} onClick={() => setActiveTab('evidence')}><FileText size={16} /> Evidence <span>{result.evidence.length}</span></button></div>

          {activeTab === 'overview' ? <div className="result-grid">
            <section className="card graph-card"><div className="card-heading"><div><div className="panel-kicker"><GitBranch size={16} /> RELATIONSHIP GRAPH</div><p>{result.report.data_freshness === 'current_external_fetch' ? 'Current DNS and OTX links · inspect each source timestamp' : 'Stored links · current sources unavailable'} · max 2 hops</p></div><a className="card-tag graph-browser-link" href="http://localhost:3000" target="_blank" rel="noreferrer" title="Open FalkorDB Browser and select the threatweaver graph">OPEN IN FALKORDB <ExternalLink size={12} /></a></div>
              <div className="graph-canvas"><ReactFlow nodes={flow.nodes} edges={flow.edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.25 }} onEdgeClick={(_, edge) => inspectEdge(edge.id)} nodesDraggable={false} nodesConnectable={false}><Background color="#203444" gap={24} size={1} /><Controls showInteractive={false} /></ReactFlow></div>
              <div className="graph-foot"><span><i className="legend-dot" /> Sourced link</span><span>{result.graph.edges.length} link(s) shown{result.graph.truncated ? ' · limit reached' : ''}</span></div></section>
            <div className="right-stack"><section className="card actions-card"><div className="panel-kicker"><ShieldCheck size={16} /> RECOMMENDED NEXT STEPS</div>
              <div className="action-progress"><span>{actionCount} of {result.report.recommended_actions.length} complete</span><small>Saved in this browser</small></div><progress value={actionCount} max={result.report.recommended_actions.length || 1} aria-label="Recommended actions completed" />
              {storageWarning && <p className="storage-warning" role="status">{storageWarning}</p>}
              {result.report.recommended_actions.map((action, index) => <label className={`action-row ${completedActions.includes(action) ? 'done' : ''}`} key={index}><input type="checkbox" checked={completedActions.includes(action)} onChange={() => toggleAction(action)} /><p>{action}</p></label>)}</section>
              <section className="card pivot-card"><div className="panel-kicker"><Waypoints size={16} /> GRAPH SELECTED PIVOT</div>{result.pivot ? <><strong>{result.pivot.indicator}</strong><p>{result.pivot.reason}</p><span className="pivot-status"><span className={result.pivot.lookup_status === 'complete' ? 'good' : 'bad'} /> Lookup {result.pivot.lookup_status.replace('_', ' ')}</span></> : <p>No observed neighbor was available to inspect.</p>}</section></div>
            <section className="card narrative-card"><div className="panel-kicker"><Check size={16} /> SOURCE OBSERVATIONS</div>{result.report.observations.map((item, i) => <p key={i}>{item}</p>)}
              {result.report.observation_refs.length > 0 && <button className="inline-link" onClick={() => setActiveTab('evidence')}>View {result.report.observation_refs.length} source reference(s) in evidence ledger <ArrowRight size={13} /></button>}
              {result.findings.pulse_names && result.findings.pulse_names.length > 0 && <div className="pulse-list"><small>OTX PULSE NAMES</small>{result.findings.pulse_names.map((name, i) => <span key={i}>{name}</span>)}</div>}</section>
            <section className="card narrative-card"><div className="panel-kicker"><Sparkles size={16} /> INFERENCE & UNKNOWNS</div>{result.report.inferences.map((item, i) => <p key={i}>{item}</p>)}
              {result.report.unknowns.map((item, i) => <p className="unknown" key={i}>{item}</p>)}</section>
          </div> : <section className="card evidence-card"><div className="card-heading"><div><div className="panel-kicker"><FileText size={16} /> EVIDENCE LEDGER</div><p>Source IDs and timestamps for stored observations</p></div></div>
            <div className="evidence-toolbar"><div className="input-wrap"><Search size={16} /><input aria-label="Search evidence" placeholder="Search indicator, observation, or source…" value={evidenceQuery} onChange={event => setEvidenceQuery(event.target.value)} /></div><label><SlidersHorizontal size={15} /><select aria-label="Filter evidence by source" value={sourceFilter} onChange={event => setSourceFilter(event.target.value)}><option value="all">All sources</option>{[...new Set(result.evidence.map(item => item.source_id))].map(source => <option key={source} value={source}>{source}</option>)}</select></label><span role="status">{filteredEvidence.length} of {result.evidence.length} items</span></div>
            {filteredEvidence.length ? filteredEvidence.map(item => <button className="evidence-row" key={item.id} onClick={() => setSelectedEvidence(item)}><span className="evidence-type">{item.predicate.replaceAll('_', ' ')}</span><strong>{item.object}</strong><small>{item.source_id}</small><ChevronRight size={16} /></button>) : <div className="no-evidence">{result.evidence.length ? 'No evidence matches your filters.' : 'No verified evidence has been stored for this indicator.'}</div>}</section>}
          <div className="result-disclaimer"><Info size={15} /> OTX associations and graph proximity do not establish compromise. Validate against internal telemetry before acting.</div>
        </div>}
      </div>
    </main>

    {selectedEvidence && <div className="drawer-backdrop" onClick={() => setSelectedEvidence(null)}><aside ref={drawerRef} className="evidence-drawer" role="dialog" aria-modal="true" aria-labelledby="evidence-title" onClick={e => e.stopPropagation()}><div className="drawer-head"><div><small>EVIDENCE INSPECTOR</small><h3 id="evidence-title">Source observation</h3></div><button onClick={() => setSelectedEvidence(null)} aria-label="Close"><X size={20} /></button></div>
      <div className="drawer-body"><div className="drawer-label">OBSERVATION</div><div className="drawer-value strong">{selectedEvidence.predicate.replaceAll('_', ' ')}</div><div className="drawer-value">{selectedEvidence.object}</div>
        <div className="drawer-label">SOURCE ID</div><div className="drawer-value mono">{selectedEvidence.source_id}</div>
        <div className="drawer-label">OBSERVATION ID</div><div className="drawer-value mono">{selectedEvidence.id}</div>
        <div className="drawer-label">EVIDENCE ID</div><div className="drawer-value mono">{selectedEvidence.evidence_id}</div>
        <div className="drawer-label">SOURCE TIMESTAMP</div><div className="drawer-value">{formatTime(selectedEvidence.source_time)}</div>
        <div className="drawer-label">LAST FETCHED</div><div className="drawer-value">{formatTime(selectedEvidence.fetched_at)}</div>
        {selectedEvidence.neighbor_key && <><div className="drawer-label">LINKED INDICATOR</div><div className="drawer-value mono">{selectedEvidence.neighbor_key}</div></>}
        <a className="source-link" href={selectedEvidence.source_url} target="_blank" rel="noreferrer">View source record <ExternalLink size={15} /></a></div>
    </aside></div>}
  </div>
}
