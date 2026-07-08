Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "FOREX AI LAB - Windows PowerShell launcher"
Write-Host "If PowerShell blocks this script because of execution policy, use START_WINDOWS.bat or run:"
Write-Host "powershell -ExecutionPolicy Bypass -File .\START_WINDOWS.ps1"
Write-Host ""

try {
    $python = Get-Command python -ErrorAction Stop
} catch {
    Write-Host "Python was not found. Install Python 3.11+ and enable Add Python to PATH."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating local virtual environment..."
    & $python.Source -m venv .venv
}

$activate = Join-Path $PWD ".venv\Scripts\Activate.ps1"
try {
    . $activate
} catch {
    Write-Host "Could not activate .venv in PowerShell. This is often caused by execution policy."
    Write-Host "Use START_WINDOWS.bat, or run PowerShell with: powershell -ExecutionPolicy Bypass -File .\START_WINDOWS.ps1"
    Read-Host "Press Enter to exit"
    exit 1
}

python -m pip install -r requirements.txt
python run_menu.py

Write-Host ""
Read-Host "Launcher finished. Press Enter to close this window"
