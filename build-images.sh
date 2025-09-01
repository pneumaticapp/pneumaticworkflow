#!/bin/bash

# Pneumatic Docker Images Build Script
# This script builds and pushes Docker images for backend and frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_IMAGE="realm74/pneumatic-backend"
FRONTEND_IMAGE="realm74/pneumatic-frontend"
VERSION=${1:-latest}

echo -e "${BLUE}🚀 Pneumatic Docker Images Build Script${NC}"
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    print_warning "Not logged in to Docker Hub. Please run 'docker login' first."
    read -p "Do you want to continue with building only? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    PUSH_IMAGES=false
else
    PUSH_IMAGES=true
fi

# Build Backend Image
print_status "Building backend image..."
cd core
if docker build -t "${BACKEND_IMAGE}:${VERSION}" .; then
    print_status "Backend image built successfully"
else
    print_error "Backend image build failed"
    exit 1
fi
cd ..

# Build Frontend Image
print_status "Building frontend image..."
cd web-client
if docker build -t "${FRONTEND_IMAGE}:${VERSION}" .; then
    print_status "Frontend image built successfully"
else
    print_error "Frontend image build failed"
    exit 1
fi
cd ..

# Test images (optional)
if [ "$2" = "--test" ]; then
    print_status "Testing images..."
    
    # Test backend
    if docker run --rm -e DJANGO_SETTINGS_MODULE=pneumatic_backend.settings \
        "${BACKEND_IMAGE}:${VERSION}" python manage.py check > /dev/null 2>&1; then
        print_status "Backend image test passed"
    else
        print_warning "Backend image test failed"
    fi
    
    # Test frontend
    if docker run --rm -d --name test-frontend "${FRONTEND_IMAGE}:${VERSION}" > /dev/null 2>&1; then
        sleep 5
        if docker ps | grep -q test-frontend; then
            print_status "Frontend image test passed"
        else
            print_warning "Frontend image test failed"
        fi
        docker stop test-frontend > /dev/null 2>&1
        docker rm test-frontend > /dev/null 2>&1
    else
        print_warning "Frontend image test failed"
    fi
fi

# Push images to Docker Hub
if [ "$PUSH_IMAGES" = true ]; then
    print_status "Pushing images to Docker Hub..."
    
    if docker push "${BACKEND_IMAGE}:${VERSION}"; then
        print_status "Backend image pushed successfully"
    else
        print_error "Failed to push backend image"
        exit 1
    fi
    
    if docker push "${FRONTEND_IMAGE}:${VERSION}"; then
        print_status "Frontend image pushed successfully"
    else
        print_error "Failed to push frontend image"
        exit 1
    fi
else
    print_warning "Skipping image push (not logged in to Docker Hub)"
fi

# Show built images
echo ""
print_status "Build Summary:"
echo -e "${BLUE}Backend:${NC}  ${BACKEND_IMAGE}:${VERSION}"
echo -e "${BLUE}Frontend:${NC} ${FRONTEND_IMAGE}:${VERSION}"

if [ "$PUSH_IMAGES" = true ]; then
    echo ""
    print_status "Images are now available on Docker Hub!"
    echo -e "${BLUE}Usage in docker-compose.yml:${NC}"
    echo "  pneumatic-backend:"
    echo "    image: ${BACKEND_IMAGE}:${VERSION}"
    echo "  pneumatic-frontend:"
    echo "    image: ${FRONTEND_IMAGE}:${VERSION}"
fi

echo ""
print_status "Build complete! 🎉"
