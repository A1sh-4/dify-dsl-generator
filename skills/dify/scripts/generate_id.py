"""
generate_id.py - Utilities for generating Dify DSL node and edge IDs.

Naming Convention:
  - Node IDs: millisecond-precision Unix timestamps as strings (e.g. "1716300000000").
    Using timestamps makes IDs unique across sessions without requiring a UUID library,
    and the numeric ordering reflects creation order.
  - Edge IDs: composed of the source node ID, the output handle name, and the target
    node ID joined with hyphens, with "-target" appended as a suffix.
    Format: "<source_id>-<handle>-<target_id>-target"
    Common handles: source (default/unconditional), true/false (if-else branches),
    success-branch / fail-branch (tool/code node outcomes).
"""

import time


def generate_node_id() -> str:
    """Return a unique node ID based on the current millisecond timestamp."""
    return str(int(time.time() * 1000))


def generate_edge_id(source_id: str, handle: str, target_id: str) -> str:
    """Return an edge ID in the standard Dify DSL format.

    Args:
        source_id: The ID of the source node.
        handle:    The output handle on the source node (e.g. "source", "true",
                   "false", "success-branch", "fail-branch").
        target_id: The ID of the target node.

    Returns:
        A string of the form "<source_id>-<handle>-<target_id>-target".
    """
    return f"{source_id}-{handle}-{target_id}-target"


if __name__ == "__main__":
    node_id = generate_node_id()
    print(f"Sample node ID : {node_id}")
    print()

    # Demonstrate edge IDs for all common handle types
    target_id = generate_node_id()
    handles = ["source", "true", "false", "success-branch", "fail-branch"]
    print("Example edge IDs:")
    for handle in handles:
        edge_id = generate_edge_id(node_id, handle, target_id)
        print(f"  handle={handle!r:20s}  ->  {edge_id}")
