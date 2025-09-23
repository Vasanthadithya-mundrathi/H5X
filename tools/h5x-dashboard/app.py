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
import requests

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
        UPLOAD_PATH.mkdir(exist_ok=True)
        (OUTPUT_PATH / "obfuscated").mkdir(exist_ok=True)
        (OUTPUT_PATH / "reports").mkdir(exist_ok=True)
    
    def get_system_status(self):
        """Get H5X system status"""
        try:
            # Check if H5X CLI is available
            result = subprocess.run([self.h5x_cli, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            cli_available = result.returncode == 0
            cli_version = "H5X Engine v1.0.0" if cli_available else "Not available"
            
            # Check configuration
            config_exists = CONFIG_PATH.exists()
            config_valid = self.validate_config() if config_exists else False
            
            # Check blockchain connectivity
            blockchain_status = self.check_blockchain_status()
            
            return {
                'cli_available': cli_available,
                'cli_version': cli_version,
                'config_exists': config_exists,
                'config_valid': config_valid,
                'blockchain_connected': blockchain_status['connected'],
                'blockchain_url': blockchain_status['url'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'cli_available': False,
                'cli_version': f"Error: {str(e)}",
                'config_exists': False,
                'config_valid': False,
                'blockchain_connected': False,
                'blockchain_url': 'N/A',
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_config(self):
        """Validate H5X configuration"""
        try:
            if not CONFIG_PATH.exists():
                return False
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            # Basic validation
            return 'obfuscation' in config
        except Exception:
            return False
    
    def check_blockchain_status(self):
        """Check blockchain connectivity"""
        try:
            response = requests.get('http://127.0.0.1:8545', timeout=3)
            return {
                'connected': True,
                'url': 'http://127.0.0.1:8545'
            }
        except:
            return {
                'connected': False,
                'url': 'http://127.0.0.1:8545'
            }
    
    def run_obfuscation(self, input_file, output_name, level, task_id):
        """Run obfuscation process in background"""
        try:
            active_tasks[task_id] = {
                'status': 'running',
                'progress': 0,
                'stage': 'Initializing...',
                'start_time': datetime.now().isoformat()
            }
            
            # Update progress
            active_tasks[task_id]['progress'] = 20
            active_tasks[task_id]['stage'] = 'Compiling to LLVM IR...'
            time.sleep(1)
            
            # Run the obfuscation
            cmd = [self.h5x_cli, 'obfuscate', input_file, '-o', output_name, '--level', str(level)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
            
            active_tasks[task_id]['progress'] = 80
            active_tasks[task_id]['stage'] = 'Applying obfuscation passes...'
            time.sleep(1)
            
            if result.returncode == 0:
                # Parse output for metrics
                output_lines = result.stdout.split('\n')
                metrics = self.parse_obfuscation_output(output_lines)
                
                active_tasks[task_id]['progress'] = 100
                active_tasks[task_id]['stage'] = 'Completed successfully!'
                active_tasks[task_id]['status'] = 'completed'
                
                task_results[task_id] = {
                    'success': True,
                    'metrics': metrics,
                    'output_file': output_name,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                active_tasks[task_id]['status'] = 'failed'
                task_results[task_id] = {
                    'success': False,
                    'error': result.stderr,
                    'stdout': result.stdout
                }
                
        except Exception as e:
            active_tasks[task_id]['status'] = 'failed'
            task_results[task_id] = {
                'success': False,
                'error': str(e)
            }
    
    def parse_obfuscation_output(self, output_lines):
        """Parse obfuscation CLI output for metrics"""
        metrics = {
            'functions_processed': 0,
            'strings_obfuscated': 0,
            'instructions_modified': 0,
            'security_score': 0,
            'processing_time': 0,
            'original_size': 0,
            'obfuscated_size': 0,
            'size_increase': '0%'
        }
        
        for line in output_lines:
            if 'Functions Processed:' in line:
                metrics['functions_processed'] = int(line.split(':')[1].strip())
            elif 'Strings Obfuscated:' in line:
                metrics['strings_obfuscated'] = int(line.split(':')[1].strip())
            elif 'Instructions Modified:' in line:
                metrics['instructions_modified'] = int(line.split(':')[1].strip())
            elif 'Security Score:' in line:
                score_str = line.split(':')[1].strip().split('/')[0]
                metrics['security_score'] = float(score_str)
            elif 'Processing Time:' in line:
                time_str = line.split(':')[1].strip().rstrip('s')
                metrics['processing_time'] = float(time_str)
            elif 'Original Size:' in line:
                size_str = line.split(':')[1].strip().split()[0]
                metrics['original_size'] = int(size_str)
            elif 'Obfuscated Size:' in line:
                size_str = line.split(':')[1].strip().split()[0]
                metrics['obfuscated_size'] = int(size_str)
            elif 'Size Increase:' in line:
                metrics['size_increase'] = line.split(':')[1].strip()
        
        return metrics

dashboard = H5XDashboard()

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(dashboard.get_system_status())

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath
        })
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    """Start obfuscation process"""
    data = request.json
    input_file = data.get('input_file')
    output_name = data.get('output_name', 'obfuscated_output')
    level = data.get('level', 3)
    
    if not input_file:
        return jsonify({'success': False, 'error': 'No input file specified'})
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Start obfuscation in background thread
    thread = threading.Thread(
        target=dashboard.run_obfuscation, 
        args=(input_file, output_name, level, task_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id
    })

@app.route('/api/task/<task_id>')
def api_task_status(task_id):
    """Get task status"""
    if task_id in active_tasks:
        task = active_tasks[task_id].copy()
        if task_id in task_results:
            task['result'] = task_results[task_id]
        return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/recent-files')
def api_recent_files():
    """Get recent obfuscated files"""
    try:
        files = []
        output_dir = OUTPUT_PATH / "obfuscated"
        if output_dir.exists():
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'path': str(file_path)
                    })
        
        # Sort by modification time
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify(files[:10])  # Return last 10 files
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download obfuscated file"""
    try:
        return send_from_directory(str(OUTPUT_PATH / "obfuscated"), filename, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'cpp', 'c', 'cc', 'cxx', 'h', 'hpp', 'hxx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    print("🚀 Starting H5X Web Dashboard...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🔧 H5X CLI: {H5X_CLI_PATH}")
    print("🌐 Dashboard will be available at: http://localhost:8080")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=8080)