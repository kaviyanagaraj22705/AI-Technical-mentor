#Requires: -Version 5.1
$ErrorActionPreference = "Stop"

$PROJECT_DIR = "C:\Users\HP\Documents\visualstudiocode\AI_Technical_Mentor"
$VENV_ACTIVATE = Join-Path $PROJECT_DIR ".venv\Scripts\Activate.ps1"

Write-Host "AI Technical Learning Mentor" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

if (-Not (Test-Path $VENV_ACTIVATE)) {
    Write-Error "Virtual environment not found at $VENV_ACTIVATE"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& $VENV_ACTIVATE

if (-Not (Get-Command streamlit -ErrorAction SilentlyContinue)) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r "$PROJECT_DIR\requirements.txt"
}

Write-Host "Starting Streamlit app..." -ForegroundColor Green
streamlit run "$PROJECT_DIR\app.py"
