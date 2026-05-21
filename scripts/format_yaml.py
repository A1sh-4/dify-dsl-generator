"""
format_yaml.py - Reformat a Dify DSL workflow YAML file with consistent indentation.

Usage:
    python format_yaml.py <path/to/workflow.yaml>            # print to stdout
    python format_yaml.py <path/to/workflow.yaml> --inplace  # overwrite the file

The file is loaded with PyYAML and re-emitted with:
  - 2-space indentation
  - Block (non-flow) style for all collections
  - Unicode characters preserved as-is (not escaped)
  - Key order preserved (sort_keys=False)
"""

import argparse
import sys

import yaml


def load_yaml(path: str) -> object:
    """Load and return the parsed contents of a YAML file.

    Raises:
        FileNotFoundError: if the file does not exist.
        yaml.YAMLError:    if the file cannot be parsed.
    """
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def format_yaml(data: object) -> str:
    """Return a reformatted YAML string for *data*.

    Settings:
        default_flow_style=False  — use block style throughout
        allow_unicode=True        — write unicode chars directly (no escaping)
        indent=2                  — 2-space indentation
        sort_keys=False           — preserve original key order
    """
    return yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        indent=2,
        sort_keys=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Reformat a Dify DSL workflow YAML file with 2-space indentation."
    )
    parser.add_argument("yaml_file", help="Path to the YAML file to reformat.")
    parser.add_argument(
        "--inplace", "-i",
        action="store_true",
        help="Overwrite the original file instead of printing to stdout.",
    )
    args = parser.parse_args()

    # Load
    try:
        data = load_yaml(args.yaml_file)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.yaml_file}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse YAML: {exc}", file=sys.stderr)
        sys.exit(1)

    if data is None:
        print("ERROR: YAML file is empty or contains only null.", file=sys.stderr)
        sys.exit(1)

    # Reformat
    formatted = format_yaml(data)

    if args.inplace:
        try:
            with open(args.yaml_file, "w", encoding="utf-8") as fh:
                fh.write(formatted)
            print(f"Reformatted and saved: {args.yaml_file}")
        except OSError as exc:
            print(f"ERROR: Could not write file: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(formatted, end="")


if __name__ == "__main__":
    main()
