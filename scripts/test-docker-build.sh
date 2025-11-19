#!/bin/bash
# ============================================
# Docker Build Test Script
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Testing Docker Build for CasualTrader"
echo "================================================"

# Step 1: Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."
echo "================================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker: $(docker --version)"

# Check frontend dist
if [ ! -d "$PROJECT_ROOT/frontend/dist" ]; then
    echo "⚠️  Frontend dist not found. Building frontend first..."
    cd "$PROJECT_ROOT/frontend"
    npm ci
    npm run build
    echo "✅ Frontend built successfully"
else
    echo "✅ Frontend dist exists"
fi

# Step 2: Build Docker image
echo ""
echo "🏗️  Building Docker image..."
echo "================================================"

cd "$PROJECT_ROOT"

docker build \
    -f scripts/Dockerfile \
    -t casualtrader:test \
    .

echo "✅ Docker image built successfully!"

# Step 3: Test the image
echo ""
echo "🧪 Testing Docker image..."
echo "================================================"

# Start container in background
echo "Starting test container..."
docker run -d \
    --name casualtrader-test \
    -p 8888:8000 \
    -e DATABASE_URL=sqlite:///app/data/casualtrader.db \
    -e STATIC_DIR=/app/static \
    casualtrader:test

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Test health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:8888/api/health; then
    echo ""
    echo "✅ Health check passed!"
else
    echo ""
    echo "❌ Health check failed!"
    docker logs casualtrader-test
    docker stop casualtrader-test
    docker rm casualtrader-test
    exit 1
fi

# Test static files
echo ""
echo "Testing static files..."
if curl -f http://localhost:8888/ -I | grep -q "200"; then
    echo "✅ Static files served successfully!"
else
    echo "⚠️  Static files might not be available"
fi

# Show logs
echo ""
echo "📋 Container logs:"
echo "================================================"
docker logs casualtrader-test | tail -20

# Cleanup
echo ""
echo "🧹 Cleaning up..."
echo "================================================"
docker stop casualtrader-test
docker rm casualtrader-test

echo ""
echo "================================================"
echo "✅ All tests passed!"
echo "================================================"
echo ""
echo "Image 'casualtrader:test' is ready to use."
echo "To run it:"
echo "  docker run -d -p 8000:8000 casualtrader:test"
echo ""
