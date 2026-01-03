# Quick Start Script for MethaneWatch India

Write-Host "🛰️  MethaneWatch India - Quick Start" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "✓ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠ Virtual environment not active. Activating..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan

# Check if key packages are installed
$packages = @("streamlit", "geopandas", "earthaccess", "xarray")
$missing = @()

foreach ($pkg in $packages) {
    $installed = pip show $pkg 2>$null
    if ($installed) {
        Write-Host "  ✓ $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $pkg missing" -ForegroundColor Red
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠ Missing packages detected. Installing..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "🌍 Project Structure:" -ForegroundColor Cyan
Write-Host "  • app.py                    - Main dashboard"
Write-Host "  • src/emit_fetcher.py       - NASA EMIT data"
Write-Host "  • src/climate_trace_fetcher - Climate TRACE API"
Write-Host "  • src/esg_report_generator  - ESG compliance"
Write-Host "  • data/india_facilities.csv - Verified facilities"
Write-Host ""

Write-Host "🚀 Launching Streamlit Dashboard..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit
streamlit run app.py
