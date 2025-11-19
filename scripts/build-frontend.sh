#!/bin/bash
# ============================================
# Frontend Build Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "================================================"
echo "Building Frontend for CasualTrader"
echo "================================================"

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm ci

# Build frontend
echo "🏗️  Building frontend..."
npm run build

# Verify build
if [ -d "$FRONTEND_DIR/dist" ]; then
    echo "✅ Frontend build successful!"
    echo "📁 Build output: $FRONTEND_DIR/dist"
    ls -lh "$FRONTEND_DIR/dist"
else
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "================================================"
echo "Frontend build completed successfully!"
echo "================================================"
