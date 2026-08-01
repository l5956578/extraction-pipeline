# Launch soft-issue inspector on http://127.0.0.1:8765/
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
$py = "D:\y\lang-platform\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $PSScriptRoot "app.py") @args
