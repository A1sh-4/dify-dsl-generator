"""
validate_workflow.py — Validate a Dify DSL workflow YAML file.

Based on ground-truth analysis of 12 real Dify exports (skills/dify/assets/).

Usage:
    .venv/Scripts/python skills/dify/scripts/validate_workflow.py <path/to/workflow.yaml> [--verbose]

Exit codes:
    0  All checks passed.
    1  One or more checks failed (errors printed to stdout).
"""

import argparse
import re
import sys

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_strings(obj):
    """Recursively yield every string value in a nested dict/list."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _collect_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _collect_strings(item)


# Matches {{#prefix.rest#}} — captures the prefix (node_id or system prefix)
_VAR_REF_RE = re.compile(r'\{\{#([^.#]+)\.[^#]*#\}\}')

# Dify built-in variable prefixes that are NOT node IDs
_SYSTEM_PREFIXES = {"sys", "env", "conversation"}


def find_variable_references(obj):
    """Return list of (prefix, full_ref) for all {{#prefix.x#}} found in obj."""
    refs = []
    for s in _collect_strings(obj):
        for m in _VAR_REF_RE.finditer(s):
            refs.append((m.group(1), m.group(0)))
    return refs


def _get_node_data_type(node):
    """Return the node type string from either data.type or top-level type."""
    if isinstance(node, dict):
        data = node.get("data", {})
        if isinstance(data, dict):
            t = data.get("type")
            if t:
                return str(t)
        return str(node.get("type", ""))
    return ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(data: dict, verbose: bool = False) -> list:
    """Run all validation checks. Return list of error strings (empty = pass)."""
    errors = []

    # ------------------------------------------------------------------
    # 1. Top-level required keys: app, kind, version, workflow, dependencies
    # ------------------------------------------------------------------
    required_top = {"app", "kind", "version", "workflow"}
    missing_top = required_top - set(data.keys())
    if missing_top:
        errors.append(f"Missing top-level keys: {sorted(missing_top)}")

    if "dependencies" not in data:
        errors.append(
            "'dependencies' key is missing at top level — must be present "
            "(use '[]' if no plugins required)."
        )

    # ------------------------------------------------------------------
    # 2. version must be unquoted 0.5.0 or 0.6.0
    # ------------------------------------------------------------------
    version = data.get("version")
    if version is not None:
        version_str = str(version)
        if version_str not in ("0.5.0", "0.6.0"):
            errors.append(
                f"'version' is '{version_str}' — Dify expects 0.5.0 (unquoted). "
                "Wrong version causes 'caution: different versions' on import."
            )
    else:
        errors.append("'version' is missing.")

    # ------------------------------------------------------------------
    # 3. kind must be 'app'
    # ------------------------------------------------------------------
    kind = data.get("kind")
    if kind is not None and str(kind) != "app":
        errors.append(f"'kind' must be 'app', got '{kind}'.")

    # ------------------------------------------------------------------
    # 4. app block checks
    # ------------------------------------------------------------------
    app = data.get("app")
    if isinstance(app, dict):
        mode = app.get("mode")
        if mode not in ("workflow", "advanced-chat"):
            errors.append(
                f"'app.mode' must be 'workflow' or 'advanced-chat', got '{mode}'."
            )
    elif app is not None:
        errors.append("'app' must be a mapping.")

    # ------------------------------------------------------------------
    # 5. workflow block
    # ------------------------------------------------------------------
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        errors.append("'workflow' is missing or not a mapping — skipping sub-checks.")
        return errors

    # 5a. conversation_variables must be present
    if "conversation_variables" not in workflow:
        errors.append(
            "'workflow.conversation_variables' is missing — must be present "
            "(use '[]' if none). Its absence causes Dify import errors."
        )

    # 5b. environment_variables must be present
    if "environment_variables" not in workflow:
        errors.append(
            "'workflow.environment_variables' is missing — must be present "
            "(use '[]' if none). Its absence causes Dify import errors."
        )

    # 5c. rag_pipeline_variables must be present
    if "rag_pipeline_variables" not in workflow:
        errors.append(
            "'workflow.rag_pipeline_variables' is missing — must be present "
            "(use '[]' if none)."
        )

    # 5d. features must be present and be a dict
    features = workflow.get("features")
    if features is None:
        errors.append(
            "'workflow.features' is missing — its absence causes Dify to crash "
            "with 'An unexpected error occurred while rendering this component'."
        )
    elif not isinstance(features, dict):
        errors.append("'workflow.features' must be a mapping (dict).")
    else:
        # 5d-i. fileUploadConfig must have required keys
        file_upload = features.get("file_upload", {})
        if isinstance(file_upload, dict):
            fuc = file_upload.get("fileUploadConfig")
            if fuc is not None and isinstance(fuc, dict):
                required_fuc_keys = {
                    "audio_file_size_limit",
                    "batch_count_limit",
                    "file_size_limit",
                    "image_file_size_limit",
                    "single_chunk_attachment_limit",
                    "video_file_size_limit",
                    "workflow_file_upload_limit",
                }
                missing_fuc = required_fuc_keys - set(fuc.keys())
                if missing_fuc:
                    errors.append(
                        f"'workflow.features.file_upload.fileUploadConfig' is missing "
                        f"required keys: {sorted(missing_fuc)}"
                    )

    # ------------------------------------------------------------------
    # 6. graph block
    # ------------------------------------------------------------------
    graph = workflow.get("graph")
    if not isinstance(graph, dict):
        errors.append("'workflow.graph' is missing or not a mapping — skipping node/edge checks.")
        return errors

    # 6a. viewport required
    if "viewport" not in graph:
        errors.append(
            "'workflow.graph.viewport' is missing — must be present as "
            "'{x: 0, y: 0, zoom: 1}'. Its absence causes layout issues."
        )

    # ------------------------------------------------------------------
    # 7. nodes
    # ------------------------------------------------------------------
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        errors.append("'workflow.graph.nodes' is missing or not a list.")
        nodes = []
    elif len(nodes) == 0:
        errors.append("'workflow.graph.nodes' is empty — at least one node is required.")

    node_ids = []
    node_id_set = set()
    node_type_map = {}  # id -> type string

    for node in nodes:
        if not isinstance(node, dict):
            continue
        nid = node.get("id")
        if nid is not None:
            nid_str = str(nid)
            node_ids.append(nid_str)
            node_id_set.add(nid_str)
            node_type_map[nid_str] = _get_node_data_type(node)

    # 7a. Unique node IDs
    seen = {}
    for nid in node_ids:
        seen[nid] = seen.get(nid, 0) + 1
    duplicates = [nid for nid, count in seen.items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate node IDs: {duplicates}")

    # ------------------------------------------------------------------
    # 8. edges
    # ------------------------------------------------------------------
    edges = graph.get("edges")
    if not isinstance(edges, list):
        errors.append("'workflow.graph.edges' is missing or not a list.")
        edges = []

    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"Edge[{i}] is not a mapping.")
            continue
        src = str(edge.get("source", ""))
        tgt = str(edge.get("target", ""))

        if src and src not in node_id_set:
            errors.append(f"Edge[{i}] source '{src}' references unknown node ID.")
        if tgt and tgt not in node_id_set:
            errors.append(f"Edge[{i}] target '{tgt}' references unknown node ID.")
        if src and tgt and src == tgt:
            errors.append(f"Edge[{i}] is a self-loop (source == target == '{src}').")

        # 8a. edge type must be 'custom'
        edge_type = edge.get("type")
        if edge_type is not None and str(edge_type) != "custom":
            errors.append(f"Edge[{i}] 'type' must be 'custom', got '{edge_type}'.")

    # ------------------------------------------------------------------
    # 9. At least one entry node (start, or a trigger node for workflows)
    # ------------------------------------------------------------------
    node_types = list(node_type_map.values())
    entry_node_types = {"start", "trigger-schedule", "trigger-webhook"}
    if not entry_node_types.intersection(node_types):
        errors.append(
            "No entry node found - every flow needs a 'start' node "
            "(or a 'trigger-schedule' / 'trigger-webhook' entry node for workflows)."
        )

    # ------------------------------------------------------------------
    # 10. At least one terminal node (end or answer)
    # ------------------------------------------------------------------
    if "end" not in node_types and "answer" not in node_types:
        errors.append(
            "No terminal node ('end' or 'answer') found. "
            "Workflows need 'end'; chatflows need 'answer'."
        )

    # ------------------------------------------------------------------
    # 11. Mode/terminal-type consistency
    # ------------------------------------------------------------------
    if isinstance(app, dict):
        mode = app.get("mode")
        if mode == "workflow" and "answer" in node_types and "end" not in node_types:
            errors.append(
                "App mode is 'workflow' but only 'answer' node found — "
                "workflows must use 'end' nodes, not 'answer'."
            )
        if mode == "advanced-chat" and "end" in node_types and "answer" not in node_types:
            errors.append(
                "App mode is 'advanced-chat' but only 'end' node found — "
                "chatflows must use 'answer' nodes, not 'end'."
            )

    # ------------------------------------------------------------------
    # 12. Variable references use known node IDs or system prefixes
    # ------------------------------------------------------------------
    bad_refs = []
    for prefix, full_ref in find_variable_references(data):
        if prefix in _SYSTEM_PREFIXES:
            continue
        if prefix not in node_id_set:
            bad_refs.append((prefix, full_ref))
    for prefix, full_ref in bad_refs:
        errors.append(
            f"Variable reference {full_ref!r} uses unknown node/prefix '{prefix}'."
        )

    # ------------------------------------------------------------------
    # 13. conversation_variables entries have required fields
    # ------------------------------------------------------------------
    conv_vars = workflow.get("conversation_variables", [])
    if isinstance(conv_vars, list):
        valid_cv_types = {
            "string", "number", "integer", "boolean",
            "array[string]", "array[object]", "array[number]",
        }
        for idx, cv in enumerate(conv_vars):
            if not isinstance(cv, dict):
                errors.append(f"conversation_variables[{idx}] is not a mapping.")
                continue
            for field in ("id", "name", "value_type"):
                if field not in cv:
                    errors.append(
                        f"conversation_variables[{idx}] missing required field '{field}'."
                    )
            vt = cv.get("value_type")
            if vt and vt not in valid_cv_types:
                errors.append(
                    f"conversation_variables[{idx}] 'value_type' is '{vt}' — "
                    f"must be one of: {sorted(valid_cv_types)}."
                )

    # ------------------------------------------------------------------
    # 14. Code nodes must use 'variables' not 'inputs'
    # ------------------------------------------------------------------
    for node in nodes:
        if not isinstance(node, dict):
            continue
        ndata = node.get("data", {})
        if not isinstance(ndata, dict):
            continue
        ntype = ndata.get("type")
        nid = node.get("id", "?")

        if ntype == "code":
            if "inputs" in ndata and "variables" not in ndata:
                errors.append(
                    f"Code node '{nid}' uses old 'inputs' dict format — "
                    "must use 'variables' list with value_selector entries."
                )
            # Check outputs use the dict/mapping format Dify actually produces (ground truth):
            #   outputs:
            #     var_name:
            #       type: string      # one of the 7 valid code-output types
            #       children: null    # always null for code-node outputs
            # NOTE: only CODE-node outputs are a dict. END-node outputs are a list
            # (handled separately by check 14b) - do not conflate the two.
            outputs = ndata.get("outputs")
            if outputs is not None:
                valid_out_types = {
                    "string", "number", "boolean", "object",
                    "array[string]", "array[number]", "array[object]",
                }
                if isinstance(outputs, list):
                    errors.append(
                        f"Code node '{nid}' outputs use the old list format - "
                        "must be a dict/mapping keyed by variable name, each value a "
                        "mapping with 'type:' and 'children:' (children: null)."
                    )
                elif isinstance(outputs, dict):
                    for var_name, spec in outputs.items():
                        if not isinstance(spec, dict):
                            errors.append(
                                f"Code node '{nid}' output '{var_name}' must be a mapping "
                                "with 'type:' and 'children:' fields."
                            )
                            continue
                        out_type = spec.get("type")
                        if out_type is None:
                            errors.append(
                                f"Code node '{nid}' output '{var_name}' is missing 'type:'."
                            )
                        elif str(out_type) not in valid_out_types:
                            errors.append(
                                f"Code node '{nid}' output '{var_name}' has invalid type "
                                f"'{out_type}' - must be one of: string, number, boolean, "
                                "object, array[string], array[number], array[object]."
                            )
                        if "children" not in spec:
                            errors.append(
                                f"Code node '{nid}' output '{var_name}' is missing 'children:' - "
                                "use 'children: null' for code-node outputs."
                            )
                else:
                    errors.append(
                        f"Code node '{nid}' outputs must be a dict/mapping keyed by "
                        "variable name (with 'type:' and 'children:' per entry)."
                    )

        # 14b. End node outputs must use value_type not label
        if ntype == "end":
            out_list = ndata.get("outputs", [])
            if isinstance(out_list, list):
                for oi, out_entry in enumerate(out_list):
                    if isinstance(out_entry, dict):
                        if "label" in out_entry and "value_type" not in out_entry:
                            errors.append(
                                f"End node '{nid}' output[{oi}] uses 'label' — "
                                "must use 'value_type' (e.g. value_type: string)."
                            )

        # 14c. LLM prompt_template entries should have 'id' field
        if ntype == "llm":
            prompt_template = ndata.get("prompt_template", [])
            if isinstance(prompt_template, list):
                for pi, entry in enumerate(prompt_template):
                    if isinstance(entry, dict) and "id" not in entry:
                        errors.append(
                            f"LLM node '{nid}' prompt_template[{pi}] is missing "
                            "'id' field (UUID required by Dify)."
                        )

    if verbose and not errors:
        print("All checks passed.")

    return errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Windows consoles default to cp932; force UTF-8 so non-ASCII in messages
    # (em-dashes in existing checks, Japanese node titles, etc.) never crash on print.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(
        description="Validate a Dify DSL workflow YAML file."
    )
    parser.add_argument("yaml_file", help="Path to the workflow YAML file.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print detailed progress.")
    args = parser.parse_args()

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
        print(f"\nFAIL - {len(errors)} error(s):\n")
        for err in errors:
            print(f"  [ERROR] {err}")
        sys.exit(1)

    graph = data.get("workflow", {}).get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    mode = data.get("app", {}).get("mode", "unknown") if isinstance(data.get("app"), dict) else "unknown"
    print(f"\nPASS - {len(nodes)} node(s), {len(edges)} edge(s), mode: {mode}")
    sys.exit(0)


if __name__ == "__main__":
    main()
