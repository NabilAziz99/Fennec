#!/bin/bash
# Fennec Linux Docker Image Rebuild Script
#
# Usage:
#   ./rebuild_image.sh          # Normal rebuild (uses cache)
#   ./rebuild_image.sh --force  # Force rebuild (no cache)
#   ./rebuild_image.sh --clean  # Remove image and rebuild fresh
#   ./rebuild_image.sh --status # Show current image status

set -e

IMAGE_NAME="fennec-linux:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_DIR="$SCRIPT_DIR/linux"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_status() {
    echo ""
    echo "=== Fennec Linux Docker Image Status ==="
    echo ""

    if docker image inspect "$IMAGE_NAME" &>/dev/null; then
        print_success "Image exists: $IMAGE_NAME"
        echo ""
        echo "Image details:"
        docker image inspect "$IMAGE_NAME" --format '  ID: {{.Id}}'
        docker image inspect "$IMAGE_NAME" --format '  Created: {{.Created}}'
        docker image inspect "$IMAGE_NAME" --format '  Size: {{.Size}} bytes'
        echo ""
        echo "Running containers using this image:"
        docker ps --filter "ancestor=$IMAGE_NAME" --format "  {{.ID}} - {{.Names}} ({{.Status}})" || echo "  None"
    else
        print_warning "Image does not exist: $IMAGE_NAME"
    fi
    echo ""
}

stop_containers() {
    print_status "Stopping any running containers using $IMAGE_NAME..."
    containers=$(docker ps -q --filter "ancestor=$IMAGE_NAME" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        docker stop $containers
        print_success "Stopped containers"
    else
        print_status "No running containers to stop"
    fi
}

remove_image() {
    print_status "Removing existing image $IMAGE_NAME..."
    if docker image inspect "$IMAGE_NAME" &>/dev/null; then
        docker rmi -f "$IMAGE_NAME"
        print_success "Image removed"
    else
        print_status "Image doesn't exist, nothing to remove"
    fi
}

build_image() {
    local no_cache=""
    if [ "$1" == "--no-cache" ]; then
        no_cache="--no-cache"
        print_status "Building with --no-cache (forced fresh build)..."
    else
        print_status "Building image (using cache)..."
    fi

    cd "$LINUX_DIR"
    docker build $no_cache -t "$IMAGE_NAME" .
    print_success "Image built successfully: $IMAGE_NAME"
}

# Main
case "${1:-}" in
    --status)
        show_status
        ;;
    --force)
        echo ""
        echo "=== Force Rebuilding Fennec Linux Image (no cache) ==="
        echo ""
        stop_containers
        build_image --no-cache
        show_status
        ;;
    --clean)
        echo ""
        echo "=== Clean Rebuild Fennec Linux Image ==="
        echo ""
        stop_containers
        remove_image
        build_image --no-cache
        show_status
        ;;
    --help|-h)
        echo "Fennec Linux Docker Image Rebuild Script"
        echo ""
        echo "Usage:"
        echo "  $0              Normal rebuild (uses Docker cache)"
        echo "  $0 --force      Force rebuild without cache"
        echo "  $0 --clean      Remove image completely and rebuild fresh"
        echo "  $0 --status     Show current image status"
        echo "  $0 --help       Show this help"
        echo ""
        ;;
    "")
        echo ""
        echo "=== Rebuilding Fennec Linux Image ==="
        echo ""
        stop_containers
        build_image
        show_status
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
