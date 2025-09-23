#!/usr/bin/env python3
"""
H5X Dashboard - Modern Web Interface for H5X Obfuscation Engine
Professional web interface for code obfuscation with real-time monitoring
"""

import os
import sys
import json
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
import hashlib
import uuid

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'h5x-dashboard-secret-key-2025'
app.config['UPLOAD_FOLDER'] = str(PROJECT_ROOT / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
H5X_CLI_PATH = PROJECT_ROOT / "build" / "h5x-cli"
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
OUTPUT_PATH = PROJECT_ROOT / "output"
LOGS_PATH = PROJECT_ROOT / "logs"
UPLOAD_PATH = PROJECT_ROOT / "uploads"

# Global task tracking
active_tasks = {}
task_results = {}

class H5XDashboard:
    def __init__(self):
        self.h5x_cli = str(H5X_CLI_PATH)
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        OUTPUT_PATH.mkdir(exist_ok=True)
        LOGS_PATH.mkdir(exist_ok=True)
        (OUTPUT_PATH / "obfuscated").mkdir(exist_ok=True)
        (OUTPUT_PATH / "reports").mkdir(exist_ok=True)
    
    def get_system_status(self):
        """Get H5X system status"""
        try:
            # Check if H5X CLI is available
            result = subprocess.run([self.h5x_cli, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            cli_available = result.returncode == 0
            cli_version = result.stdout.strip() if cli_available else "Not available"
            
            # Check configuration
            config_exists = CONFIG_PATH.exists()
            config_valid = False
            if config_exists:
                try:
                    with open(CONFIG_PATH) as f:
                        json.load(f)
                    config_valid = True
                except:
                    pass
            
            # Check blockchain status
            blockchain_status = self.check_blockchain_status()
            
            # Get recent activity
            recent_files = self.get_recent_files()
            
            return {
                "cli_available": cli_available,
                "cli_version": cli_version,
                "config_exists": config_exists,
                "config_valid": config_valid,
                "blockchain_status": blockchain_status,
                "recent_files": recent_files,
                "output_directory": str(OUTPUT_PATH),
                "logs_directory": str(LOGS_PATH)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_blockchain_status(self):
        """Check blockchain connectivity"""
        try:
            result = subprocess.run([self.h5x_cli, "config", "show"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse config output to get blockchain status
                output = result.stdout
                if "blockchain" in output.lower() and "enabled: true" in output:
                    return "enabled"
                elif "blockchain" in output.lower():
                    return "disabled"
            return "unknown"
        except:
            return "error"
    
    def get_recent_files(self):
        """Get recently obfuscated files"""
        try:
            obfuscated_dir = OUTPUT_PATH / "obfuscated"
            if not obfuscated_dir.exists():
                return []
            
            files = []
            for file_path in obfuscated_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(file_path.relative_to(PROJECT_ROOT))
                    })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x["modified"], reverse=True)
            return files[:10]  # Return last 10 files
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_config(self):
        """Get current configuration"""
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH) as f:
                    return json.load(f)
            return {}
        except Exception as e:
            return {"error": str(e)}
    
    def run_obfuscation(self, source_file, level=1, enable_blockchain=True):
        """Run obfuscation process"""
        try:
            cmd = [self.h5x_cli, "--input", source_file, "--level", str(level)]
            
            if not enable_blockchain:
                cmd.extend(["--no-blockchain"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Obfuscation process timed out (5 minutes)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Initialize dashboard
dashboard = H5XDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    status = dashboard.get_system_status()
    return render_template('index.html', status=status)

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(dashboard.get_system_status())

@app.route('/api/config')
def api_config():
    """API endpoint for configuration"""
    return jsonify(dashboard.get_config())

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    """API endpoint for running obfuscation"""
    try:
        data = request.get_json()
        source_file = data.get('source_file')
        level = data.get('level', 1)
        enable_blockchain = data.get('enable_blockchain', True)
        
        if not source_file:
            return jsonify({"error": "Source file is required"}), 400
        
        # Validate file exists
        file_path = Path(source_file)
        if not file_path.exists():
            return jsonify({"error": f"File not found: {source_file}"}), 400
        
        result = dashboard.run_obfuscation(source_file, level, enable_blockchain)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files')
def api_files():
    """API endpoint for recent files"""
    return jsonify(dashboard.get_recent_files())

@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve files from output directory"""
    return send_from_directory(OUTPUT_PATH, filename)

@app.route('/logs/<path:filename>')
def serve_logs(filename):
    """Serve files from logs directory"""
    return send_from_directory(LOGS_PATH, filename)

# Template folder setup
template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)

# Create basic HTML template if it doesn't exist
index_template = template_dir / "index.html"
if not index_template.exists():
    with open(index_template, 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H5X Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-ok { background: #27ae60; }
        .status-error { background: #e74c3c; }
        .status-warning { background: #f39c12; }
        .files-list { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .file-item { padding: 10px; border-bottom: 1px solid #eee; }
        .file-item:last-child { border-bottom: none; }
        .obfuscation-form { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
        .result-area { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 20px; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ H5X Obfuscation Dashboard</h1>
            <p>Advanced Code Obfuscation & Blockchain Verification</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🔧 System Status</h3>
                <p><span class="status-indicator {% if status.cli_available %}status-ok{% else %}status-error{% endif %}"></span>
                   H5X CLI: {{ "Available" if status.cli_available else "Not Available" }}</p>
                <p><span class="status-indicator {% if status.config_valid %}status-ok{% elif status.config_exists %}status-warning{% else %}status-error{% endif %}"></span>
                   Configuration: {% if status.config_valid %}Valid{% elif status.config_exists %}Invalid{% else %}Missing{% endif %}</p>
                <p><span class="status-indicator {% if status.blockchain_status == 'enabled' %}status-ok{% elif status.blockchain_status == 'disabled' %}status-warning{% else %}status-error{% endif %}"></span>
                   Blockchain: {{ status.blockchain_status|title }}</p>
            </div>
            
            <div class="status-card">
                <h3>📊 Quick Stats</h3>
                <p><strong>CLI Version:</strong> {{ status.cli_version }}</p>
                <p><strong>Output Directory:</strong> {{ status.output_directory }}</p>
                <p><strong>Recent Files:</strong> {{ status.recent_files|length }}</p>
            </div>
        </div>
        
        <div class="obfuscation-form">
            <h3>🚀 Run Obfuscation</h3>
            <form id="obfuscationForm">
                <div class="form-group">
                    <label for="sourceFile">Source File:</label>
                    <input type="text" id="sourceFile" name="sourceFile" placeholder="/path/to/source.cpp" required>
                </div>
                <div class="form-group">
                    <label for="level">Obfuscation Level:</label>
                    <select id="level" name="level">
                        <option value="1">Level 1 - Basic</option>
                        <option value="2" selected>Level 2 - Standard</option>
                        <option value="3">Level 3 - Advanced</option>
                        <option value="4">Level 4 - Aggressive</option>
                        <option value="5">Level 5 - Maximum</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="enableBlockchain" name="enableBlockchain" checked>
                        Enable Blockchain Verification
                    </label>
                </div>
                <button type="submit" class="btn btn-success">Start Obfuscation</button>
            </form>
        </div>
        
        <div id="resultArea" class="result-area" style="display: none;">
            <h3>🔄 Obfuscation Results</h3>
            <pre id="resultOutput"></pre>
        </div>
        
        <div class="files-list">
            <h3>📁 Recent Files</h3>
            <div id="recentFiles">
                {% for file in status.recent_files %}
                <div class="file-item">
                    <strong>{{ file.name }}</strong>
                    <br>Size: {{ "%.1f"|format(file.size / 1024) }} KB
                    <br>Modified: {{ file.modified }}
                </div>
                {% endfor %}
                {% if not status.recent_files %}
                <p>No files found. Run an obfuscation to see results here.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('obfuscationForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                source_file: formData.get('sourceFile'),
                level: parseInt(formData.get('level')),
                enable_blockchain: formData.get('enableBlockchain') === 'on'
            };
            
            const resultArea = document.getElementById('resultArea');
            const resultOutput = document.getElementById('resultOutput');
            
            resultArea.style.display = 'block';
            resultOutput.textContent = 'Running obfuscation...';
            
            try {
                const response = await fetch('/api/obfuscate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultOutput.textContent = 'Obfuscation completed successfully!\\n\\n' + result.stdout;
                } else {
                    resultOutput.textContent = 'Obfuscation failed:\\n\\n' + (result.error || result.stderr);
                }
                
            } catch (error) {
                resultOutput.textContent = 'Error: ' + error.message;
            }
        });
        
        // Auto-refresh status every 30 seconds
        setInterval(async function() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                // Update status indicators
                const indicators = document.querySelectorAll('.status-indicator');
                // Update logic here if needed
                
            } catch (error) {
                console.error('Failed to refresh status:', error);
            }
        }, 30000);
    </script>
</body>
</html>''')

if __name__ == '__main__':
    print("🚀 Starting H5X Dashboard...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🔧 H5X CLI: {H5X_CLI_PATH}")
    print(f"⚙️ Config: {CONFIG_PATH}")
    print(f"📤 Output: {OUTPUT_PATH}")
    print()
    print("🌐 Dashboard will be available at: http://localhost:5000")
    print("📋 API endpoints:")
    print("   • GET  /api/status - System status")
    print("   • GET  /api/config - Configuration")
    print("   • POST /api/obfuscate - Run obfuscation")
    print("   • GET  /api/files - Recent files")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)