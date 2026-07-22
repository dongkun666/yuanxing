#!/bin/bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT"

echo "=== LexPrime Frontend Deployment ==="

echo "1. Running npm install..."
npm install

echo "2. Building production version..."
npm run build

DEPLOY_DIR="$PROJECT_ROOT/dist"
mkdir -p "$DEPLOY_DIR"

echo "3. Copying built files to deployment directory..."
cp -r assets/ "$DEPLOY_DIR/"
cp index.html "$DEPLOY_DIR/"
cp manifest.json "$DEPLOY_DIR/"
cp service-worker.js "$DEPLOY_DIR/"

echo "4. Generating index.prod.html..."
sed 's/development/production/g' index.html > "$DEPLOY_DIR/index.prod.html"

echo "5. Optimizing assets..."
find "$DEPLOY_DIR/assets" -name "*.js" -exec gzip -k {} \; 2>/dev/null || true
find "$DEPLOY_DIR/assets" -name "*.css" -exec gzip -k {} \; 2>/dev/null || true

echo ""
echo "=== Deployment complete ==="
echo "Deployed to: $DEPLOY_DIR"
echo "Production index: $DEPLOY_DIR/index.prod.html"