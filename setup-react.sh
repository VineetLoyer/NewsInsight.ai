#!/bin/bash

# NewsInsight React UI Setup Script

echo "🚀 Setting up NewsInsight React UI..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Install dependencies
echo "📦 Installing React dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# React App Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=NewsInsight
REACT_APP_VERSION=1.0.0

# Optional: Enable development features
REACT_APP_DEBUG=true
EOL
    echo "✅ Created .env file"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "🎉 React UI setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Start the backend server: python backend.py"
echo "   2. Start the React app: npm start"
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "🔧 Available commands:"
echo "   npm start     - Start development server"
echo "   npm run build - Build for production"
echo "   npm test      - Run tests"
echo ""