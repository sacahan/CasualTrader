#!/bin/bash
# ============================================
# Build and Deploy Script for CasualTrader
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
DOCKER_IMAGE_NAME="${DOCKER_IMAGE_NAME:-casualtrader}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DOCKER_USERNAME="${DOCKER_USERNAME:-}"

# Full image name
FULL_IMAGE_NAME="$DOCKER_REGISTRY/$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:$DOCKER_TAG"

echo "================================================"
echo "CasualTrader - Build and Deploy"
echo "================================================"
echo "Image: $FULL_IMAGE_NAME"
echo "================================================"

# Check required environment variables
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Error: DOCKER_USERNAME environment variable is required"
    echo "Usage: DOCKER_USERNAME=yourusername ./build-and-deploy.sh"
    exit 1
fi

# Step 1: Build Docker Image
echo ""
echo "🏗️  Step 1: Building Docker image..."
echo "================================================"

cd "$PROJECT_ROOT"

docker build \
    -f scripts/Dockerfile \
    -t "$DOCKER_IMAGE_NAME:$DOCKER_TAG" \
    -t "$FULL_IMAGE_NAME" \
    .

echo "✅ Docker image built successfully!"

# Step 2: Test the image locally (optional)
echo ""
echo "🧪 Step 2: Testing image..."
echo "================================================"

# You can add local testing here if needed
docker images | grep "$DOCKER_IMAGE_NAME"

# Step 3: Login to Docker Registry
echo ""
echo "🔐 Step 3: Logging into Docker registry..."
echo "================================================"

if [ -n "$DOCKER_PASSWORD" ]; then
    echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
else
    echo "Please enter your Docker Hub password:"
    docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME"
fi

echo "✅ Logged in successfully!"

# Step 4: Push to Registry
echo ""
echo "📤 Step 4: Pushing image to registry..."
echo "================================================"

docker push "$FULL_IMAGE_NAME"

echo "✅ Image pushed successfully!"

# Step 5: Generate deployment commands
echo ""
echo "================================================"
echo "✅ Build and Deploy Complete!"
echo "================================================"
echo ""
echo "📋 Deployment Instructions for Ubuntu Server:"
echo ""
echo "1. SSH into your Ubuntu server"
echo ""
echo "2. Pull the image:"
echo "   docker pull $FULL_IMAGE_NAME"
echo ""
echo "3. Stop and remove old container (if exists):"
echo "   docker stop casualtrader 2>/dev/null || true"
echo "   docker rm casualtrader 2>/dev/null || true"
echo ""
echo "4. Run the container:"
echo "   docker run -d \\"
echo "     --name casualtrader \\"
echo "     --restart unless-stopped \\"
echo "     -p 8000:8000 \\"
echo "     -v casualtrader-data:/app/data \\"
echo "     -v casualtrader-logs:/app/logs \\"
echo "     -e DATABASE_URL=sqlite:///app/data/casualtrader.db \\"
echo "     $FULL_IMAGE_NAME"
echo ""
echo "5. Check logs:"
echo "   docker logs -f casualtrader"
echo ""
echo "6. Access the application:"
echo "   http://your-server-ip:8000"
echo ""
echo "================================================"

# Save deployment script
DEPLOY_SCRIPT="$PROJECT_ROOT/scripts/deploy-on-server.sh"
cat > "$DEPLOY_SCRIPT" << EOF
#!/bin/bash
# ============================================
# Deployment Script for Ubuntu Server
# ============================================
set -e

IMAGE="$FULL_IMAGE_NAME"
CONTAINER_NAME="casualtrader"

echo "Pulling latest image..."
docker pull "\$IMAGE"

echo "Stopping existing container..."
docker stop "\$CONTAINER_NAME" 2>/dev/null || true
docker rm "\$CONTAINER_NAME" 2>/dev/null || true

echo "Starting new container..."
docker run -d \\
  --name "\$CONTAINER_NAME" \\
  --restart unless-stopped \\
  -p 8000:8000 \\
  -v casualtrader-data:/app/data \\
  -v casualtrader-logs:/app/logs \\
  -e DATABASE_URL=sqlite:///app/data/casualtrader.db \\
  "\$IMAGE"

echo "Waiting for container to start..."
sleep 5

echo "Checking container status..."
docker ps | grep "\$CONTAINER_NAME"

echo "✅ Deployment complete!"
echo "📋 View logs: docker logs -f \$CONTAINER_NAME"
EOF

chmod +x "$DEPLOY_SCRIPT"

echo "💾 Deployment script saved to: $DEPLOY_SCRIPT"
echo "   Copy this script to your Ubuntu server and run it!"
echo ""
