#!/bin/bash

# Startup script for OpenWebUI with Adaptive RAG
# This script checks prerequisites and starts all necessary services

set -e

echo "🌿 Adaptive RAG + OpenWebUI Startup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_status "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_status "Docker Compose is installed"

echo ""

# Check if Neo4j is running
echo "Checking services..."
if ! curl -s http://localhost:7474 > /dev/null 2>&1; then
    print_warning "Neo4j doesn't seem to be running on port 7474"
    echo "  Starting Neo4j..."
    docker-compose up -d neo4j
    echo "  Waiting for Neo4j to start..."
    sleep 10
fi
print_status "Neo4j is accessible"

# Check if Adaptive RAG API is running
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    print_warning "Adaptive RAG API is not running on port 8000"
    echo ""
    echo "Please start the API first:"
    echo "  python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Press Enter when the API is running, or Ctrl+C to exit..."
    
    # Check again
    if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_error "API is still not accessible. Exiting."
        exit 1
    fi
fi
print_status "Adaptive RAG API is running"

echo ""

# Check if openwebui_pipeline.py exists
if [ ! -f "openwebui_pipeline.py" ]; then
    print_error "openwebui_pipeline.py not found in current directory"
    exit 1
fi
print_status "Pipeline file found"

echo ""

# Ask user for configuration
echo "Configuration:"
read -p "OpenWebUI port (default: 3000): " OPENWEBUI_PORT
OPENWEBUI_PORT=${OPENWEBUI_PORT:-3000}

echo ""

# Start OpenWebUI
echo "Starting OpenWebUI..."
docker-compose -f docker-compose.openwebui.yaml up -d

echo ""
echo "Waiting for OpenWebUI to start..."
sleep 5

# Check if OpenWebUI is running
MAX_RETRIES=12
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:$OPENWEBUI_PORT > /dev/null 2>&1; then
        print_status "OpenWebUI is running!"
        break
    fi
    echo "  Still waiting... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "OpenWebUI failed to start. Check logs with:"
    echo "  docker logs openwebui-adaptive-rag"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "OpenWebUI is now running at: http://localhost:$OPENWEBUI_PORT"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:$OPENWEBUI_PORT in your browser"
echo "2. Create an admin account (first visit only)"
echo "3. Go to Settings → Admin Settings → Pipelines"
echo "4. Find 'Adaptive RAG: Durian Pest & Disease' and configure:"
echo "   - API_BASE_URL: http://host.docker.internal:8000"
echo "   - Enable NODE_RETRIEVAL and EDGE_RETRIEVAL"
echo "   - Enable SHOW_CITATIONS"
echo "5. Start chatting!"
echo ""
echo "Available models:"
echo "  • Adaptive RAG (Speed Mode) - Fast (~3-5s)"
echo "  • Adaptive RAG (Balanced Mode) - Balanced (~5-8s)"
echo "  • Adaptive RAG (Quality Mode) - Best quality (~10-15s)"
echo ""
echo "To view logs:"
echo "  docker logs -f openwebui-adaptive-rag"
echo ""
echo "To stop:"
echo "  docker-compose -f docker-compose.openwebui.yaml down"
echo ""
