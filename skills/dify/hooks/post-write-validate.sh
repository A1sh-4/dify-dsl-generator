#!/bin/bash
# post-write-validate.sh
# Automatically validates any YAML file written during /dify skill execution.
# Called by the PostToolCall hook after the Write tool completes.
# Usage: skills/dify/hooks/post-write-validate.sh <file_path>

FILE_PATH="$1"

if [[ "$FILE_PATH" == *.yml ]] || [[ "$FILE_PATH" == *.yaml ]]; then
  echo "=== Auto-validating DSL: $FILE_PATH ==="
  .venv/Scripts/python skills/dify/scripts/validate_workflow.py "$FILE_PATH"
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ DSL validation passed"
  else
    echo "✗ DSL validation failed — see errors above"
    echo "  Run: .venv/Scripts/python skills/dify/scripts/validate_workflow.py \"$FILE_PATH\" to re-check"
  fi
fi
