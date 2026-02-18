#!/bin/bash
# ============================================
#  ENGRAM MEMORY SYSTEM - ONE-CLICK LAUNCHER
# ============================================

echo ""
echo "========================================"
echo "   ENGRAM MEMORY SYSTEM V1"
echo "========================================"
echo ""
echo "Starting API Server..."
echo ""

# Set Python path
export PYTHONPATH="$(pwd)"

# Start API server in background
python core/api.py &
API_PID=$!

# Wait for server to start
sleep 3

echo ""
echo "Opening Control Center..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8000/control.html
elif command -v open > /dev/null; then
    open http://localhost:8000/control.html
fi

echo ""
echo "Opening 3D Memory Universe..."
sleep 1
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8000/index.html
elif command -v open > /dev/null; then
    open http://localhost:8000/index.html
fi

echo ""
echo "========================================"
echo "   ENGRAM SYSTEM IS RUNNING!"
echo "========================================"
echo ""
echo "   Control Center: http://localhost:8000/control.html"
echo "   3D Universe:    http://localhost:8000/index.html"
echo ""
echo "   Press Ctrl+C to stop..."
echo ""

# Wait for interrupt
wait $API_PID
