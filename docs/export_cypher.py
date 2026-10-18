"""Export the application's actual literal Cypher templates for reviewers."""
import ast
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "backend" / "app" / "graph.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
parts = [
    "// ThreatWeaver: actual Cypher templates extracted from backend/app/graph.py.",
    "// Regenerate: python docs/export_cypher.py",
    "// Includes writes and reads. Execute one template with its parameters, not the whole file.",
    "// Algorithm explanation and literal read-only demo queries: docs/GRAPH_QUERIES.md.",
    "",
]
count = 0
for node in ast.walk(tree):
    if not isinstance(node, ast.ClassDef) or node.name != "GraphStore":
        continue
    for method in node.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        queries = []
        for child in ast.walk(method):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                query = textwrap.dedent(child.value).strip()
                if re.match(r"^(MATCH|MERGE|CREATE INDEX)\b", query):
                    queries.append((child.lineno, query))
        for line, query in sorted(queries):
            parameters = sorted(set(re.findall(r"\$([a-z_]+)", query)))
            parts.extend([
                f"// {method.name} — backend/app/graph.py:{line}",
                "// Parameters: " + (", ".join(parameters) or "none"),
                query + ";",
                "",
            ])
            count += 1
(ROOT / "docs" / "queries.cypher").write_text("\n".join(parts), encoding="utf-8")
print(f"Exported {count} query templates to docs/queries.cypher")
