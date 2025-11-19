#!/bin/bash
# ============================================
# Backend Build Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "================================================"
echo "Building Backend for CasualTrader"
echo "================================================"

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found, installing..."
    pip install uv
fi

# Install dependencies
echo "📦 Installing backend dependencies..."
uv pip install --system -r pyproject.toml

# Run linting
echo "🔍 Running code quality checks..."
if command -v ruff &> /dev/null; then
    ruff check src/ || echo "⚠️  Linting warnings found"
fi

# Run type checking
echo "🔍 Running type checks..."
if command -v mypy &> /dev/null; then
    mypy src/ || echo "⚠️  Type checking warnings found"
fi

echo "================================================"
echo "Backend build completed successfully!"
echo "================================================"
