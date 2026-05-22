"""
validate_workflow.py - Validate a Dify DSL workflow YAML file.

Usage:
    python validate_workflow.py <path/to/workflow.yaml> [--verbose]

Exit codes:
    0  All validation checks passed.
    1  One or more validation checks failed (errors printed to stdout).
"""

import argparse
import re
import sys

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_strings(obj):
    """Recursively yield every string value found in a nested dict/list."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _collect_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _collect_strings(item)


_VAR_REF_RE = re.compile(r'\{\{#([^.#]+)\.[^#]+#\}\}')


def find_variable_references(obj):
    """Return a list of (node_id, full_ref) tuples found in all string values."""
    refs = []
    for s in _collect_strings(obj):
        for m in _VAR_REF_RE.finditer(s):
            refs.append((m.group(1), m.group(0)))
    return refs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(data: dict, verbose: bool) -> list:
    """Run all validation checks and return a list of error strings."""
    errors = []

    # ------------------------------------------------------------------
    # 1. Top-level required keys
    # ------------------------------------------------------------------
    required_top = {"app", "kind", "version", "workflow"}
    missing_top = required_top - set(data.keys())
    if missing_top:
        errors.append(f"Missing top-level keys: {sorted(missing_top)}")

    # ------------------------------------------------------------------
    # 2. workflow.graph exists
    # ------------------------------------------------------------------
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        errors.append("'workflow' is missing or not a mapping — skipping graph checks.")
        return errors  # Cannot proceed without workflow

    graph = workflow.get("graph")
    if not isinstance(graph, dict):
        errors.append("'workflow.graph' is missing or not a mapping — skipping node/edge checks.")
        return errors  # Cannot proceed without graph

    # ------------------------------------------------------------------
    # 3. workflow.graph.nodes is a non-empty list
    # ------------------------------------------------------------------
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        errors.append("'workflow.graph.nodes' is missing or not a list.")
        nodes = []
    elif len(nodes) == 0:
        errors.append("'workflow.graph.nodes' is empty — at least one node is required.")

    # ------------------------------------------------------------------
    # 4. workflow.graph.edges is a list
    # ------------------------------------------------------------------
    edges = graph.get("edges")
    if not isinstance(edges, list):
        errors.append("'workflow.graph.edges' is missing or not a list.")
        edges = []

    # Build a map from node id -> node for subsequent checks
    node_ids = []
    node_id_set = set()
    for node in nodes:
        if isinstance(node, dict):
            nid = node.get("id")
            if nid is not None:
                node_ids.append(nid)
                node_id_set.add(str(nid))

    # ------------------------------------------------------------------
    # 5. All node IDs are unique
    # ------------------------------------------------------------------
    seen_ids = {}
    for nid in node_ids:
        key = str(nid)
        seen_ids[key] = seen_ids.get(key, 0) + 1
    duplicates = [nid for nid, count in seen_ids.items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate node IDs found: {duplicates}")

    # ------------------------------------------------------------------
    # 6 & 7. Every edge source/target references an existing node ID
    # 8. No self-loop edges
    # ------------------------------------------------------------------
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"Edge at index {i} is not a mapping.")
            continue

        src = str(edge.get("source", ""))
        tgt = str(edge.get("target", ""))

        if src and src not in node_id_set:
            errors.append(
                f"Edge[{i}] source '{src}' does not reference an existing node ID."
            )
        if tgt and tgt not in node_id_set:
            errors.append(
                f"Edge[{i}] target '{tgt}' does not reference an existing node ID."
            )
        if src and tgt and src == tgt:
            errors.append(
                f"Edge[{i}] is a self-loop (source == target == '{src}')."
            )

    # ------------------------------------------------------------------
    # 9. workflow.environment_variables must be present (list)
    # ------------------------------------------------------------------
    if "environment_variables" not in workflow:
        errors.append(
            "'workflow.environment_variables' is missing - must be present as [] even if empty. "
            "Its absence causes Dify to crash with 'An unexpected error occurred while rendering this component'."
        )

    # ------------------------------------------------------------------
    # 10. workflow.features must be present (not missing, not null)
    # ------------------------------------------------------------------
    features = workflow.get("features")
    if features is None:
        errors.append(
            "'workflow.features' is missing - must be present with at least file_upload, retriever_resource, etc. "
            "Its absence causes Dify to crash with 'An unexpected error occurred while rendering this component'."
        )
    elif not isinstance(features, dict):
        errors.append("'workflow.features' must be a mapping (dict), not a scalar value.")

    # ------------------------------------------------------------------
    # 12. At least one node with type 'start'
    # ------------------------------------------------------------------
    node_types = [
        str(node.get("data", {}).get("type", node.get("type", "")))
        for node in nodes
        if isinstance(node, dict)
    ]
    if "start" not in node_types:
        errors.append("No node with type 'start' found — a workflow must have a start node.")

    # ------------------------------------------------------------------
    # 13. At least one node with type 'end' or 'answer'
    # ------------------------------------------------------------------
    if "end" not in node_types and "answer" not in node_types:
        errors.append(
            "No node with type 'end' or 'answer' found — "
            "a workflow must have a terminal node."
        )

    # ------------------------------------------------------------------
    # 14. Variable references use existing node IDs
    # ------------------------------------------------------------------
    bad_refs = []
    for ref_node_id, full_ref in find_variable_references(data):
        if ref_node_id not in node_id_set:
            bad_refs.append((ref_node_id, full_ref))

    if bad_refs:
        for ref_node_id, full_ref in bad_refs:
            errors.append(
                f"Variable reference {full_ref!r} uses unknown node ID '{ref_node_id}'."
            )

    if verbose and not errors:
        print("All checks passed — no issues found.")

    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate a Dify DSL workflow YAML file."
    )
    parser.add_argument("yaml_file", help="Path to the workflow YAML file.")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress information.",
    )
    args = parser.parse_args()

    # Load file
    try:
        with open(args.yaml_file, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.yaml_file}")
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse YAML: {exc}")
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: YAML root must be a mapping (dict).")
        sys.exit(1)

    if args.verbose:
        print(f"Loaded: {args.yaml_file}")

    errors = validate(data, verbose=args.verbose)

    if errors:
        print(f"\nFAIL - {len(errors)} error(s) found:\n")
        for err in errors:
            print(f"  [ERROR] {err}")
        sys.exit(1)

    # Build summary from validated data
    graph = data.get("workflow", {}).get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    app_mode = data.get("app", {}).get("mode", "unknown") if isinstance(data.get("app"), dict) else "unknown"

    print(
        f"\nPASS - {len(nodes)} node(s), {len(edges)} edge(s), app mode: {app_mode}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
