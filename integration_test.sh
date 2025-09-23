#!/bin/bash

# H5X Final Integration Test Script
# Tests all components before git commit

echo "🧪 H5X FINAL INTEGRATION TEST"
echo "=============================="
echo ""

# Test 1: Blockchain Connectivity
echo "🔗 Testing Blockchain (Ganache) connectivity..."
if curl -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":67}' -s http://127.0.0.1:8545 | grep -q "Ganache"; then
    echo "✅ Ganache blockchain is running and responding"
else
    echo "⚠️  Ganache blockchain test failed"
fi
echo ""

# Test 2: H5X CLI
echo "🔧 Testing H5X CLI engine..."
if [ -f "/Users/vasanthadithya/H5X/build/h5x-cli" ]; then
    echo "✅ H5X CLI binary exists"
    echo "   Testing version command..."
    if /Users/vasanthadithya/H5X/build/h5x-cli --version > /dev/null 2>&1; then
        echo "✅ H5X CLI responds to version command"
    else
        echo "⚠️  H5X CLI version test failed"
    fi
else
    echo "❌ H5X CLI binary not found"
fi
echo ""

# Test 3: Web Dashboard Components
echo "🌐 Testing Web Dashboard components..."
if [ -f "/Users/vasanthadithya/H5X/tools/h5x-dashboard/app.py" ]; then
    echo "✅ Flask app.py exists"
else
    echo "❌ Flask app.py missing"
fi

if [ -f "/Users/vasanthadithya/H5X/tools/h5x-dashboard/templates/index.html" ]; then
    echo "✅ HTML template exists"
else
    echo "❌ HTML template missing"
fi

if [ -f "/Users/vasanthadithya/H5X/tools/h5x-dashboard/static/css/style.css" ]; then
    echo "✅ CSS styles exist"
else
    echo "❌ CSS styles missing"
fi

if [ -f "/Users/vasanthadithya/H5X/tools/h5x-dashboard/static/js/dashboard.js" ]; then
    echo "✅ JavaScript dashboard exists"
else
    echo "❌ JavaScript dashboard missing"
fi
echo ""

# Test 4: Demo Files
echo "🎯 Testing Demo files..."
if [ -f "/Users/vasanthadithya/H5X/judge_demo.cpp" ]; then
    echo "✅ Judge demo file exists"
else
    echo "❌ Judge demo file missing"
fi

if [ -f "/Users/vasanthadithya/H5X/start_web_dashboard.sh" ]; then
    echo "✅ Dashboard start script exists"
else
    echo "❌ Dashboard start script missing"
fi
echo ""

# Test 5: Quick Obfuscation Test
echo "⚡ Running quick obfuscation test..."
cd /Users/vasanthadithya/H5X
if ./build/h5x-cli obfuscate judge_demo.cpp -o integration_test --level 1 > /dev/null 2>&1; then
    echo "✅ Obfuscation test passed"
    if [ -f "./integration_test" ]; then
        echo "✅ Obfuscated binary created"
        # Test the binary
        if ./integration_test > /dev/null 2>&1; then
            echo "✅ Obfuscated binary executes successfully"
        else
            echo "⚠️  Obfuscated binary execution failed"
        fi
        # Clean up
        rm -f ./integration_test
    else
        echo "⚠️  Obfuscated binary not found"
    fi
else
    echo "❌ Obfuscation test failed"
fi
echo ""

# Test 6: File Structure Check
echo "📁 Checking project structure..."
required_dirs=("src" "tools" "config" "docs" "blockchain" "tests" "tools/h5x-dashboard")
for dir in "${required_dirs[@]}"; do
    if [ -d "/Users/vasanthadithya/H5X/$dir" ]; then
        echo "✅ Directory $dir exists"
    else
        echo "⚠️  Directory $dir missing"
    fi
done
echo ""

echo "🎉 INTEGRATION TEST COMPLETE"
echo "==========================="
echo ""
echo "✅ Ready for git commit if all tests passed!"
echo "🚀 Use: git add . && git commit -m 'Add professional web interface'"
echo ""