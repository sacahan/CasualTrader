#!/bin/zsh
# ============================================
# Build and Deploy Script for CasualTrader
# ============================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${ZSH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Configuration
DOCKER_IMAGE_NAME="${DOCKER_IMAGE_NAME:-casual-trader}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
DOCKER_USERNAME="${DOCKER_USERNAME:-sacahan}"

# Function to display usage
show_usage() {
    echo "Usage: ./build-and-deploy.sh [OPTIONS]"
    echo ""
    echo "Options (interactive if not provided):"
    echo "  --platform PLATFORM    Select platform: arm64, amd64, or all"
    echo "  --action ACTION        Select action: build, push, or build-push"
    echo "  --no-interactive       Use defaults without prompting"
    echo "  --help                 Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_USERNAME        Docker Hub username (default: sacahan)"
    echo "  DOCKER_IMAGE_NAME      Image name (default: casual-trader)"
    echo "  DOCKER_TAG             Image tag (default: latest)"
}

# Parse command line arguments
PLATFORM=""
ACTION=""
INTERACTIVE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --no-interactive)
            INTERACTIVE=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check required environment variables
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Error: DOCKER_USERNAME environment variable is required"
    echo "Usage: DOCKER_USERNAME=yourusername ./build-and-deploy.sh"
    exit 1
fi

# Interactive selection for platform
if [ -z "$PLATFORM" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "================================================"
    echo "Platform Selection"
    echo "================================================"
    echo "1. arm64 (M1/M2/M3 Mac, ARM servers)"
    echo "2. amd64 (Intel Mac, x86_64 servers)"
    echo "3. all (arm64 + amd64)"
    echo ""
    echo -n "Select platform (1-3) [default: 1]: "
    read platform_choice
    platform_choice=${platform_choice:-1}

    case $platform_choice in
        1) PLATFORM="arm64" ;;
        2) PLATFORM="amd64" ;;
        3) PLATFORM="all" ;;
        *)
            echo "❌ Invalid choice. Using default: arm64"
            PLATFORM="arm64"
            ;;
    esac
elif [ -z "$PLATFORM" ]; then
    PLATFORM="arm64"
fi

# Validate platform choice
case $PLATFORM in
    arm64) PLATFORMS="linux/arm64" ;;
    amd64) PLATFORMS="linux/amd64" ;;
    all)   PLATFORMS="linux/arm64,linux/amd64" ;;
    *)
        echo "❌ Invalid platform: $PLATFORM"
        echo "Valid options: arm64, amd64, all"
        exit 1
        ;;
esac

# Interactive selection for action
if [ -z "$ACTION" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "================================================"
    echo "Action Selection"
    echo "================================================"
    echo "1. build (only build, no push)"
    echo "2. push (only push existing image)"
    echo "3. build-push (build then push) [default]"
    echo ""
    echo -n "Select action (1-3) [default: 3]: "
    read action_choice
    action_choice=${action_choice:-3}

    case $action_choice in
        1) ACTION="build" ;;
        2) ACTION="push" ;;
        3) ACTION="build-push" ;;
        *)
            echo "❌ Invalid choice. Using default: build-push"
            ACTION="build-push"
            ;;
    esac
elif [ -z "$ACTION" ]; then
    ACTION="build-push"
fi

# Validate action choice
case $ACTION in
    build|push|build-push) ;;
    *)
        echo "❌ Invalid action: $ACTION"
        echo "Valid options: build, push, build-push"
        exit 1
        ;;
esac

# Full image name
FULL_IMAGE_NAME="$DOCKER_USERNAME/$DOCKER_IMAGE_NAME:$DOCKER_TAG"

echo ""
echo "================================================"
echo "CasualTrader - Build and Deploy"
echo "================================================"
echo "Image: $FULL_IMAGE_NAME"
echo "Platforms: $PLATFORMS"
echo "Action: $ACTION"
echo "================================================"

# Step 0: Setup Docker buildx for multi-platform builds (required for Mac to build Linux images)
echo ""
echo "⚙️  Step 0: Setting up Docker buildx for multi-platform builds..."
echo "================================================"

BUILDER_NAME="multiarch-builder"

if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    echo "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
    echo "Using existing buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

docker buildx inspect --bootstrap

echo "Registering QEMU multiarch binfmt support (requires Docker privileged mode)..."
docker run --rm --privileged tonistiigi/binfmt:latest --install all || \
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true

echo "✅ Docker buildx setup complete!"

# Step 1: Build Docker Image (if action is build or build-push)
if [ "$ACTION" != "push" ]; then
    echo ""
    echo "🏗️  Step 1: Building Docker image for platforms: $PLATFORMS"
    echo "================================================"

    cd "$PROJECT_ROOT"

    # Determine push flag based on action
    PUSH_FLAG="--load"
    if [ "$ACTION" = "build-push" ]; then
        PUSH_FLAG="--push"
    fi

    docker buildx build \
        --platform "$PLATFORMS" \
        $PUSH_FLAG \
        -t "$FULL_IMAGE_NAME" \
        -f scripts/Dockerfile \
        .

    echo "✅ Docker image built successfully!"
else
    echo ""
    echo "⏭️  Skipping build step (push-only action)"
fi

# Step 2: Push Docker Image (if action is push or build-push)
if [ "$ACTION" != "build" ]; then
    echo ""
    echo "📤 Step 2: Pushing Docker image to registry"
    echo "================================================"

    docker buildx build \
        --platform "$PLATFORMS" \
        --push \
        -t "$FULL_IMAGE_NAME" \
        -f scripts/Dockerfile \
        "$PROJECT_ROOT"

    echo "✅ Docker image pushed successfully!"
else
    echo ""
    echo "⏭️  Skipping push step (build-only action)"
fi
