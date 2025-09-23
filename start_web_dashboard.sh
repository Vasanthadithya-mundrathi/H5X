#!/bin/bash

# H5X Web Dashboard Demo Script
# This script demonstrates the H5X web interface for judges

echo "🚀 H5X Web Dashboard Demo"
echo "========================="
echo ""

# Check if Ganache is running
echo "🔗 Checking Blockchain Status..."
if curl -s http://127.0.0.1:8545 > /dev/null 2>&1; then
    echo "✅ Ganache blockchain is running"
else
    echo "⚠️  Ganache blockchain is not running"
    echo "   Please start Ganache on port 8545 for full functionality"
fi
echo ""

# Check if H5X CLI is available
echo "🔧 Checking H5X Engine..."
if [ -f "/Users/vasanthadithya/H5X/build/h5x-cli" ]; then
    echo "✅ H5X CLI is available"
else
    echo "❌ H5X CLI not found - please build the project first"
    exit 1
fi
echo ""

# Start the web dashboard
echo "🌐 Starting H5X Web Dashboard..."
echo "📍 URL: http://localhost:8080"
echo "📱 The interface will be available in your browser"
echo ""
echo "🎯 DEMO FEATURES:"
echo "   • Real-time system monitoring"
echo "   • Drag & drop file upload"
echo "   • Interactive obfuscation with progress tracking"
echo "   • Comprehensive results display"
echo "   • Blockchain integration status"
echo "   • One-click judge demo execution"
echo ""
echo "🔥 PRESS CTRL+C TO STOP THE DASHBOARD"
echo "================================================"
echo ""

# Change to the dashboard directory and start the server
cd /Users/vasanthadithya/H5X/tools/h5x-dashboard
python3 app.py