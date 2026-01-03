# CO2Watch India - Quick Start Script

Write-Host "🌍 CO2Watch India - Quick Start" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "✓ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠ Virtual environment not active. Checking for .venv..." -ForegroundColor Yellow
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        .\.venv\Scripts\Activate.ps1
    } else {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
    }
}

Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan

# Check if key packages are installed
$packages = @("streamlit", "earthengine-api", "geemap", "pandas", "pydeck")
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
Write-Host "  • app.py                         - Streamlit dashboard"
Write-Host "  • authenticate.py                - GEE authentication"
Write-Host "  • src/ingestion/tropomi_fetcher  - TROPOMI data via GEE"
Write-Host "  • src/processing/detect_plumes   - Plume detection algorithm"
Write-Host "  • data/plants/*.csv              - Thermal plant database"
Write-Host "  • config/target_plant.yaml       - Target plant config"
Write-Host ""

# Check GEE authentication
Write-Host "🔐 Checking Earth Engine authentication..." -ForegroundColor Cyan
$geeTest = python -c "import ee; ee.Initialize(); print('OK')" 2>&1
if ($geeTest -like "*OK*") {
    Write-Host "  ✓ Earth Engine authenticated" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Earth Engine not authenticated" -ForegroundColor Yellow
    Write-Host "  Run: python authenticate.py" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Launching CO2Watch Dashboard..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will open at: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Run Streamlit
streamlit run app.py
