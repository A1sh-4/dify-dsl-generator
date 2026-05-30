# post-write-validate.ps1
# Auto-validates any Dify DSL YAML file written during /dify skill execution.
# Registered as a PostToolUse hook in .claude/settings.local.json.
# Receives the Write tool call as JSON on stdin.

param()

try {
    $stdin_content = [Console]::In.ReadToEnd()
    if (-not $stdin_content) { exit 0 }
    $hook_input = $stdin_content | ConvertFrom-Json
} catch {
    exit 0
}

$file_path = $hook_input.tool_input.file_path
if (-not $file_path) { exit 0 }

if ($file_path -notmatch '\.(yml|yaml)$') { exit 0 }

# Only validate files written under the output/ directory to avoid
# accidentally validating asset/template/reference YAML files.
if ($file_path -notmatch '[/\\]output[/\\]') { exit 0 }

Write-Host "=== Auto-validating DSL: $file_path ==="

$venv_python = Join-Path $PSScriptRoot "..\..\..\..\.venv\Scripts\python.exe"
$validate_script = Join-Path $PSScriptRoot "..\scripts\validate_workflow.py"

& $venv_python $validate_script $file_path
$exit_code = $LASTEXITCODE

if ($exit_code -eq 0) {
    Write-Host "✓ DSL validation passed"
} else {
    Write-Host "✗ DSL validation failed — see errors above"
    Write-Host "  Re-run manually: .venv\Scripts\python skills\dify\scripts\validate_workflow.py `"$file_path`""
}
