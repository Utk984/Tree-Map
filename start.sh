#!/bin/bash

# Start script for Tree Map React + deck.gl application

echo "🌳 Starting Tree Map Application"
echo "=================================="

# Set environment variables to suppress multiprocessing warnings
export PYTHONWARNINGS="ignore::UserWarning:multiprocessing.resource_tracker"
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Check if Python API server is already running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Python API server already running on port 5001"
else
    echo "🚀 Starting Python API server on port 5001..."
    python api_server.py &
    API_PID=$!
    sleep 3
    
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Python API server started successfully"
    else
        echo "❌ Failed to start Python API server"
        exit 1
    fi
fi

# Check if React dev server is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ React dev server already running on port 3000"
else
    echo "🚀 Starting React development server on port 3000..."
    npm run dev &
    REACT_PID=$!
    sleep 5
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ React dev server started successfully"
    else
        echo "❌ Failed to start React dev server"
        exit 1
    fi
fi

echo ""
echo "🎉 Application started successfully!"
echo "=================================="
echo "📱 React Frontend: http://localhost:3000"
echo "🔧 Python API:     http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Keep script running until interrupted
trap "echo ''; echo '🛑 Shutting down servers...'; kill $API_PID $REACT_PID 2>/dev/null; echo '✅ Servers stopped'; exit" INT

# Wait for user to press Ctrl+C
while true; do
    sleep 1
done
