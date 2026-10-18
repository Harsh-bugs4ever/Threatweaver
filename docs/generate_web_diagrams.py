"""Build matching website SVG previews and editable Excalidraw scenes.

Run from any directory: python docs/generate_web_diagrams.py
Both representations share geometry and content; no external service is needed.
"""
from html import escape
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)
WIDTH, HEIGHT = 1160, 650


def generate(slug, title, subtitle, boxes, arrows, notes):
    elements = []
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#b5a1e7" stroke-width="1.5"/></marker></defs>',
           f'<rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="#14131f"/>']

    def base(identifier, kind, x, y, w, h, stroke="#b5a1e7", fill="transparent"):
        return dict(id=identifier, type=kind, x=x, y=y, width=w, height=h, angle=0,
                    strokeColor=stroke, backgroundColor=fill, fillStyle="solid", strokeWidth=2,
                    strokeStyle="solid", roughness=1, opacity=100, groupIds=[], frameId=None,
                    roundness={"type": 3} if kind == "rectangle" else None,
                    seed=1000 + len(elements), version=1, versionNonce=2000 + len(elements),
                    isDeleted=False, boundElements=None, updated=1, link=None, locked=False)

    def text(identifier, value, x, y, size=16, color="#b7abc9", width=1040):
        lines = value.split("\n")
        item = base(identifier, "text", x, y, width, len(lines) * size * 1.35, color)
        item.update(text=value, originalText=value, fontSize=size, fontFamily=2,
                    textAlign="left", verticalAlign="top", containerId=None, autoResize=False,
                    lineHeight=1.35, baseline=int(size * .8))
        elements.append(item)
        for index, line in enumerate(lines):
            svg.append(f'<text x="{x}" y="{y + size + index * size * 1.35}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')

    text("title", title, 40, 30, 29, "#eee7fa")
    text("subtitle", subtitle, 40, 78, 16)
    for index, (x, y, heading, detail, color) in enumerate(boxes):
        group_start = len(elements)
        elements.append(base(f"box-{index}", "rectangle", x, y, 260, 112, color, "#211b30"))
        svg.append(f'<rect x="{x}" y="{y}" width="260" height="112" rx="12" fill="#211b30" stroke="{color}" stroke-width="1.7"/>')
        text(f"heading-{index}", heading, x + 18, y + 18, 19, "#eee7fa", 224)
        text(f"detail-{index}", detail, x + 18, y + 54, 14, "#b7abc9", 224)
        for element in elements[group_start:]:
            element["groupIds"] = [f"node-{index}"]
    for index, (points, label, lx, ly) in enumerate(arrows):
        x = min(point[0] for point in points)
        y = min(point[1] for point in points)
        item = base(f"arrow-{index}", "arrow", x, y,
                    max(p[0] for p in points) - min(p[0] for p in points),
                    max(p[1] for p in points) - min(p[1] for p in points))
        item.update(points=[[px-x, py-y] for px, py in points], lastCommittedPoint=None,
                    startBinding=None, endBinding=None, startArrowhead=None,
                    endArrowhead="arrow", elbowed=False)
        elements.append(item)
        route = " ".join(f'{px},{py}' for px, py in points)
        svg.append(f'<polyline points="{route}" fill="none" stroke="#b5a1e7" stroke-width="1.8" stroke-linejoin="round" marker-end="url(#arrow)"/>')
        label_width = len(label) * 7 + 12
        elements.append(base(f"label-bg-{index}", "rectangle", lx - 5, ly - 3,
                             label_width, 22, "transparent", "#14131f"))
        svg.append(f'<rect x="{lx - 5}" y="{ly - 3}" width="{label_width}" height="22" rx="4" fill="#14131f"/>')
        text(f"label-{index}", label, lx, ly, 11, "#d1bff1", 260)
    for index, note in enumerate(notes):
        text(f"note-{index}", note, 40, 558 + index * 30, 15)
    svg.append('</svg>')
    scene = dict(type="excalidraw", version=2, source="https://excalidraw.com", elements=elements,
                 appState={"viewBackgroundColor": "#14131f", "gridSize": None}, files={})
    (OUT / f"{slug}.excalidraw").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    (OUT / f"{slug}.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


generate("system-flow", "From one indicator to a sourced investigation",
         "The API gathers external context, stores provenance, and reads bounded graph paths.", [
    (40, 160, "01 / React workbench", "Domain or public IPv4\nGraph, evidence, report", "#aa8ee6"),
    (440, 160, "02 / FastAPI", "Validate, enrich, persist\nTrace paths and select a pivot", "#83b8e8"),
    (840, 160, "03 / FalkorDB", "Indicators and observations\nEvidence and saved runs", "#89c8a9"),
    (40, 410, "AlienVault OTX", "Pulse context\nHistorical passive DNS", "#e59cae"),
    (440, 410, "Google Public DNS", "Current domain A answers\nUp to five public IPv4s", "#89c8a9"),
    (840, 410, "Optional DeepSeek", "Bounded, audited tool calls\nSeparate planner stage", "#aa8ee6"),
], [
    ([(310, 216), (430, 216)], "INVESTIGATE", 326, 187),
    ([(710, 216), (830, 216)], "WRITE / READ", 725, 187),
    ([(485, 284), (170, 398)], "OTX LOOKUP", 262, 330),
    ([(570, 284), (570, 398)], "LIVE DNS", 585, 328),
    ([(655, 284), (970, 398)], "IF ENABLED", 817, 330),
], ["Source failures produce warnings and partial results; available evidence is retained.",
    "The report supports analyst review. It does not block traffic, isolate hosts, or establish compromise."])

generate("evidence-model", "Every finding has a source",
         "The full database graph records indicators, findings, supporting records, and investigation history.", [
    (40, 160, "Indicator", "A domain or public IP\nThe subject of a finding", "#d995ee"),
    (440, 160, "Observation", "Predicate + observed value\nSource time + last fetch", "#d4a055"),
    (840, 160, "Evidence", "Source ID and source URL\nRetrieval timestamp", "#83a7ff"),
    (40, 410, "Investigation", "Saved report snapshot\nRun ID, time, and method", "#e78cca"),
    (440, 410, "Related indicator", "A sourced neighboring\ndomain or IP address", "#d995ee"),
], [
    ([(310, 216), (430, 216)], "HAS_OBSERVATION", 308, 187),
    ([(710, 216), (830, 216)], "SUPPORTED_BY", 726, 187),
    ([(170, 284), (170, 398)], "HAS_INVESTIGATION", 42, 330),
    ([(570, 284), (570, 398)], "POINTS_TO", 585, 330),
    ([(310, 258), (423, 451)], "OBSERVED_LINK", 290, 356),
], ["OBSERVED_LINK stores the observation ID and predicate as a direct indicator-to-indicator connection.",
    "Graph node IDs are database identifiers, not scores. The arrow label defines its meaning."])

generate("two-hop-paths", "Two hops. One connection at a time.",
         "Illustrative topology only: these labels are examples, not live findings or a reputation verdict.", [
    (40, 200, "Starting domain", "site-a.example\nYour investigation root", "#d995ee"),
    (440, 200, "Shared public IP", "An observed address\nOne connection from the root", "#83b8e8"),
    (840, 200, "Related domain", "site-b.example\nTwo connections from the root", "#d995ee"),
], [
    ([(310, 256), (430, 256)], "DNS ASSOCIATION", 316, 221),
    ([(830, 256), (710, 256)], "DNS ASSOCIATION", 716, 221),
], ["Hop 1: start domain to IP. Hop 2: traverse from the IP to the related domain.",
    "Paths follow OBSERVED_LINK in either direction. A second hop exists only when stored links support it.",
    "Shared hosting does not establish shared ownership, malicious intent, or compromise."])

print("Generated three SVG / Excalidraw pairs in", OUT)
