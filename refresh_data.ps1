# HoReCa Market Intelligence & POS Dashboard - Pipeline Refresh Script (PowerShell)
# This script runs all scraper and data processing steps to refresh all 5 CSV files.

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " STARTING FULL DATA PIPELINE REFRESH " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Run Playwright Scrapers for competitor menus
Write-Host "`n[1/4] Running Playwright scrapers for competitor menus..." -ForegroundColor Yellow
node index.js
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to run Playwright scrapers."
    exit 1
}

# 2. Run LangGraph Gemini AI Classification Agent
Write-Host "`n[2/4] Running LangGraph Gemini AI Classification Agent..." -ForegroundColor Yellow
.\.venv\Scripts\python agent/classify_agent.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to classify competitor items with LangGraph."
    exit 1
}

# 3. Generate Own Restaurant Menu (restaurant_classified.csv)
Write-Host "`n[3/4] Generating own restaurant menu..." -ForegroundColor Yellow
.\.venv\Scripts\python scripts/generate_own_restaurant_menu.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate own restaurant menu."
    exit 1
}

# 4. Generate Internal POS Transactions (pos_orders.csv, pos_order_items.csv, pos_transactions_flat.csv)
Write-Host "`n[4/4] Generating internal POS transactions..." -ForegroundColor Yellow
.\.venv\Scripts\python scripts/generate_pos_transactions.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate POS transactions."
    exit 1
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS: ALL 5 CSV FILES REFRESHED IN data/processed/! " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
