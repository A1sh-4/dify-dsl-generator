"""
Comprehensive pytest suite for scripts/validate_workflow.py

Run from project root with the project venv:
    .venv/Scripts/python -m pytest skills/dify/tests/test_validate_workflow.py -v

Coverage targets every check in validate_workflow.py (checks 1-14).
"""

import sys
import textwrap
import importlib.util
from pathlib import Path
import pytest
import yaml

# ---------------------------------------------------------------------------
# Import the module under test from scripts/
# ---------------------------------------------------------------------------
_SCRIPT = Path(__file__).parent.parent / "scripts" / "validate_workflow.py"
_spec = importlib.util.spec_from_file_location("validate_workflow", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

validate = _mod.validate
find_variable_references = _mod.find_variable_references
_collect_strings = _mod._collect_strings


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _node(id_, type_, extra_data=None, **kwargs):
    """Build a minimal valid node dict."""
    data = {"selected": False, "title": type_.capitalize(), "type": type_}
    if extra_data:
        data.update(extra_data)
    n = {
        "id": id_,
        "type": "custom",
        "height": 54,
        "width": 244,
        "position": {"x": 80, "y": 282},
        "positionAbsolute": {"x": 80, "y": 282},
        "selected": False,
        "sourcePosition": "right",
        "targetPosition": "left",
        "data": data,
    }
    n.update(kwargs)
    return n


def _edge(src, tgt, source_handle="source"):
    """Build a minimal valid edge dict."""
    return {
        "id": f"{src}-{source_handle}-{tgt}-target",
        "source": src,
        "sourceHandle": source_handle,
        "target": tgt,
        "targetHandle": "target",
        "type": "custom",
        "zIndex": 0,
        "data": {"isInLoop": False, "sourceType": "start", "targetType": "end"},
    }


def _valid_workflow() -> dict:
    """Return a minimal fully-valid workflow DSL dict."""
    return {
        "app": {
            "description": "Test",
            "icon": "🤖",
            "icon_background": "#FFEAD5",
            "mode": "workflow",
            "name": "Test Workflow",
            "use_icon_as_answer_icon": False,
        },
        "dependencies": [],
        "kind": "app",
        "version": 0.5,   # will be serialized as 0.5 — use string below
        "workflow": {
            "conversation_variables": [],
            "environment_variables": [],
            "rag_pipeline_variables": [],
            "features": {
                "file_upload": {
                    "fileUploadConfig": {
                        "audio_file_size_limit": 50,
                        "batch_count_limit": 5,
                        "file_size_limit": 15,
                        "image_file_size_limit": 5,
                        "single_chunk_attachment_limit": 10,
                        "video_file_size_limit": 100,
                        "workflow_file_upload_limit": 10,
                    }
                },
                "retriever_resource": {"enabled": False},
                "sensitive_word_avoidance": {"enabled": False},
                "speech_to_text": {"enabled": False},
                "suggested_questions": [],
                "suggested_questions_after_answer": {"enabled": False},
                "text_to_speech": {"enabled": False, "language": "", "voice": ""},
            },
            "graph": {
                "edges": [_edge("n1", "n2")],
                "nodes": [
                    _node("n1", "start"),
                    _node("n2", "end"),
                ],
                "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
            },
        },
    }


def _valid_chatflow() -> dict:
    """Return a minimal valid chatflow DSL dict."""
    d = _valid_workflow()
    d["app"]["mode"] = "advanced-chat"
    # Replace end node with answer node
    d["workflow"]["graph"]["nodes"] = [
        _node("n1", "start"),
        _node("n2", "answer", {"answer": "{{#n1.query#}}"}),
    ]
    return d


def _v(d: dict) -> list:
    """Shorthand: validate dict, return errors."""
    # Round-trip through YAML so version is always a string '0.5.0'
    d["version"] = "0.5.0"
    return validate(d)


# ===========================================================================
# Check 1 — Top-level required keys
# ===========================================================================

class TestTopLevelKeys:
    def test_valid_has_no_errors(self):
        assert _v(_valid_workflow()) == []

    def test_missing_app(self):
        d = _valid_workflow()
        del d["app"]
        errors = _v(d)
        assert any("app" in e for e in errors)

    def test_missing_kind(self):
        d = _valid_workflow()
        del d["kind"]
        errors = _v(d)
        assert any("kind" in e for e in errors)

    def test_missing_version(self):
        d = _valid_workflow()
        del d["version"]
        errors = validate(d)   # call validate() directly — _v() would re-add version
        assert any("version" in e for e in errors)

    def test_missing_workflow(self):
        d = _valid_workflow()
        del d["workflow"]
        errors = _v(d)
        assert any("workflow" in e for e in errors)

    def test_missing_dependencies(self):
        d = _valid_workflow()
        del d["dependencies"]
        errors = _v(d)
        assert any("dependencies" in e for e in errors)

    def test_all_required_keys_present_no_error(self):
        d = _valid_workflow()
        errors = _v(d)
        # No top-level key errors
        assert not any("Missing top-level" in e for e in errors)


# ===========================================================================
# Check 2 — version value
# ===========================================================================

class TestVersion:
    def test_valid_050(self):
        d = _valid_workflow()
        d["version"] = "0.5.0"
        assert validate(d) == []

    def test_valid_060(self):
        d = _valid_workflow()
        d["version"] = "0.6.0"
        assert validate(d) == []

    def test_old_version_013(self):
        d = _valid_workflow()
        d["version"] = "0.1.3"
        errors = validate(d)
        assert any("0.1.3" in e for e in errors)

    def test_wrong_version_1(self):
        d = _valid_workflow()
        d["version"] = "1.0.0"
        errors = validate(d)
        assert any("version" in e.lower() for e in errors)

    def test_quoted_numeric_050_is_valid(self):
        # When YAML round-trips, "0.5.0" stays as string
        d = _valid_workflow()
        d["version"] = "0.5.0"
        assert validate(d) == []


# ===========================================================================
# Check 3 — kind
# ===========================================================================

class TestKind:
    def test_kind_app_is_valid(self):
        d = _valid_workflow()
        assert _v(d) == []

    def test_kind_wrong_value(self):
        d = _valid_workflow()
        d["kind"] = "plugin"
        errors = _v(d)
        assert any("kind" in e for e in errors)


# ===========================================================================
# Check 4 — app.mode
# ===========================================================================

class TestAppMode:
    def test_workflow_mode_valid(self):
        assert _v(_valid_workflow()) == []

    def test_advanced_chat_mode_valid(self):
        assert _v(_valid_chatflow()) == []

    def test_bad_mode(self):
        d = _valid_workflow()
        d["app"]["mode"] = "chat"
        errors = _v(d)
        assert any("app.mode" in e for e in errors)

    def test_missing_mode(self):
        d = _valid_workflow()
        d["app"]["mode"] = None
        errors = _v(d)
        assert any("app.mode" in e for e in errors)


# ===========================================================================
# Check 5 — workflow sub-keys
# ===========================================================================

class TestWorkflowSubKeys:
    def test_missing_conversation_variables(self):
        d = _valid_workflow()
        del d["workflow"]["conversation_variables"]
        errors = _v(d)
        assert any("conversation_variables" in e for e in errors)

    def test_missing_environment_variables(self):
        d = _valid_workflow()
        del d["workflow"]["environment_variables"]
        errors = _v(d)
        assert any("environment_variables" in e for e in errors)

    def test_missing_rag_pipeline_variables(self):
        d = _valid_workflow()
        del d["workflow"]["rag_pipeline_variables"]
        errors = _v(d)
        assert any("rag_pipeline_variables" in e for e in errors)

    def test_missing_features(self):
        d = _valid_workflow()
        del d["workflow"]["features"]
        errors = _v(d)
        assert any("features" in e for e in errors)

    def test_features_not_a_dict(self):
        d = _valid_workflow()
        d["workflow"]["features"] = "bad"
        errors = _v(d)
        assert any("features" in e for e in errors)

    def test_features_present_empty_dict_no_fuc_error(self):
        # Empty features dict is allowed (no fileUploadConfig to validate)
        d = _valid_workflow()
        d["workflow"]["features"] = {}
        errors = _v(d)
        # Should not raise features-missing error
        assert not any("features' is missing" in e for e in errors)

    def test_fileUploadConfig_missing_keys(self):
        d = _valid_workflow()
        # Remove a required fileUploadConfig key
        del d["workflow"]["features"]["file_upload"]["fileUploadConfig"]["audio_file_size_limit"]
        errors = _v(d)
        assert any("audio_file_size_limit" in e for e in errors)

    def test_fileUploadConfig_all_required_present(self):
        assert _v(_valid_workflow()) == []


# ===========================================================================
# Check 6 — graph.viewport
# ===========================================================================

class TestViewport:
    def test_missing_viewport(self):
        d = _valid_workflow()
        del d["workflow"]["graph"]["viewport"]
        errors = _v(d)
        assert any("viewport" in e for e in errors)

    def test_viewport_present_no_error(self):
        assert _v(_valid_workflow()) == []


# ===========================================================================
# Check 7 — nodes
# ===========================================================================

class TestNodes:
    def test_nodes_not_a_list(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = "bad"
        errors = _v(d)
        assert any("nodes" in e for e in errors)

    def test_nodes_empty_list(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = []
        errors = _v(d)
        assert any("empty" in e.lower() for e in errors)

    def test_duplicate_node_ids(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n1", "end"),   # duplicate ID
        ]
        errors = _v(d)
        assert any("Duplicate" in e for e in errors)

    def test_unique_node_ids_no_error(self):
        assert _v(_valid_workflow()) == []


# ===========================================================================
# Check 8 — edges
# ===========================================================================

class TestEdges:
    def test_edges_not_a_list(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["edges"] = "bad"
        errors = _v(d)
        assert any("edges" in e for e in errors)

    def test_edge_source_unknown_node(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["edges"] = [_edge("UNKNOWN", "n2")]
        errors = _v(d)
        assert any("UNKNOWN" in e for e in errors)

    def test_edge_target_unknown_node(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["edges"] = [_edge("n1", "UNKNOWN")]
        errors = _v(d)
        assert any("UNKNOWN" in e for e in errors)

    def test_self_loop_edge(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n1")]
        errors = _v(d)
        assert any("self-loop" in e.lower() for e in errors)

    def test_edge_type_not_custom(self):
        d = _valid_workflow()
        e = _edge("n1", "n2")
        e["type"] = "default"
        d["workflow"]["graph"]["edges"] = [e]
        errors = _v(d)
        assert any("'type' must be 'custom'" in e for e in errors)

    def test_edge_type_custom_no_error(self):
        assert _v(_valid_workflow()) == []

    def test_valid_empty_edges(self):
        # A single-node workflow with no edges — should error on terminal node
        # but not on edges themselves
        d = _valid_workflow()
        d["workflow"]["graph"]["edges"] = []
        errors = _v(d)
        # edges itself is valid; other checks may fire
        assert not any("edges' is missing" in e for e in errors)


# ===========================================================================
# Check 9 — start node required
# ===========================================================================

class TestStartNode:
    def test_no_start_node(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [_node("n1", "llm"), _node("n2", "end")]
        errors = _v(d)
        assert any("start" in e for e in errors)

    def test_start_node_present(self):
        assert _v(_valid_workflow()) == []


# ===========================================================================
# Check 10 — terminal node required
# ===========================================================================

class TestTerminalNode:
    def test_no_end_or_answer(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [_node("n1", "start"), _node("n2", "llm")]
        errors = _v(d)
        assert any("terminal" in e.lower() or "'end'" in e for e in errors)

    def test_end_node_in_workflow(self):
        assert _v(_valid_workflow()) == []

    def test_answer_node_in_chatflow(self):
        assert _v(_valid_chatflow()) == []


# ===========================================================================
# Check 11 — mode / terminal-type consistency
# ===========================================================================

class TestModeConsistency:
    def test_workflow_with_answer_node_only(self):
        d = _valid_workflow()
        # workflow mode but answer node (no end)
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "answer"),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2")]
        errors = _v(d)
        assert any("workflow" in e and "answer" in e for e in errors)

    def test_chatflow_with_end_node_only(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "end"),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2")]
        errors = _v(d)
        assert any("advanced-chat" in e and "end" in e for e in errors)

    def test_workflow_with_end_is_consistent(self):
        assert _v(_valid_workflow()) == []

    def test_chatflow_with_answer_is_consistent(self):
        assert _v(_valid_chatflow()) == []


# ===========================================================================
# Check 12 — variable references
# ===========================================================================

class TestVariableReferences:
    def test_valid_sys_reference(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = "{{#sys.query#}}"
        assert _v(d) == []

    def test_valid_env_reference(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = "{{#env.api_key#}}"
        assert _v(d) == []

    def test_valid_conversation_reference(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = "{{#conversation.history#}}"
        assert _v(d) == []

    def test_valid_node_reference(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = "{{#n1.output#}}"
        assert _v(d) == []

    def test_unknown_node_reference(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = "{{#ghost_node.output#}}"
        errors = _v(d)
        assert any("ghost_node" in e for e in errors)

    def test_multiple_unknown_refs_all_reported(self):
        d = _valid_chatflow()
        d["workflow"]["graph"]["nodes"][1]["data"]["answer"] = (
            "{{#bad1.x#}} and {{#bad2.y#}}"
        )
        errors = _v(d)
        bad_refs = [e for e in errors if "bad1" in e or "bad2" in e]
        assert len(bad_refs) == 2


# ===========================================================================
# Check 13 — conversation_variables entries
# ===========================================================================

class TestConversationVariables:
    def test_valid_conv_var(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {
                "description": "",
                "id": "abc-123",
                "name": "history",
                "selector": ["conversation", "history"],
                "value": None,
                "value_type": "string",
            }
        ]
        assert _v(d) == []

    def test_conv_var_missing_id(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"name": "history", "value_type": "string"}
        ]
        errors = _v(d)
        assert any("'id'" in e for e in errors)

    def test_conv_var_missing_name(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"id": "abc", "value_type": "string"}
        ]
        errors = _v(d)
        assert any("'name'" in e for e in errors)

    def test_conv_var_missing_value_type(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"id": "abc", "name": "history"}
        ]
        errors = _v(d)
        assert any("'value_type'" in e for e in errors)

    def test_conv_var_invalid_value_type(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"id": "abc", "name": "x", "value_type": "list"}
        ]
        errors = _v(d)
        assert any("value_type" in e and "list" in e for e in errors)

    def test_conv_var_valid_array_type(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"id": "abc", "name": "items", "value_type": "array[string]"}
        ]
        assert _v(d) == []

    def test_conv_var_valid_integer_type(self):
        d = _valid_chatflow()
        d["workflow"]["conversation_variables"] = [
            {"id": "abc", "name": "count", "value_type": "integer"}
        ]
        assert _v(d) == []


# ===========================================================================
# Check 14a — code node format
# ===========================================================================

class TestCodeNode:
    def _flow_with_code(self, code_data):
        d = _valid_workflow()
        nodes = [
            _node("n1", "start"),
            _node("n2", "code", code_data),
            _node("n3", "end"),
        ]
        edges = [_edge("n1", "n2"), _edge("n2", "n3")]
        d["workflow"]["graph"]["nodes"] = nodes
        d["workflow"]["graph"]["edges"] = edges
        return d

    def test_valid_code_node_variables_format(self):
        code_data = {
            "code": "def main(x: str) -> dict:\n    return {'out': x}",
            "code_language": "python3",
            "variables": [{"value_selector": ["n1", "query"], "value_type": "string", "variable": "x"}],
            "outputs": {"out": {"children": None, "type": "string"}},
        }
        d = self._flow_with_code(code_data)
        assert _v(d) == []

    def test_old_inputs_format_flagged(self):
        code_data = {
            "code": "def main(x): return {'out': x}",
            "code_language": "python3",
            "inputs": {"x": {"type": "string", "value": "{{#n1.query#}}"}},
            "outputs": {"out": {"children": None, "type": "string"}},
        }
        d = self._flow_with_code(code_data)
        errors = _v(d)
        assert any("inputs" in e and "variables" in e for e in errors)

    def test_output_missing_children_flagged(self):
        code_data = {
            "code": "def main(x: str) -> dict:\n    return {'out': x}",
            "code_language": "python3",
            "variables": [],
            "outputs": {"out": {"type": "string"}},  # missing children
        }
        d = self._flow_with_code(code_data)
        errors = _v(d)
        assert any("children" in e for e in errors)

    def test_output_children_null_no_error(self):
        code_data = {
            "code": "def main() -> dict:\n    return {'out': 'x'}",
            "code_language": "python3",
            "variables": [],
            "outputs": {"out": {"children": None, "type": "string"}},
        }
        d = self._flow_with_code(code_data)
        assert _v(d) == []


# ===========================================================================
# Check 14b — end node outputs use value_type not label
# ===========================================================================

class TestEndNode:
    def test_end_node_with_label_flagged(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "end", {
                "outputs": [
                    {"value_selector": ["n1", "query"], "label": "Result", "variable": "result"}
                ]
            }),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2")]
        errors = _v(d)
        assert any("value_type" in e and "label" in e for e in errors)

    def test_end_node_with_value_type_no_error(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "end", {
                "outputs": [
                    {"value_selector": ["n1", "query"], "value_type": "string", "variable": "result"}
                ]
            }),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2")]
        assert _v(d) == []

    def test_end_node_empty_outputs_no_error(self):
        d = _valid_workflow()
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "end", {"outputs": []}),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2")]
        assert _v(d) == []


# ===========================================================================
# Check 14c — LLM prompt_template entries must have 'id'
# ===========================================================================

class TestLLMNode:
    def _flow_with_llm(self, prompt_template):
        d = _valid_workflow()
        llm_data = {
            "context": {"enabled": False, "variable_selector": []},
            "model": {
                "completion_params": {"max_tokens": 2048, "temperature": 0.7},
                "mode": "chat",
                "name": "claude-sonnet-4-6",
                "provider": "anthropic",
            },
            "prompt_template": prompt_template,
            "selected": False,
            "title": "LLM",
            "type": "llm",
            "vision": {"enabled": False},
        }
        d["workflow"]["graph"]["nodes"] = [
            _node("n1", "start"),
            _node("n2", "llm", llm_data),
            _node("n3", "end"),
        ]
        d["workflow"]["graph"]["edges"] = [_edge("n1", "n2"), _edge("n2", "n3")]
        return d

    def test_prompt_entry_with_id_no_error(self):
        pt = [
            {"id": "uuid-1111", "role": "system", "text": "You are helpful."},
            {"id": "uuid-2222", "role": "user", "text": "{{#n1.query#}}"},
        ]
        assert _v(self._flow_with_llm(pt)) == []

    def test_prompt_entry_missing_id_flagged(self):
        pt = [
            {"role": "system", "text": "You are helpful."},
        ]
        errors = _v(self._flow_with_llm(pt))
        assert any("prompt_template" in e and "id" in e for e in errors)

    def test_prompt_entry_partial_ids_flags_missing(self):
        pt = [
            {"id": "uuid-1111", "role": "system", "text": "You are helpful."},
            {"role": "user", "text": "hello"},  # missing id
        ]
        errors = _v(self._flow_with_llm(pt))
        assert any("prompt_template" in e and "id" in e for e in errors)

    def test_empty_prompt_template_no_error(self):
        assert _v(self._flow_with_llm([])) == []


# ===========================================================================
# Integration — real asset files must all pass
# ===========================================================================

class TestAssetFiles:
    """Smoke-test all asset YAML files against the validator."""

    _ASSETS_ROOT = Path(__file__).parent.parent / "assets"

    def _collect_yamls(self):
        return list(self._ASSETS_ROOT.rglob("*.yml"))

    def test_asset_files_exist(self):
        yamls = self._collect_yamls()
        assert len(yamls) > 0, "No .yml files found under skills/dify/assets/"

    @pytest.mark.parametrize("yml_path", [
        p for p in (Path(__file__).parent.parent / "assets").rglob("*.yml")
    ])
    def test_asset_file_passes_validation(self, yml_path):
        with open(yml_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        assert isinstance(data, dict), f"{yml_path.name} did not parse as a dict"
        errors = validate(data)
        assert errors == [], (
            f"{yml_path.name} failed validation:\n"
            + "\n".join(f"  {e}" for e in errors)
        )


# ===========================================================================
# Helper unit tests — _collect_strings and find_variable_references
# ===========================================================================

class TestHelpers:
    def test_collect_strings_flat(self):
        result = list(_collect_strings({"a": "hello", "b": "world"}))
        assert "hello" in result
        assert "world" in result

    def test_collect_strings_nested(self):
        obj = {"a": {"b": ["x", "y"]}, "c": "z"}
        result = list(_collect_strings(obj))
        assert "x" in result and "y" in result and "z" in result

    def test_collect_strings_ignores_non_strings(self):
        result = list(_collect_strings({"a": 123, "b": None, "c": True}))
        assert result == []

    def test_find_variable_references_basic(self):
        obj = {"text": "Hello {{#node1.output#}} world"}
        refs = find_variable_references(obj)
        assert ("node1", "{{#node1.output#}}") in refs

    def test_find_variable_references_sys_prefix(self):
        obj = {"text": "{{#sys.query#}}"}
        refs = find_variable_references(obj)
        assert ("sys", "{{#sys.query#}}") in refs

    def test_find_variable_references_multiple(self):
        obj = {"text": "{{#n1.out#}} and {{#n2.val#}}"}
        refs = find_variable_references(obj)
        prefixes = {r[0] for r in refs}
        assert "n1" in prefixes
        assert "n2" in prefixes

    def test_find_variable_references_none_in_plain_text(self):
        obj = {"text": "no references here"}
        assert find_variable_references(obj) == []

    def test_find_variable_references_nested(self):
        obj = {"a": {"b": ["{{#n3.field#}}"]}}
        refs = find_variable_references(obj)
        assert any(r[0] == "n3" for r in refs)
