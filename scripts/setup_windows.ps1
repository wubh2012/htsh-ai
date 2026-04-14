<#
Windows PowerShell helper to setup the project's Python virtualenv and install dependencies.

Usage:
  .\scripts\setup_windows.ps1          # create venv and install requirements
  .\scripts\setup_windows.ps1 -RunApp # also run the app
  .\scripts\setup_windows.ps1 -RunTests # run pytest after installing deps
#>

param(
    [switch]$RunApp,
    [switch]$RunTests
)

$ErrorActionPreference = 'Stop'

$venv = ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment in $venv..."
    python -m venv $venv
} else {
    Write-Host "Virtual environment already exists: $venv"
}

$py = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Error "Python in venv not found at $py"
    exit 1
}

Start-Process -FilePath $py -ArgumentList '-m','pip','install','--upgrade','pip' -NoNewWindow -Wait

if (Test-Path "contract_audit\requirements.txt") {
    Write-Host "Installing requirements from contract_audit/requirements.txt..."
    Start-Process -FilePath $py -ArgumentList '-m','pip','install','-r','contract_audit\\requirements.txt' -NoNewWindow -Wait
} elseif (Test-Path "requirements.txt") {
    Write-Host "Installing requirements from requirements.txt..."
    Start-Process -FilePath $py -ArgumentList '-m','pip','install','-r','requirements.txt' -NoNewWindow -Wait
} else {
    Write-Host "No requirements file found. You can edit this script to point to the correct requirements file."
}

if ($RunTests) {
    Write-Host "Running tests..."
    Start-Process -FilePath $py -ArgumentList '-m','pytest','-q' -NoNewWindow -Wait
}

if ($RunApp) {
    Write-Host "Starting application (contract_audit/main.py)..."
    Push-Location contract_audit
    Start-Process -FilePath $py -ArgumentList 'main.py' -NoNewWindow -Wait
    Pop-Location
}

Write-Host "Setup script finished. To activate the venv in PowerShell run: .\\.venv\\Scripts\\Activate.ps1"
