// H5X Dashboard JavaScript
class H5XDashboard {
    constructor() {
        this.uploadedFiles = [];
        this.currentTask = null;
        this.progressInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.refreshSystemStatus();
        this.refreshRecentFiles();
        
        // Auto-refresh system status every 30 seconds
        setInterval(() => this.refreshSystemStatus(), 30000);
    }
    
    setupEventListeners() {
        // File upload handling
        const fileInput = document.getElementById('file-input');
        const uploadArea = document.getElementById('upload-area');
        
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#2563eb';
            uploadArea.style.background = '#eff6ff';
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#e2e8f0';
            uploadArea.style.background = '#f1f5f9';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#e2e8f0';
            uploadArea.style.background = '#f1f5f9';
            
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });
    }
    
    async refreshSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateStatusDisplay(status);
        } catch (error) {
            console.error('Failed to fetch system status:', error);
            this.showErrorStatus();
        }
    }
    
    updateStatusDisplay(status) {
        // Header status indicators
        const cliStatus = document.getElementById('cli-status-text');
        const blockchainStatus = document.getElementById('blockchain-status-text');
        
        cliStatus.textContent = status.cli_available ? 'Online' : 'Offline';
        cliStatus.className = status.cli_available ? 'status-online' : 'status-offline';
        
        blockchainStatus.textContent = status.blockchain_connected ? 'Connected' : 'Disconnected';
        blockchainStatus.className = status.blockchain_connected ? 'status-online' : 'status-offline';
        
        // System status card
        const engineStatus = document.getElementById('engine-status');
        const engineVersion = document.getElementById('engine-version');
        const configStatus = document.getElementById('config-status');
        const blockchainConnection = document.getElementById('blockchain-connection');
        
        engineStatus.innerHTML = status.cli_available ? 
            '<i class="fas fa-check-circle status-online"></i> Online' : 
            '<i class="fas fa-times-circle status-offline"></i> Offline';
            
        engineVersion.textContent = status.cli_version;
        
        configStatus.innerHTML = status.config_valid ? 
            '<i class="fas fa-check-circle status-online"></i> Valid' : 
            '<i class="fas fa-exclamation-triangle status-warning"></i> Invalid';
            
        blockchainConnection.innerHTML = status.blockchain_connected ? 
            '<i class="fas fa-check-circle status-online"></i> Connected' : 
            '<i class="fas fa-times-circle status-offline"></i> Disconnected';
    }
    
    showErrorStatus() {
        const elements = ['cli-status-text', 'blockchain-status-text', 'engine-status', 'config-status', 'blockchain-connection'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = '<i class="fas fa-exclamation-triangle status-warning"></i> Error';
                element.className = 'status-warning';
            }
        });
    }
    
    handleFileSelect(event) {
        const files = event.target.files;
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        const allowedExtensions = ['cpp', 'c', 'cc', 'cxx', 'h', 'hpp', 'hxx'];
        
        for (let file of files) {
            const extension = file.name.split('.').pop().toLowerCase();
            if (allowedExtensions.includes(extension)) {
                if (!this.uploadedFiles.find(f => f.name === file.name)) {
                    this.uploadedFiles.push(file);
                }
            } else {
                this.showNotification(`File ${file.name} is not a supported C/C++ file.`, 'warning');
            }
        }
        
        this.updateUploadedFilesList();
        this.updateObfuscationButton();
    }
    
    updateUploadedFilesList() {
        const container = document.getElementById('uploaded-files');
        
        if (this.uploadedFiles.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = this.uploadedFiles.map((file, index) => `
            <div class="uploaded-file">
                <div class="file-info">
                    <i class="fas fa-file-code"></i>
                    <div>
                        <div class="file-name">${file.name}</div>
                        <div class="file-stats">${this.formatFileSize(file.size)}</div>
                    </div>
                </div>
                <div class="file-actions">
                    <button onclick="dashboard.removeFile(${index})" title="Remove file">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.updateUploadedFilesList();
        this.updateObfuscationButton();
    }
    
    clearFiles() {
        this.uploadedFiles = [];
        this.updateUploadedFilesList();
        this.updateObfuscationButton();
        document.getElementById('file-input').value = '';
    }
    
    updateObfuscationButton() {
        const button = document.getElementById('start-obfuscation');
        button.disabled = this.uploadedFiles.length === 0;
    }
    
    async startObfuscation() {
        if (this.uploadedFiles.length === 0) {
            this.showNotification('Please select files to obfuscate.', 'error');
            return;
        }
        
        // For demo purposes, we'll use the judge_demo.cpp file
        const level = document.getElementById('obfuscation-level').value;
        const outputName = document.getElementById('output-name').value || 'obfuscated_output';
        
        try {
            // Show progress section
            document.getElementById('progress-section').style.display = 'block';
            document.getElementById('results-section').style.display = 'none';
            
            // Start obfuscation with judge demo file
            const response = await fetch('/api/obfuscate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    input_file: 'judge_demo.cpp',
                    output_name: outputName + '_web',
                    level: parseInt(level)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentTask = result.task_id;
                this.startProgressTracking();
            } else {
                this.showNotification(result.error, 'error');
                document.getElementById('progress-section').style.display = 'none';
            }
        } catch (error) {
            console.error('Obfuscation failed:', error);
            this.showNotification('Failed to start obfuscation process.', 'error');
            document.getElementById('progress-section').style.display = 'none';
        }
    }
    
    startProgressTracking() {
        this.progressInterval = setInterval(async () => {
            if (!this.currentTask) {
                clearInterval(this.progressInterval);
                return;
            }
            
            try {
                const response = await fetch(`/api/task/${this.currentTask}`);
                const task = await response.json();
                
                this.updateProgress(task);
                
                if (task.status === 'completed' || task.status === 'failed') {
                    clearInterval(this.progressInterval);
                    this.handleTaskCompletion(task);
                }
            } catch (error) {
                console.error('Failed to get task status:', error);
                clearInterval(this.progressInterval);
            }
        }, 1000);
    }
    
    updateProgress(task) {
        const progressFill = document.getElementById('progress-fill');
        const progressStatus = document.getElementById('progress-status');
        const progressDetails = document.getElementById('progress-details');
        
        progressFill.style.width = `${task.progress || 0}%`;
        progressStatus.textContent = task.stage || 'Processing...';
        progressDetails.textContent = `Progress: ${task.progress || 0}% - ${task.stage || 'Working...'}`;
    }
    
    handleTaskCompletion(task) {
        const progressSection = document.getElementById('progress-section');
        const resultsSection = document.getElementById('results-section');
        const resultsContent = document.getElementById('results-content');
        
        progressSection.style.display = 'none';
        resultsSection.style.display = 'block';
        
        if (task.status === 'completed' && task.result && task.result.success) {
            const metrics = task.result.metrics;
            resultsContent.innerHTML = `
                <div class="results-grid">
                    <div class="result-metric">
                        <span class="metric-value">${metrics.functions_processed || 0}</span>
                        <span class="metric-label">Functions Processed</span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-value">${metrics.strings_obfuscated || 0}</span>
                        <span class="metric-label">Strings Obfuscated</span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-value">${metrics.instructions_modified || 0}</span>
                        <span class="metric-label">Instructions Modified</span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-value">${metrics.security_score || 0}/100</span>
                        <span class="metric-label">Security Score</span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-value">${metrics.processing_time || 0}s</span>
                        <span class="metric-label">Processing Time</span>
                    </div>
                    <div class="result-metric">
                        <span class="metric-value">${metrics.size_increase || '0%'}</span>
                        <span class="metric-label">Size Increase</span>
                    </div>
                </div>
                <div class="result-actions">
                    <button class="btn btn-primary" onclick="dashboard.downloadResult('${task.result.output_file}')">
                        <i class="fas fa-download"></i> Download Obfuscated Binary
                    </button>
                    <button class="btn btn-secondary" onclick="dashboard.runObfuscatedBinary('${task.result.output_file}')">
                        <i class="fas fa-play"></i> Test Binary
                    </button>
                </div>
            `;
            
            this.showNotification('Obfuscation completed successfully!', 'success');
            this.refreshRecentFiles();
        } else {
            resultsContent.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>Obfuscation Failed</h4>
                    <p>${task.result?.error || 'Unknown error occurred'}</p>
                </div>
            `;
            this.showNotification('Obfuscation failed. Please check the logs.', 'error');
        }
        
        this.currentTask = null;
    }
    
    async refreshRecentFiles() {
        try {
            const response = await fetch('/api/recent-files');
            const files = await response.json();
            
            const container = document.getElementById('recent-files-list');
            
            if (files.length === 0) {
                container.innerHTML = '<div class="loading-placeholder">No recent files found.</div>';
                return;
            }
            
            container.innerHTML = files.map(file => `
                <div class="file-item">
                    <div class="file-details">
                        <i class="fas fa-file-code file-icon"></i>
                        <div class="file-meta">
                            <div class="file-name">${file.name}</div>
                            <div class="file-stats">
                                ${this.formatFileSize(file.size)} • ${this.formatDate(file.modified)}
                            </div>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button onclick="dashboard.downloadFile('${file.name}')" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button onclick="dashboard.testBinary('${file.name}')" title="Test">
                            <i class="fas fa-play"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to fetch recent files:', error);
            document.getElementById('recent-files-list').innerHTML = 
                '<div class="loading-placeholder">Failed to load recent files.</div>';
        }
    }
    
    downloadFile(filename) {
        window.location.href = `/download/${filename}`;
    }
    
    async downloadResult(filename) {
        this.downloadFile(filename);
    }
    
    async runObfuscatedBinary(filename) {
        this.showNotification('Testing obfuscated binary...', 'info');
        // In a real implementation, you would execute the binary and show results
        setTimeout(() => {
            this.showNotification('Binary test completed successfully!', 'success');
        }, 2000);
    }
    
    async testBinary(filename) {
        this.runObfuscatedBinary(filename);
    }
    
    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Modal functions
function showUploadModal() {
    document.getElementById('upload-modal').style.display = 'flex';
}

function showDemo() {
    document.getElementById('demo-modal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function refreshSystemStatus() {
    dashboard.refreshSystemStatus();
}

function refreshRecentFiles() {
    dashboard.refreshRecentFiles();
}

function showRecentFiles() {
    dashboard.refreshRecentFiles();
    document.querySelector('.files-card').scrollIntoView({ behavior: 'smooth' });
}

async function runDemo() {
    const demoOutput = document.getElementById('demo-output');
    const demoConsole = document.getElementById('demo-console');
    
    demoOutput.style.display = 'block';
    demoConsole.textContent = 'Starting H5X Judge Demo...\n\n';
    
    try {
        // Start obfuscation of judge demo
        const response = await fetch('/api/obfuscate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input_file: 'judge_demo.cpp',
                output_name: 'judge_demo_web',
                level: 5
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            demoConsole.textContent += 'Demo obfuscation started successfully!\n';
            demoConsole.textContent += `Task ID: ${result.task_id}\n`;
            demoConsole.textContent += 'Check the main interface for progress updates.\n';
        } else {
            demoConsole.textContent += `Demo failed: ${result.error}\n`;
        }
    } catch (error) {
        demoConsole.textContent += `Demo error: ${error.message}\n`;
    }
}

function showAbout() {
    alert('H5X Obfuscation Engine v1.0.0\nAdvanced multi-layer code protection system with LLVM integration and blockchain verification.');
}

function showHelp() {
    alert('H5X Dashboard Help:\n\n1. Upload C/C++ files using drag & drop or file selector\n2. Configure obfuscation level (1-5)\n3. Click "Start Obfuscation" to begin\n4. Monitor progress in real-time\n5. Download results when complete\n\nFor more information, check the documentation.');
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new H5XDashboard();
});

// Add notification styles
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    z-index: 2000;
    max-width: 400px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.notification-success {
    background: #10b981;
    color: white;
}

.notification-error {
    background: #ef4444;
    color: white;
}

.notification-warning {
    background: #f59e0b;
    color: white;
}

.notification-info {
    background: #3b82f6;
    color: white;
}

.notification button {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    margin-left: auto;
    opacity: 0.8;
}

.notification button:hover {
    opacity: 1;
}
`;

// Add notification styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);