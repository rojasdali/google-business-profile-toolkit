#!/usr/bin/env python3
"""build_graph.py: Converts markdown notes into graph.json and GRAPH_REPORT.md."""
import json
import os
import re
from datetime import datetime

VAULT_DIRS = ["wiki/concepts", "wiki/entities", "wiki/systems"]
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def parse_md(path: str) -> tuple[dict, str]:
    with open(path, encoding="utf-8") as f:
        content = f.read()
    fm, body = {}, content
    if content.startswith("---") and len(content.split("---", 2)) >= 3:
        for line in content.split("---", 2)[1].split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip("\"'")
        body = content.split("---", 2)[2]
    return fm, body


def main() -> None:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nodes, node_map = [], {}
    for vdir in VAULT_DIRS:
        d = os.path.join(base, vdir)
        if not os.path.exists(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            nid = os.path.splitext(fn)[0]
            fm, body = parse_md(os.path.join(d, fn))
            node = {
                "id": nid,
                "title": fm.get("title", nid.replace("-", " ").title()),
                "type": fm.get("type", vdir.split("/")[-1].rstrip("s")),
                "summary": fm.get("summary", body.strip()[:140]),
            }
            nodes.append(node)
            node_map[nid] = (node, body)

    edges, node_ids = [], {n["id"] for n in nodes}
    for sid, (_, body) in node_map.items():
        for m in WIKILINK_RE.finditer(body):
            target = os.path.splitext(os.path.basename(m.group(1).strip()))[0]
            if target in node_ids and target != sid and not any(e["source"] == sid and e["target"] == target for e in edges):
                edges.append({"source": sid, "target": target, "type": "relates_to"})

    deg = {nid: sum(1 for e in edges if e["source"] == nid or e["target"] == nid) for nid in node_ids}
    orphans = [nid for nid, c in deg.items() if c == 0]
    out_dir = os.path.join(base, "graph")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "graph.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "built_at": datetime.utcnow().isoformat(),
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                },
            },
            f,
            indent=2,
        )

    report = f"# Knowledge Graph Analysis Report\n\nBuilt: `{datetime.utcnow().isoformat()}Z`\n\n"
    report += f"- **Nodes**: {len(nodes)}\n- **Edges**: {len(edges)}\n- **Orphans**: {len(orphans)}\n\n"
    report += "## Connected Entities\n" + "\n".join(f"- `[[{nid}]]` ({deg[nid]} links)" for nid in sorted(deg, key=deg.get, reverse=True)) + "\n"
    with open(os.path.join(out_dir, "GRAPH_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Generated graph/graph.json ({len(nodes)} nodes, {len(edges)} edges) and GRAPH_REPORT.md")


if __name__ == "__main__":
    main()
