#!/bin/bash

# Start script for Tree Map React + deck.gl application

echo "🌳 Starting Tree Map Application"
echo "=================================="

# Set environment variables to suppress multiprocessing warnings
export PYTHONWARNINGS="ignore::UserWarning:multiprocessing.resource_tracker"
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Initialize PID variables
API_PID=""
REACT_PID=""

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    
    if [ ! -z "$API_PID" ]; then
        echo "Stopping Python API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null
    fi
    
    if [ ! -z "$REACT_PID" ]; then
        echo "Stopping React dev server (PID: $REACT_PID)..."
        kill $REACT_PID 2>/dev/null
    fi
    
    # Additional cleanup for any remaining processes
    pkill -f "api_server.py" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Check if .venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check if requirements are installed, install if not
echo "📋 Checking Python dependencies..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✅ Python dependencies installed/verified"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found"
    exit 1
fi

# Install npm dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install npm dependencies"
        exit 1
    fi
    echo "✅ npm dependencies installed"
else
    echo "✅ npm dependencies already installed"
fi

# Check if Python API server is already running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Python API server already running on port 5001"
else
    echo "🚀 Starting Python API server on port 5001..."
    python api_server.py &
    API_PID=$!
    sleep 3
    
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
        echo "✅ Python API server started successfully (PID: $API_PID)"
    else
        echo "❌ Failed to start Python API server"
        cleanup
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
        echo "✅ React dev server started successfully (PID: $REACT_PID)"
    else
        echo "❌ Failed to start React dev server"
        cleanup
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
while true; do
    sleep 1
done
