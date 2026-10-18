import { isValidElement, useEffect, useState, type ReactNode } from 'react'
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Check, CheckCheck, ChevronRight,
  Code2, Download, ExternalLink, FileText, GitBranch, Globe2, Info, Layers3,
  Radar, Search, ShieldCheck, Waypoints, X } from 'lucide-react'
import Workbench from './App'
import './site.css'

function Brand() {
  return <a href="/" className="site-brand" aria-label="ThreatWeaver home"><span><Waypoints size={23} /></span>ThreatWeaver<small> / INTELLIGENCE IN CONTEXT</small></a>
}

function Header({ page }: { page: 'home' | 'docs' }) {
  return <header className="site-header"><div className="site-header-inner"><Brand /><nav aria-label="Main navigation">
    <a href="/" aria-current={page === 'home' ? 'page' : undefined}>Overview</a>
    <a href="/docs" aria-current={page === 'docs' ? 'page' : undefined}>Documentation</a>
    <a href="/investigate" className="site-button small">Open workbench <ArrowUpRight size={15} /></a>
  </nav></div></header>
}

function Footer() {
  return <footer className="site-footer"><Brand /><p>Evidence first. Conclusions with context.</p><a href="/docs#limits">Understand the limits <ArrowUpRight size={13} /></a></footer>
}

const diagramInfo = {
  'system-flow': { title: 'The investigation pipeline', alt: 'System flow: React sends an indicator to FastAPI, which writes and reads FalkorDB and requests OTX, Google DNS, and optional DeepSeek context.' },
  'evidence-model': { title: 'A graph built around provenance', alt: 'Evidence model: Indicator has Observation, Observation is supported by Evidence and points to a related Indicator. Indicator also has Investigation history and a direct observed link to the related indicator.' },
  'two-hop-paths': { title: 'Reading a two-hop path', alt: 'Illustrative two-hop path: starting domain points to a shared IP, and a related domain also points to that IP. Traverse these two associations in either direction.' },
}

function Diagram({ name }: { name: keyof typeof diagramInfo }) {
  const item = diagramInfo[name]
  return <figure className="docs-diagram" tabIndex={0} aria-label={item.title}><div className="diagram-top"><span><Waypoints size={15} /> EXCALIDRAW / EDITABLE SCENE</span><a href={`/diagrams/${name}.svg`} target="_blank" rel="noreferrer">View full size <ExternalLink size={13} /></a></div>
    <img src={`/diagrams/${name}.svg`} alt={item.alt} width="1160" height="650" loading="lazy" />
    <figcaption><span>{item.title}</span><a href={`/diagrams/${name}.excalidraw`} download><Download size={14} /> Download Excalidraw</a></figcaption>
  </figure>
}

function Home() {
  return <div className="public-site"><a href="#main" className="skip-link">Skip to content</a><Header page="home" /><main id="main" tabIndex={-1}>
    <section className="landing-hero site-container"><div className="hero-copy"><div className="site-eyebrow"><span /> AN EVIDENCE-FIRST INVESTIGATION WORKBENCH</div>
      <h1>Follow the signal.<br />Understand the <em>connection.</em></h1>
      <p className="hero-description">A domain is a starting point. ThreatWeaver brings threat intelligence, DNS observations, and graph relationships into one place—so you can see the evidence behind your next decision.</p>
      <div className="hero-buttons"><a className="site-button" href="/investigate">Start an investigation <ArrowRight size={17} /></a><a className="site-button secondary" href="/docs">Explore the docs <BookOpen size={17} /></a></div>
      <div className="hero-details"><span><Check size={13} /> Domains & public IPv4</span><span><Check size={13} /> Source-backed findings</span><span><Check size={13} /> Local graph storage</span></div>
    </div><div className="hero-visual" aria-label="Illustrative investigation graph; not live results"><div className="visual-toolbar"><span><span className="tiny-dot" /> RELATIONSHIP EXPLORER</span><span>ILLUSTRATIVE</span></div>
      <div className="hero-network"><svg viewBox="0 0 520 360" role="img" aria-label="Example domain connected to current DNS, passive DNS history, and source evidence"><defs><pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#514367" /></pattern></defs><rect width="520" height="360" fill="url(#grid)" /><path d="M260 175 L115 75 M260 175 L410 80 M260 175 L105 275 M260 175 L410 280" fill="none" stroke="#8c73b7" strokeWidth="1.5" strokeDasharray="5 5" />
        <g fill="#1c192b" stroke="#64507e"><rect x="25" y="39" width="172" height="65" rx="10" /><rect x="335" y="44" width="166" height="65" rx="10" /><rect x="17" y="252" width="180" height="65" rx="10" /><rect x="335" y="252" width="166" height="65" rx="10" /></g>
        <g fontFamily="Arial, sans-serif" fill="#ece4fa" fontSize="13"><text x="43" y="65">Current DNS</text><text x="352" y="70">Source records</text><text x="35" y="278">Passive DNS</text><text x="352" y="278">Related indicators</text></g>
        <g fontFamily="Arial, sans-serif" fill="#a79ab9" fontSize="10"><text x="43" y="85">LIVE A RECORDS</text><text x="352" y="90">URL + TIMESTAMPS</text><text x="35" y="298">HISTORICAL LINKS</text><text x="352" y="298">BOUNDED GRAPH PATHS</text></g>
        <rect x="166" y="139" width="190" height="78" rx="13" fill="#362647" stroke="#bc99f5" strokeWidth="1.5" /><text x="188" y="170" fill="#f0e3ff" fontFamily="Arial, sans-serif" fontSize="17">example.com</text><text x="188" y="193" fill="#c4a4ea" fontFamily="Arial, sans-serif" fontSize="10">STARTING INDICATOR</text>
      </svg></div><div className="visual-evidence"><ShieldCheck size={20} /><div><strong>Every connection needs context.</strong><span>Inspect the source. Check its timestamp.</span></div><Check size={16} /></div></div></section>

    <div className="source-strip"><div className="site-container"><span>BUILT AROUND REAL SOURCES</span><strong>AlienVault OTX</strong><i /> <strong>Google Public DNS</strong><i /><strong>FalkorDB</strong><i /><strong>DeepSeek <small>OPTIONAL</small></strong></div></div>

    <section className="site-container landing-section" id="workflow"><div className="section-intro"><div><div className="site-eyebrow">01 / THE WORKFLOW</div><h2>From an unfamiliar indicator<br />to a useful next step.</h2></div><p>Keep observations, interpretations, and unanswered questions separate. Follow the trail without losing the source.</p></div>
      <div className="workflow-cards">{[
        { icon: Globe2, number: '01', title: 'Bring one signal', copy: 'Start with a bare domain or public IPv4 address. Collect OTX pulse context, passive DNS history, and current domain A records.' },
        { icon: GitBranch, number: '02', title: 'Trace its relationships', copy: 'Explore up to two hops of stored, sourced graph links. Optionally enrich one currently observed neighbor through OTX.' },
        { icon: CheckCheck, number: '03', title: 'Decide what comes next', copy: 'Inspect sources, review unknowns, track recommended actions, and export the investigation as Markdown or JSON.' },
      ].map(item => <article key={item.number}><div className="workflow-card-top"><item.icon size={23} /><span>{item.number}</span></div><h3>{item.title}</h3><p>{item.copy}</p></article>)}</div>
    </section>

    <section className="site-container landing-story"><div className="story-copy"><div className="site-eyebrow">02 / THE EVIDENCE TRAIL</div><h2>A finding is only as useful<br />as the evidence behind it.</h2><p>Move from a graph connection to its observation, original source URL, and collection time. Current DNS and historical passive DNS remain distinct, so yesterday’s association doesn’t become today’s assumption.</p><ul><li><Check size={16} /> Trace findings to source records</li><li><Check size={16} /> Reopen saved investigation snapshots</li><li><Check size={16} /> See partial results and source warnings</li></ul><a className="text-link" href="/docs#evidence">Understand the evidence model <ArrowRight size={15} /></a></div>
      <div className="evidence-example"><div className="example-caption"><FileText size={16} /> EXAMPLE OBSERVATION <span>ILLUSTRATIVE</span></div><div className="example-predicate">current_dns_a</div><h3>Domain → public IP</h3><dl><div><dt>SOURCE</dt><dd>Google Public DNS</dd></div><div><dt>PROVENANCE</dt><dd>Source URL + observation ID</dd></div><div><dt>TIME CONTEXT</dt><dd>Source time + last fetched</dd></div></dl><div className="example-note"><Info size={16} /> A DNS association is a lead, not a verdict.</div></div>
    </section>

    <section className="site-container landing-section"><div className="section-intro"><div><div className="site-eyebrow">03 / UNDER THE HOOD</div><h2>One connected workflow.<br />A visible chain of evidence.</h2></div><a className="text-link" href="/docs#architecture">Read the architecture guide <ArrowRight size={15} /></a></div><Diagram name="system-flow" /></section>

    <section className="site-container landing-boundaries"><ShieldCheck size={30} /><div><h2>Built for investigation. Guided by uncertainty.</h2><p>Shared hosting does not prove shared ownership. OTX mentions do not establish compromise. ThreatWeaver recommends next steps; validate findings against your own telemetry before acting.</p></div><a href="/docs#limits">Read the limits <ArrowUpRight size={15} /></a></section>

    <section className="site-container landing-cta"><div className="site-eyebrow">YOUR NEXT INVESTIGATION STARTS HERE</div><h2>Give the signal some context.</h2><p>Start with a domain or public IP. Follow the evidence from there.</p><a className="site-button" href="/investigate">Open the workbench <ArrowRight size={17} /></a><a className="cta-secondary" href="/docs#quickstart">New here? Read the quick start <ArrowDown size={13} /></a></section>
  </main><Footer /></div>
}

function Callout({ children }: { children: ReactNode }) {
  return <div className="docs-callout"><Info size={18} /><div>{children}</div></div>
}

function CodeBlock({ children }: { children: string }) {
  const [status, setStatus] = useState('Copy')
  async function copy() {
    try { await navigator.clipboard.writeText(children); setStatus('Copied') }
    catch { setStatus('Select text to copy') }
  }
  return <div className="docs-code"><button onClick={copy} aria-label="Copy code snippet">{status}</button><pre><code>{children}</code></pre></div>
}

const sections: { id: string; title: string; keywords: string; content: ReactNode }[] = [
  { id: 'introduction', title: 'What is ThreatWeaver?', keywords: 'overview introduction workbench intelligence domains public IPv4 purpose', content: <>
    <p>ThreatWeaver is a local security investigation workbench for a domain or public IPv4 address. It collects external intelligence, preserves findings and their sources in FalkorDB, and follows bounded graph relationships to produce a report you can inspect.</p>
    <p>Use it to understand an unfamiliar indicator, explore DNS relationships, review source context, and organize follow-up work. It is an investigation aid; it does not scan a website for application vulnerabilities or certify that a site is safe.</p>
    <div className="docs-three"><div><Globe2 size={19} /><strong>Collect</strong><span>OTX context and DNS observations</span></div><div><GitBranch size={19} /><strong>Connect</strong><span>Persistent, sourced graph links</span></div><div><ShieldCheck size={19} /><strong>Review</strong><span>Evidence, uncertainty, next steps</span></div></div>
  </> },
  { id: 'quickstart', title: 'Your first investigation', keywords: 'quick start example.com 8.8.8.8 vercel netlify domain URL input investigate export checklist history', content: <>
    <ol className="docs-steps"><li><strong>Open the workbench.</strong> Check the sidebar status. FalkorDB should be ready, and an OTX key enables live threat intelligence.</li><li><strong>Enter one indicator.</strong> Try <code>example.com</code>, <code>8.8.8.8</code>, or your own hostname, such as <code>tripcraft-blue.vercel.app</code>. Omit the scheme, path, and port.</li><li><strong>Choose your options.</strong> Enable the graph pivot to enrich one observed neighbor. The DeepSeek planner is optional and requires its own key.</li><li><strong>Investigate and inspect.</strong> Read the observations and source warnings. Select a graph edge or an evidence row to view provenance and timestamps.</li><li><strong>Follow up.</strong> Track recommended actions, download Markdown or JSON, and reopen saved runs from recent investigations.</li></ol>
    <Callout>Checklist progress is stored in this browser per indicator. It is not shared with other browsers or included in report downloads. Example hostnames are test inputs, not claims about reputation.</Callout>
    <a className="text-link" href="/investigate">Try it in the workbench <ArrowRight size={15} /></a>
  </> },
  { id: 'architecture', title: 'How an investigation flows', keywords: 'architecture flowchart system React FastAPI FalkorDB OTX DNS DeepSeek pipeline Excalidraw', content: <>
    <p>The React interface sends an indicator and options to FastAPI. The API validates the input, requests OTX general intelligence and passive DNS, and requests current A records from Google Public DNS for domains. It persists observations before reading graph paths and may select one currently observed neighbor for an OTX lookup.</p>
    <Diagram name="system-flow" />
    <p>The optional planner runs as a separate, audited stage. The evidence-backed report remains authoritative. The finished report and tool audit are saved as an investigation snapshot in the same graph.</p>
    <p>If an external source fails, the report includes warnings and uses the remaining available evidence. A partial result is a coverage limitation, not a threat verdict.</p>
  </> },
  { id: 'graph', title: 'Nodes, arrows, and two-hop paths', keywords: 'graph nodes arrows relationships hop two hops paths colors numbers current_dns_a passive_dns shared hosting owner', content: <>
    <p>The workbench graph focuses on domains, IPs, and sourced relationships. The FalkorDB Browser shows the fuller data model, including observation, evidence, and saved-investigation nodes.</p>
    <div className="docs-table-wrap"><table><thead><tr><th>Node</th><th>Meaning</th></tr></thead><tbody><tr><td><span className="type-dot indicator" />Indicator</td><td>A domain or public IPv4 address.</td></tr><tr><td><span className="type-dot observation" />Observation</td><td>A predicate and observed value, with time context.</td></tr><tr><td><span className="type-dot evidence" />Evidence</td><td>A source reference, URL, and retrieval timestamp.</td></tr><tr><td><span className="type-dot investigation" />Investigation</td><td>A saved run with its report and tool audit.</td></tr></tbody></table></div>
    <p>Colors in FalkorDB Browser can vary with its styling. Read the label and properties to identify a node. Numeric node labels are identifiers, not risk scores. Arrow direction records a relationship; it does not show an attack or network traffic.</p>
    <Diagram name="two-hop-paths" />
    <p>One hop crosses one <code>OBSERVED_LINK</code> between indicators. Two hops cross two such links. The traversal can follow relationships in either direction; a second hop only appears when the stored graph contains the necessary links. The provenance chain <code>Indicator → Observation → Evidence</code> is not a two-hop indicator path.</p>
    <Callout><strong>More connections do not mean more danger.</strong> Unrelated sites can share an IP address. An infrastructure relationship alone does not establish common ownership, malicious intent, or compromise.</Callout>
  </> },
  { id: 'evidence', title: 'Evidence and provenance', keywords: 'evidence provenance source URL timestamps fetched observation model relationships HAS_OBSERVATION SUPPORTED_BY POINTS_TO OBSERVED_LINK HAS_INVESTIGATION Excalidraw', content: <>
    <p>Each stored finding retains a stable observation ID and an associated evidence record. Repeated fetches reuse those IDs for matching findings and update the last fetch time. The inspector exposes the source URL, source ID, observation ID, evidence ID, and available timestamps.</p>
    <Diagram name="evidence-model" />
    <div className="docs-table-wrap"><table><thead><tr><th>Relationship</th><th>Read it as</th></tr></thead><tbody><tr><td><code>HAS_OBSERVATION</code></td><td>Indicator → its recorded finding.</td></tr><tr><td><code>SUPPORTED_BY</code></td><td>Observation → supporting evidence record.</td></tr><tr><td><code>POINTS_TO</code></td><td>Observation → related indicator named in the finding.</td></tr><tr><td><code>OBSERVED_LINK</code></td><td>Indicator → related indicator, with an observation ID and predicate.</td></tr><tr><td><code>HAS_INVESTIGATION</code></td><td>Indicator → saved investigation run.</td></tr></tbody></table></div>
    <p><code>current_dns_a</code> records a current Google Public DNS A answer. <code>passive_dns</code> records a historical association returned by OTX. Compare the source timestamp and last fetched time; a fresh retrieval of a historical observation does not make that association current.</p>
    <Callout>Some sources do not supply an observation timestamp. A retrieval timestamp tells you when ThreatWeaver fetched the record, not necessarily when the underlying event occurred.</Callout>
  </> },
  { id: 'reports', title: 'Reading and exporting the report', keywords: 'report complete partial freshness confidence zero pulses unknowns observations inferences warnings Markdown JSON download export audit', content: <>
    <p>The report keeps four questions separate: what the sources observed, what may be inferred, what remains unknown, and what an analyst should review next.</p>
    <ul><li><strong>Complete / partial:</strong> whether the requested source collection finished without warnings. This is not a safety rating.</li><li><strong>OTX pulses:</strong> the number reported by OTX for the indicator. Zero pulses is not proof of safety; a mention is not proof of compromise.</li><li><strong>Freshness:</strong> whether current external data was collected or the investigation is relying on stored context. Check individual source times.</li><li><strong>Graph links:</strong> sourced links shown in the bounded graph, not a count of confirmed threats.</li></ul>
    <p>Use <strong>Report .md</strong> for a readable report with source references, uncertainty, and timestamps. Use <strong>JSON</strong> for the complete response, including report, graph, evidence, and planner audit. Exports do not include your locally checked action items.</p>
  </> },
  { id: 'planner', title: 'The optional tool planner', keywords: 'agent AI DeepSeek planner tools audit optional key iterations lookup limits', content: <>
    <p>ThreatWeaver works without an LLM. When enabled and configured, DeepSeek can request a small set of tools: read graph paths, read source evidence, or request OTX context for an allowed observed neighbor. Tool requests and their outcomes are audited.</p>
    <p>The planner is limited to three model iterations and at most three tool calls per iteration. It may perform one neighbor lookup within its own stage, separately from the deterministic investigator’s optional single pivot. It cannot submit arbitrary Cypher or issue blocking or isolation actions.</p>
    <Callout>The planner does not replace the sourced report. If the key is missing or planning fails, inspect the planner status and continue reviewing the available evidence.</Callout>
  </> },
  { id: 'limits', title: 'Scope, bounds, and interpretation', keywords: 'limits safety scope scan vulnerability malicious false positives shared IP DNS bounds 50 12 5 hops', content: <>
    <div className="docs-table-wrap"><table><thead><tr><th>Boundary</th><th>Current behavior</th></tr></thead><tbody><tr><td>Accepted input</td><td>One bare domain or global public IPv4 address.</td></tr><tr><td>Graph traversal</td><td>At most two hops; at most 50 paths per bounded query.</td></tr><tr><td>Source collection</td><td>Up to 12 passive DNS entries and five current A answers per lookup.</td></tr><tr><td>Stored evidence reads</td><td>At most 50 records per query.</td></tr><tr><td>Investigation history</td><td>API returns up to 20 recent runs; sidebar shows eight.</td></tr><tr><td>Enforcement</td><td>Recommendations only; no automated blocking or isolation.</td></tr></tbody></table></div>
    <p>Queries are bounded samples, not exhaustive discovery. Shared IPs, historical DNS relationships, or OTX pulse membership are leads to validate against trusted internal telemetry. ThreatWeaver does not inspect site source code, perform penetration tests, or guarantee that a URL is safe to visit.</p>
    <p>Current DNS changes over time. Stored graph context can include older observations. Always inspect the predicate, timestamps, and source before drawing a conclusion.</p>
  </> },
  { id: 'setup', title: 'Run locally', keywords: 'install setup Docker compose Python Node env keys ports localhost database Windows PowerShell startup', content: <>
    <p>Use Docker Desktop with Compose, Python 3.11–3.14, and Node.js 20+. Run these commands from the repository root in PowerShell. Configure <code>OTX_API_KEY</code> in <code>.env</code>; <code>DEEPSEEK_API_KEY</code> is optional.</p>
    <CodeBlock>{'if (-not (Test-Path .env)) { Copy-Item .env.example .env }\nnotepad .env\ndocker compose up -d\npython -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt\n.\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000'}</CodeBlock>
    <p>Leave the API running. Open another terminal from the repository root:</p><CodeBlock>{'cd frontend\nnpm.cmd install\nnpm.cmd run dev -- --host 127.0.0.1'}</CodeBlock>
    <p>Open <a href="http://127.0.0.1:5173">127.0.0.1:5173</a>. The API runs on port 8000; FalkorDB Browser runs on port 3000. The database connection uses port 6379, which is not a webpage. Keep credentials in the local environment file.</p>
  </> },
  { id: 'api', title: 'API reference and graph queries', keywords: 'API endpoints POST GET curl Cypher query graph health trace_paths get_evidence observations investigations', content: <>
    <p>The development frontend proxies <code>/api</code> to the local API. The following routes support the same investigation workflow used by the interface.</p>
    <div className="docs-table-wrap"><table><thead><tr><th>Route</th><th>Purpose</th></tr></thead><tbody><tr><td><code>GET /api/health</code></td><td>Database readiness and key configuration flags.</td></tr><tr><td><code>POST /api/investigations</code></td><td>Investigate an indicator and save the run.</td></tr><tr><td><code>GET /api/investigations?limit=8</code></td><td>List saved runs.</td></tr><tr><td><code>GET /api/investigations/&#123;uuid&#125;</code></td><td>Reopen a saved report and audit.</td></tr><tr><td><code>GET /api/observations/&#123;id&#125;</code></td><td>Read provenance behind an observation.</td></tr><tr><td><code>GET /api/tools/trace_paths</code></td><td>Read bounded paths using indicator, depth, and limit.</td></tr><tr><td><code>GET /api/tools/get_evidence</code></td><td>Read stored evidence using indicator and limit.</td></tr></tbody></table></div>
    <p>Example investigation request body:</p><CodeBlock>{'{\n  "indicator": "example.com",\n  "expand": true,\n  "use_agent": false\n}'}</CodeBlock>
    <p>To inspect only a domain’s indicator links in FalkorDB Browser, select the <code>threatweaver</code> graph and run this read-only query:</p>
    <CodeBlock>{"MATCH (d:Indicator {key: 'domain:example.com'})-[r:OBSERVED_LINK]-(n:Indicator)\nRETURN d, r, n\nLIMIT 30"}</CodeBlock>
  </> },
  { id: 'troubleshooting', title: 'Troubleshooting and common questions', keywords: 'errors failed ConnectError unreachable network firewall not working 422 503 private URL graph empty no data rate limit missing key', content: <>
    <details open><summary>The domain loads in a browser, but investigation is partial.</summary><p>ThreatWeaver queries intelligence and DNS providers rather than loading the website. Read the source warnings. A <code>ConnectError</code> can mean the API process lacks outbound network access; a working browser connection does not establish that the API can reach those services.</p></details>
    <details><summary>Why does the API reject my input?</summary><p>Use a bare domain such as <code>tripcraft-blue.vercel.app</code>. Remove <code>https://</code>, paths, and ports. Private/local IP addresses and IPv6 inputs are unsupported.</p></details>
    <details><summary>Why are there no graph links or no second hop?</summary><p>A valid indicator may have little external coverage. A second hop requires stored relationships beyond its immediate neighbors. Confirm source availability, enable the optional pivot, and inspect the available evidence; a sparse graph is a valid result.</p></details>
    <details><summary>FalkorDB is unavailable.</summary><p>Start Docker Desktop and run <code>docker compose up -d</code>. Check <code>docker compose ps</code> and <code>docker compose logs falkordb</code>. Use port 3000 for its browser, not 6379.</p></details>
    <details><summary>OTX or DeepSeek reports a missing key or rate limit.</summary><p>Add the appropriate key to <code>.env</code> and restart the API. Check provider access if the key is rejected; wait before retrying rate-limited requests. The DeepSeek planner is optional.</p></details>
    <details><summary>Does zero OTX pulses mean the site is safe?</summary><p>No. It means the source returned zero pulses for that indicator at lookup time. Assess the evidence alongside your own telemetry; neither absence of mentions nor graph proximity establishes a security verdict.</p></details>
  </> },
  { id: 'diagrams', title: 'Edit the Excalidraw diagrams', keywords: 'download Excalidraw editable diagram flowchart SVG scene presentation video export', content: <>
    <p>Every flowchart on this site has a matching editable <code>.excalidraw</code> scene. Download the scene, open <a href="https://excalidraw.com" target="_blank" rel="noreferrer">Excalidraw <ExternalLink size={12} /></a>, and choose <strong>Open</strong> from its menu to load the file. You can move boxes, edit labels, rearrange connectors, and export an image for your presentation.</p>
    <div className="diagram-downloads">{Object.entries(diagramInfo).map(([name, item]) => <a key={name} href={`/diagrams/${name}.excalidraw`} download><Waypoints size={19} /><span><strong>{item.title}</strong><small>Editable Excalidraw scene</small></span><Download size={17} /></a>)}</div>
    <p>The SVG previews and scene files are generated from the same diagram definitions. To regenerate repository assets after editing those definitions, run <code>python docs/generate_web_diagrams.py</code>. Changes made to a downloaded scene do not automatically update the website preview.</p>
  </> },
]

function textContent(node: ReactNode): string {
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(textContent).join(' ')
  if (isValidElement<{ children?: ReactNode }>(node)) return textContent(node.props.children)
  return ''
}

function Documentation() {
  const [query, setQuery] = useState('')
  const normalizedQuery = query.trim().toLowerCase()
  const visibleSections = sections.filter(section => `${section.title} ${section.keywords} ${textContent(section.content)}`.toLowerCase().includes(normalizedQuery))
  return <div className="public-site"><a href="#docs-main" className="skip-link">Skip to documentation</a><Header page="docs" />
    <div className="docs-container"><aside className="docs-sidebar"><a className="docs-back" href="/"><ChevronRight size={13} /> Back to overview</a><div className="site-eyebrow">THE FIELD GUIDE</div>
      <label className="docs-search"><Search size={16} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search documentation…" aria-label="Search documentation topics" />{query && <button onClick={() => setQuery('')} aria-label="Clear documentation search"><X size={14} /></button>}</label>
      {query && <p className="docs-search-status" role="status">{visibleSections.length} matching topics</p>}
      <nav aria-label="Documentation topics">{visibleSections.map((section, index) => <a key={section.id} href={`#${section.id}`}><span>{String(index + 1).padStart(2, '0')}</span>{section.title}</a>)}</nav>
      <a className="docs-workbench-link" href="/investigate"><Radar size={17} /><span>Ready to investigate?<small>Open your workbench</small></span><ArrowUpRight size={16} /></a>
    </aside><main id="docs-main" tabIndex={-1} className="docs-main"><div className="docs-heading"><div className="site-eyebrow"><BookOpen size={15} /> THREATWEAVER DOCUMENTATION</div><h1>Understand the signal.<br /><em>Follow the evidence.</em></h1><p>A practical guide to investigations, graph relationships, source provenance, and the limits of external intelligence.</p><div className="docs-tags"><span><Layers3 size={13} /> Workflow & architecture</span><span><Waypoints size={13} /> Excalidraw diagrams</span><span><Code2 size={13} /> API & local setup</span></div></div>
      {visibleSections.length ? visibleSections.map(section => <section id={section.id} className="docs-section" key={section.id}><div className="docs-section-number">{String(sections.indexOf(section) + 1).padStart(2, '0')} / FIELD NOTES</div><h2><a href={`#${section.id}`}>{section.title}<span aria-hidden="true">#</span></a></h2>{section.content}<a className="back-to-top" href="#docs-main">Back to top ↑</a></section>) : <div className="docs-no-results"><Search size={28} /><h2>No matching topics</h2><p>Try “graph”, “DNS”, “setup”, or “Excalidraw”.</p><button className="site-button secondary" onClick={() => setQuery('')}>Show all documentation</button></div>}
    </main></div><Footer /></div>
}

export default function Site() {
  const path = window.location.pathname.replace(/\/+$/, '') || '/'
  useEffect(() => {
    document.title = `${path === '/docs' ? 'Documentation' : path === '/investigate' ? 'Investigation workbench' : 'Evidence-first threat investigation'} | ThreatWeaver`
    // Fragment targets are rendered by React after the initial HTML response.
    if (window.location.hash) {
      try {
        const id = decodeURIComponent(window.location.hash.slice(1))
        document.getElementById(id)?.scrollIntoView()
      } catch { /* Ignore malformed fragments supplied in a URL. */ }
    }
  }, [path])
  if (path === '/investigate') return <Workbench />
  if (path === '/docs') return <Documentation />
  if (path === '/') return <Home />
  return <div className="public-site"><Header page="home" /><main className="site-container not-found"><div className="site-eyebrow">404 / NO PATH FOUND</div><h1>This trail ends here.</h1><p>Head back to the overview or start an investigation.</p><a className="site-button" href="/">Back to home <ArrowRight size={17} /></a></main><Footer /></div>
}
