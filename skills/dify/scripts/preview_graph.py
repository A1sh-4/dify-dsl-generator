"""
preview_graph.py - Generate a Mermaid flowchart from a Dify DSL YAML file.

Usage:
    python preview_graph.py <path/to/workflow.yml>

Reads the workflow.graph section of the DSL and emits a Mermaid flowchart LR
diagram to stdout. Paste the output into any Mermaid renderer or markdown
code fence to visualise the node graph before importing into Dify.

Node shapes by type:
  start / end / answer    -> stadium  ([Label])
  llm / agent             -> rounded  (Label)
  if-else / question-classifier -> diamond {Label}
  knowledge-retrieval     -> database [(Label)]
  code / iteration        -> subroutine [[Label]]
  all others              -> rectangle [Label]

Edge labels by handle:
  true -> Yes
  false -> No
  success-branch -> Success
  fail-branch -> Fail
  (source or missing) -> no label
"""

import argparse
import re
import sys

import yaml


EDGE_LABELS = {
    "true": "Yes",
    "false": "No",
    "success-branch": "Success",
    "fail-branch": "Fail",
}

NODE_SHAPES = {
    "start": ("([", "])"),
    "end": ("([", "])"),
    "answer": ("([", "])"),
    "llm": ("(", ")"),
    "agent": ("(", ")"),
    "if-else": ("{", "}"),
    "question-classifier": ("{", "}"),
    "knowledge-retrieval": ("[(", ")]"),
    "code": ("[[", "]]"),
    "iteration": ("[[", "]]"),
}
DEFAULT_SHAPE = ("[", "]")


def safe_id(node_id: str) -> str:
    """Return a Mermaid-safe identifier for a node ID.

    Mermaid node IDs must start with a letter or underscore. Dify node IDs
    are 13-digit numeric strings, so prefix them with 'n'.
    """
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", node_id)
    if clean and clean[0].isdigit():
        clean = "n" + clean
    return clean


def escape_label(text: str) -> str:
    """Escape characters that break Mermaid node labels."""
    text = text.replace('"', "'")
    text = text.replace("[", "(").replace("]", ")")
    text = text.replace("{", "(").replace("}", ")")
    return text


def node_label(node: dict) -> str:
    """Build the display label for a node: title and type on separate lines."""
    data = node.get("data", {})
    title = data.get("title") or node.get("id", "?")
    node_type = data.get("type", "")
    title = escape_label(str(title))
    return f"{title}<br/>({node_type})"


def build_mermaid(graph: dict) -> str:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    lines = ["flowchart LR"]

    for node in nodes:
        nid = safe_id(node["id"])
        label = node_label(node)
        node_type = node.get("data", {}).get("type", "")
        open_s, close_s = NODE_SHAPES.get(node_type, DEFAULT_SHAPE)
        lines.append(f'    {nid}{open_s}"{label}"{close_s}')

    lines.append("")

    for edge in edges:
        src = safe_id(edge.get("source", ""))
        tgt = safe_id(edge.get("target", ""))
        handle = edge.get("sourceHandle", "source")
        label = EDGE_LABELS.get(handle, "")
        if label:
            lines.append(f'    {src} -->|"{label}"| {tgt}')
        else:
            lines.append(f"    {src} --> {tgt}")

    return "\n".join(lines)


def extract_graph(data: dict) -> dict:
    """Pull the graph object out of the DSL, handling both app types."""
    workflow = data.get("workflow", {})
    graph = workflow.get("graph")
    if graph:
        return graph
    raise ValueError(
        "Could not find workflow.graph in the DSL. "
        "Make sure this is a valid Dify chatflow or workflow YAML."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Mermaid flowchart from a Dify DSL YAML file."
    )
    parser.add_argument("yaml_file", help="Path to the Dify DSL YAML file.")
    args = parser.parse_args()

    try:
        with open(args.yaml_file, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.yaml_file}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse YAML: {exc}", file=sys.stderr)
        sys.exit(1)

    if not data:
        print("ERROR: YAML file is empty.", file=sys.stderr)
        sys.exit(1)

    app_name = data.get("app", {}).get("name", "Untitled")
    app_mode = data.get("app", {}).get("mode", "unknown")

    try:
        graph = extract_graph(data)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))

    print(f"# {app_name}  [{app_mode}]")
    print(f"# {node_count} nodes, {edge_count} edges")
    print()
    print("```mermaid")
    print(build_mermaid(graph))
    print("```")


if __name__ == "__main__":
    main()
