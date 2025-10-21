#!/bin/bash
# Linux/Mac startup script
# Usage: ./start.sh

set -e

echo "🚀 NewsInsight.ai Startup Script"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "✓ Virtual environment exists"
echo ""

# Activate venv
source venv/bin/activate
echo "✓ Activated venv"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Set defaults if not set
export AWS_REGION="${AWS_REGION:-us-west-2}"
export DDB_TABLE="${DDB_TABLE:-news_metadata}"
export DEBUG_MODE="${DEBUG_MODE:-false}"

echo "⚙️  Configuration:"
echo "   AWS_REGION: $AWS_REGION"
echo "   DDB_TABLE: $DDB_TABLE"
echo "   DEBUG_MODE: $DEBUG_MODE"
echo ""

# Check if data exists
echo "🔍 Checking for sample data..."
if python3 -c "import boto3; table = boto3.resource('dynamodb', region_name='$AWS_REGION').Table('$DDB_TABLE'); print(table.item_count)" &> /dev/null; then
    count=$(python3 -c "import boto3; table = boto3.resource('dynamodb', region_name='$AWS_REGION').Table('$DDB_TABLE'); print(table.item_count)" 2>/dev/null || echo "0")
    if [ "$count" -eq 0 ]; then
        echo "⚠️  No articles found in DDB"
        echo "    Run: python scripts/insert_sample_data.py insert"
        echo ""
    else
        echo "✓ Found $count articles"
        echo ""
    fi
fi

# Start Streamlit
echo "🎯 Starting Streamlit app..."
echo "    Open: http://localhost:8501"
echo "    Press Ctrl+C to stop"
echo ""

streamlit run app.py
