#!/usr/bin/env bash
# HoReCa Market Intelligence & POS Dashboard - Pipeline Refresh Script (Bash)
# Execution: bash refresh_data.sh

set -e

echo "=========================================================="
echo " STARTING FULL DATA PIPELINE REFRESH "
echo "=========================================================="

# 1. Run Playwright Scrapers for competitor menus
echo ""
echo "[1/4] Running Playwright scrapers for competitor menus..."
node index.js

# 2. Run LangGraph Gemini AI Classification Agent
echo ""
echo "[2/4] Running LangGraph Gemini AI Classification Agent..."
if [ -d ".venv/Scripts" ]; then
    ./.venv/Scripts/python agent/classify_agent.py
else
    ./.venv/bin/python agent/classify_agent.py
fi

# 3. Generate Own Restaurant Menu (restaurant_classified.csv)
echo ""
echo "[3/4] Generating own restaurant menu..."
if [ -d ".venv/Scripts" ]; then
    ./.venv/Scripts/python scripts/generate_own_restaurant_menu.py
else
    ./.venv/bin/python scripts/generate_own_restaurant_menu.py
fi

# 4. Generate Internal POS Transactions (pos_orders.csv, pos_order_items.csv, pos_transactions_flat.csv)
echo ""
echo "[4/4] Generating internal POS transactions..."
if [ -d ".venv/Scripts" ]; then
    ./.venv/Scripts/python scripts/generate_pos_transactions.py
else
    ./.venv/bin/python scripts/generate_pos_transactions.py
fi

echo ""
echo "=========================================================="
echo " SUCCESS: ALL 5 CSV FILES REFRESHED IN data/processed/! "
echo "=========================================================="
