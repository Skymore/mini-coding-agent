#!/bin/bash

# Deployment script for sample application

set -e

echo "🚀 Starting deployment..."

# Configuration
APP_NAME="sample-app"
VERSION=$(python -c "from src import __version__; print(__version__)")
BUILD_DIR="build"

echo "📦 Building application v${VERSION}..."

# Create build directory
mkdir -p ${BUILD_DIR}

# Copy source files
cp -r src/ ${BUILD_DIR}/
cp requirements.txt ${BUILD_DIR}/
cp config.yaml ${BUILD_DIR}/

# Install dependencies
echo "📥 Installing dependencies..."
cd ${BUILD_DIR}
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
cd ..
python -m pytest tests/ -v

# Package application
echo "📦 Creating package..."
tar -czf ${APP_NAME}-${VERSION}.tar.gz -C ${BUILD_DIR} .

echo "✅ Deployment package created: ${APP_NAME}-${VERSION}.tar.gz"
echo "🎉 Deployment completed successfully!"
