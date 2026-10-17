"""Generate the editable Excalidraw architecture scene and its README preview."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path


HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1320, 710

BOXES = [
    ("input", 50, 150, 230, 142, "01  Indicator", "Domain or public IPv4", "#fff7ed", "#d97706"),
    ("web", 350, 150, 230, 142, "02  React workbench", "Search, graph, evidence", "#eef2ff", "#6366f1"),
    ("api", 670, 150, 230, 142, "03  FastAPI investigator", "Validate, enrich, trace", "#ecfeff", "#0891b2"),
    ("graph", 1010, 150, 230, 142, "04  FalkorDB", "Evidence, links, history", "#ecfdf5", "#059669"),
    ("otx", 390, 460, 230, 126, "AlienVault OTX", "Pulses + passive DNS", "#fef2f2", "#e11d48"),
    ("dns", 700, 460, 230, 126, "Google Public DNS", "Current A records", "#f0fdf4", "#16a34a"),
    ("deepseek", 1010, 460, 230, 126, "DeepSeek (optional)", "Bounded tool planning", "#f5f3ff", "#7c3aed"),
]

# Each route starts and ends outside its boxes. The source routes are ordered
# left-to-right and occupy separate lanes, so no connector crosses another.
ARROWS = [
    ("input-web", [(290, 221), (340, 221)], "#64748b", False),
    ("web-api", [(590, 221), (660, 221)], "#64748b", False),
    ("api-graph", [(910, 221), (1000, 221)], "#64748b", False),
    ("api-otx", [(714, 306), (505, 446)], "#e11d48", False),
    ("api-dns", [(785, 306), (815, 446)], "#16a34a", False),
    ("api-deepseek", [(856, 306), (1125, 446)], "#7c3aed", False),
]


def common(element_id: str, element_type: str, x: float, y: float, width: float, height: float,
           stroke: str, background: str = "transparent") -> dict:
    return {
        "id": element_id, "type": element_type, "x": x, "y": y,
        "width": width, "height": height, "angle": 0,
        "strokeColor": stroke, "backgroundColor": background,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "roundness": {"type": 3} if element_type == "rectangle" else None,
        "seed": 1000 + sum(ord(char) for char in element_id),
        "version": 1, "versionNonce": 2000 + sum(ord(char) for char in element_id),
        "isDeleted": False, "boundElements": None, "updated": 0,
        "created": None, "link": None, "locked": False,
    }


def text_element(element_id: str, text: str, x: float, y: float,
                 width: float, height: float, size: int, color: str,
                 align: str = "left") -> dict:
    element = common(element_id, "text", x, y, width, height, color)
    element.update({
        "text": text, "originalText": text, "fontSize": size,
        "fontFamily": 2, "textAlign": align, "verticalAlign": "middle",
        "baseline": int(size * 0.8), "containerId": None,
        "autoResize": False, "lineHeight": 1.25,
    })
    return element


elements: list[dict] = []
elements.append(text_element("title", "ThreatWeaver / system flow", 50, 28, 950, 42, 31, "#0f172a"))
elements.append(text_element("subtitle", "Source-backed investigation through a persistent graph", 50, 77, 900, 26, 17, "#475569"))
elements.append(text_element("request-label", "REQUEST + GRAPH CONTEXT", 50, 112, 400, 20, 13, "#64748b"))
elements.append(text_element("source-label", "EXTERNAL ENRICHMENT", 50, 417, 300, 20, 13, "#64748b"))

for box_id, x, y, width, height, heading, detail, fill, stroke in BOXES:
    elements.append(common(f"box-{box_id}", "rectangle", x, y, width, height, stroke, fill))
    elements.append(text_element(f"heading-{box_id}", heading, x + 19, y + 29, width - 38, 31, 18, "#0f172a"))
    elements.append(text_element(f"detail-{box_id}", detail, x + 19, y + 76, width - 38, 24, 15, "#475569"))

for arrow_id, points, stroke, two_way in ARROWS:
    (x1, y1), (x2, y2) = points
    origin_x, origin_y = min(x1, x2), min(y1, y2)
    arrow = common(f"arrow-{arrow_id}", "arrow", origin_x, origin_y,
                   abs(x2 - x1), abs(y2 - y1), stroke)
    arrow.update({
        "points": [[x1 - origin_x, y1 - origin_y], [x2 - origin_x, y2 - origin_y]],
        "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
        "startArrowhead": "arrow" if two_way else None,
        "endArrowhead": "arrow", "elbowed": False,
    })
    elements.append(arrow)

elements.append(text_element(
    "footer", "Observations keep source IDs and retrieval times. Graph links guide at most one follow-up lookup.",
    50, 628, 1200, 25, 16, "#334155"))
elements.append(text_element(
    "safety", "Recommendations only: no automatic blocking or isolation.",
    50, 660, 1000, 21, 14, "#64748b"))

scene = {
    "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {"gridSize": None, "viewBackgroundColor": "#f8fafc"},
    "files": {},
}
(HERE / "system-flow.excalidraw").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
    '<title id="title">ThreatWeaver system flow</title>',
    '<desc id="desc">Indicator to React workbench, FastAPI investigator, and FalkorDB. The investigator uses OTX, Google Public DNS, and optionally DeepSeek.</desc>',
    '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#64748b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>',
    '<marker id="pink" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#e11d48" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>',
    '<marker id="green" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#16a34a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>',
    '<marker id="purple" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#7c3aed" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>',
    '<rect width="1320" height="710" fill="#f8fafc"/>',
    '<text x="50" y="61" font-family="Arial,sans-serif" font-size="31" font-weight="700" fill="#0f172a">ThreatWeaver / system flow</text>',
    '<text x="50" y="93" font-family="Arial,sans-serif" font-size="17" fill="#475569">Source-backed investigation through a persistent graph</text>',
    '<text x="50" y="128" font-family="Arial,sans-serif" font-size="13" font-weight="700" letter-spacing="1.4" fill="#64748b">REQUEST + GRAPH CONTEXT</text>',
    '<text x="50" y="433" font-family="Arial,sans-serif" font-size="13" font-weight="700" letter-spacing="1.4" fill="#64748b">EXTERNAL ENRICHMENT</text>',
]

# Lines sit behind boxes. Marker placement keeps tips outside every box.
for arrow_id, points, stroke, two_way in ARROWS:
    (x1, y1), (x2, y2) = points
    marker = {"#64748b": "arrow", "#e11d48": "pink", "#16a34a": "green", "#7c3aed": "purple"}[stroke]
    start = ' marker-start="url(#arrow)"' if two_way else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round" marker-end="url(#{marker})"{start}/>')

for box_id, x, y, width, height, heading, detail, fill, stroke in BOXES:
    parts.extend([
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="2.3"/>',
        f'<text x="{x+19}" y="{y+55}" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#0f172a">{escape(heading)}</text>',
        f'<text x="{x+19}" y="{y+98}" font-family="Arial,sans-serif" font-size="15" fill="#475569">{escape(detail)}</text>',
    ])
parts.extend([
    '<text x="50" y="646" font-family="Arial,sans-serif" font-size="16" fill="#334155">Observations keep source IDs and retrieval times. Graph links guide at most one follow-up lookup.</text>',
    '<text x="50" y="678" font-family="Arial,sans-serif" font-size="14" fill="#64748b">Recommendations only: no automatic blocking or isolation.</text>',
    '</svg>',
])
(HERE / "system-flow.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")

# Fail generation if a connector enters a box interior. Endpoints sit outside
# the boxes and each arrow is straight, so this catches accidental rerouting.
for arrow_id, points, _, _ in ARROWS:
    (x1, y1), (x2, y2) = points
    for box_id, bx, by, bw, bh, *_ in BOXES:
        for step in range(1, 100):
            ratio = step / 100
            px, py = x1 + (x2 - x1) * ratio, y1 + (y2 - y1) * ratio
            if bx < px < bx + bw and by < py < by + bh:
                raise ValueError(f"Connector {arrow_id} overlaps {box_id}")


def orientation(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int]) -> int:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


for index, (first_id, (a, b), _, _) in enumerate(ARROWS):
    for second_id, (c, d), _, _ in ARROWS[index + 1:]:
        if orientation(a, b, c) * orientation(a, b, d) < 0 and \
           orientation(c, d, a) * orientation(c, d, b) < 0:
            raise ValueError(f"Connectors {first_id} and {second_id} cross")

print("Generated system-flow.excalidraw and system-flow.svg; connector lanes are clear.")
