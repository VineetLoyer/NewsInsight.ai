#!/bin/bash

# NewsInsight Full Stack Startup Script

echo "🚀 Starting NewsInsight Full Stack Application"
echo "=============================================="

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to start backend
start_backend() {
    echo "🔧 Starting Backend Server..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Run setup-backend.py first."
        return 1
    fi
    
    # Check backend port
    if ! check_port 8000; then
        echo "   Backend may already be running at http://localhost:8000"
        return 1
    fi
    
    # Activate virtual environment and start backend
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    echo "   Starting FastAPI server on port 8000..."
    python backend.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "✅ Backend started successfully (PID: $BACKEND_PID)"
        echo "   API available at: http://localhost:8000"
        echo "   API docs at: http://localhost:8000/docs"
        return 0
    else
        echo "❌ Backend failed to start"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting React Frontend..."
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "❌ Node modules not found. Run 'npm install' first."
        return 1
    fi
    
    # Check frontend port
    if ! check_port 3000; then
        echo "   Frontend may already be running at http://localhost:3000"
        return 1
    fi
    
    echo "   Starting React development server on port 3000..."
    npm start &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    sleep 5
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
        echo "   Application available at: http://localhost:3000"
        return 0
    else
        echo "❌ Frontend failed to start"
        return 1
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down NewsInsight..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo "   Stopping backend server..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "   Stopping frontend server..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    # Start backend
    if start_backend; then
        echo ""
        
        # Start frontend
        if start_frontend; then
            echo ""
            echo "🎉 NewsInsight is now running!"
            echo "================================"
            echo "📱 Frontend: http://localhost:3000"
            echo "🔧 Backend:  http://localhost:8000"
            echo "📚 API Docs: http://localhost:8000/docs"
            echo ""
            echo "Press Ctrl+C to stop all services"
            echo ""
            
            # Wait for user to stop
            wait
        else
            echo "❌ Failed to start frontend"
            cleanup
            exit 1
        fi
    else
        echo "❌ Failed to start backend"
        exit 1
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Run main function
main