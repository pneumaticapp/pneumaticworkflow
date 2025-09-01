# Docker Images Build Guide

## Overview
This guide explains how to build and publish Docker images for Pneumatic backend and frontend services.

## Prerequisites
- Docker installed and running
- Access to Docker Hub (for publishing)
- Git repository cloned locally

## Backend Image (realm74/pneumatic-backend:latest)

### 1. Navigate to backend directory
```bash
cd core
```

### 2. Build the image
```bash
docker build -t realm74/pneumatic-backend:latest .
```

### 3. Test the image locally (optional)
```bash
# Test with environment variables
docker run --rm -e DJANGO_SETTINGS_MODULE=pneumatic_backend.settings \
  realm74/pneumatic-backend:latest python manage.py check
```

### 4. Push to Docker Hub
```bash
# Login to Docker Hub (if not already logged in)
docker login

# Push the image
docker push realm74/pneumatic-backend:latest
```

## Frontend Image (realm74/pneumatic-frontend:latest)

### 1. Navigate to frontend directory
```bash
cd web-client
```

### 2. Build the image
```bash
docker build -t realm74/pneumatic-frontend:latest .
```

### 3. Test the image locally (optional)
```bash
# Test the container starts
docker run --rm -p 8000:8000 realm74/pneumatic-frontend:latest
```

### 4. Push to Docker Hub
```bash
# Push the image
docker push realm74/pneumatic-frontend:latest
```

## Automated Build Script

Create a build script `build-images.sh`:

```bash
#!/bin/bash

# Build Backend
echo "Building backend image..."
cd core
docker build -t realm74/pneumatic-backend:latest .
cd ..

# Build Frontend
echo "Building frontend image..."
cd web-client
docker build -t realm74/pneumatic-frontend:latest .
cd ..

# Push images
echo "Pushing images to Docker Hub..."
docker push realm74/pneumatic-backend:latest
docker push realm74/pneumatic-frontend:latest

echo "Build complete!"
```

Make it executable:
```bash
chmod +x build-images.sh
```

## Version Tagging

For production releases, use version tags:

```bash
# Backend
docker build -t realm74/pneumatic-backend:v1.0.0 .
docker push realm74/pneumatic-backend:v1.0.0

# Frontend
docker build -t realm74/pneumatic-frontend:v1.0.0 .
docker push realm74/pneumatic-frontend:v1.0.0
```

## Multi-platform Builds

For ARM64 support (Apple Silicon, etc.):

```bash
# Backend
docker buildx build --platform linux/amd64,linux/arm64 \
  -t realm74/pneumatic-backend:latest \
  --push ./core

# Frontend
docker buildx build --platform linux/amd64,linux/arm64 \
  -t realm74/pneumatic-frontend:latest \
  --push ./web-client
```

## Troubleshooting

### Common Issues

1. **Build fails with poetry install**
   ```bash
   # Clear Docker cache
   docker system prune -a
   ```

2. **Frontend build fails**
   ```bash
   # Check Node.js version compatibility
   # Ensure all dependencies are in package.json
   ```

3. **Push fails**
   ```bash
   # Ensure you're logged in to Docker Hub
   docker login
   ```

### Build Optimization

1. **Use .dockerignore files**
   Create `.dockerignore` in both `core/` and `web-client/` directories:
   ```
   node_modules/
   __pycache__/
   *.pyc
   .git/
   .env
   ```

2. **Multi-stage builds** (for production optimization)
   Consider implementing multi-stage builds to reduce final image size.

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/docker-build.yml`:

```yaml
name: Build and Push Docker Images

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: ./core
          push: true
          tags: pneumaticapp/pneumatic-backend:latest
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./web-client
          push: true
          tags: pneumaticapp/pneumatic-frontend:latest
```

## Security Considerations

1. **Scan images for vulnerabilities**
   ```bash
   docker scan realm74/pneumatic-backend:latest
   docker scan realm74/pneumatic-frontend:latest
   ```

2. **Use specific base image versions**
   Update Dockerfile base images to use specific versions instead of `latest`.

3. **Minimize attack surface**
   Remove unnecessary packages and tools from production images.

## Monitoring

After deployment, monitor:
- Image pull statistics on Docker Hub
- Container health and performance
- Security vulnerabilities in base images
