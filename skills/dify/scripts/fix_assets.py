"""
fix_assets.py — One-shot script to bring all asset YAML files up to spec.

Fixes applied:
  1. LLM nodes: add 'id' (UUID) to each prompt_template entry missing one
  2. Code nodes: convert old 'inputs' dict to 'variables' list format
  3. Add 'children: null' to code node outputs that are missing it

Run once from project root:
    .venv/Scripts/python skills/dify/scripts/fix_assets.py
"""

import uuid
from pathlib import Path

import yaml

ASSETS_ROOT = Path(__file__).parent.parent / "assets"


def _fix_llm_node(data: dict) -> bool:
    changed = False
    pt = data.get("prompt_template", [])
    if isinstance(pt, list):
        for entry in pt:
            if isinstance(entry, dict) and "id" not in entry:
                entry["id"] = str(uuid.uuid4())
                changed = True
    return changed


def _fix_code_node(data: dict) -> bool:
    changed = False
    # Convert old 'inputs' dict → 'variables' list
    if "inputs" in data and "variables" not in data:
        old_inputs = data.pop("inputs")
        variables = []
        if isinstance(old_inputs, dict):
            for var_name, var_cfg in old_inputs.items():
                # Try to extract value_selector from the value string {{#node.field#}}
                val = var_cfg.get("value", "") if isinstance(var_cfg, dict) else ""
                # Parse {{#node_id.field_name#}}
                import re
                m = re.match(r'\{\{#([^.#]+)\.([^#]+)#\}\}', str(val))
                if m:
                    selector = [m.group(1), m.group(2)]
                else:
                    selector = ["start", var_name]
                variables.append({
                    "value_selector": selector,
                    "value_type": (var_cfg.get("type", "string") if isinstance(var_cfg, dict) else "string"),
                    "variable": var_name,
                })
        data["variables"] = variables
        changed = True

    # Add 'children: null' to outputs missing it
    outputs = data.get("outputs", {})
    if isinstance(outputs, dict):
        for out_name, out_val in outputs.items():
            if isinstance(out_val, dict) and "children" not in out_val:
                out_val["children"] = None
                changed = True
    return changed


def fix_yaml(path: Path) -> bool:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        return False

    changed = False
    nodes = data.get("workflow", {}).get("graph", {}).get("nodes", [])
    for node in nodes:
        if not isinstance(node, dict):
            continue
        ndata = node.get("data", {})
        if not isinstance(ndata, dict):
            continue
        ntype = ndata.get("type")
        if ntype == "llm":
            if _fix_llm_node(ndata):
                changed = True
        elif ntype == "code":
            if _fix_code_node(ndata):
                changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"  FIXED: {path.name}")
    return changed


def main():
    yamls = list(ASSETS_ROOT.rglob("*.yml"))
    print(f"Scanning {len(yamls)} asset files...\n")
    fixed = 0
    for p in yamls:
        if fix_yaml(p):
            fixed += 1
    print(f"\nDone. Fixed {fixed}/{len(yamls)} files.")


if __name__ == "__main__":
    main()
