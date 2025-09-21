# H5X Web Dashboard

A modern web interface for the H5X obfuscation engine, providing real-time monitoring, configuration management, and obfuscation control through a user-friendly web browser interface.

## Features

- **Real-time System Monitoring**: Live status of H5X CLI, configuration, and blockchain connectivity
- **Interactive Obfuscation**: Run obfuscation processes directly from the web interface
- **File Management**: Browse and manage obfuscated files and reports
- **Configuration Viewer**: View and validate H5X configuration settings
- **Blockchain Integration**: Monitor blockchain verification status
- **Responsive Design**: Modern, mobile-friendly interface

## Quick Start

### Prerequisites

- Python 3.8+
- H5X CLI (built and available in the project)
- Web browser

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the dashboard:**
   ```bash
   python app.py
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

## Features Overview

### System Status Dashboard

The main dashboard provides real-time monitoring of:

- **H5X CLI Status**: Availability and version information
- **Configuration Status**: Validation of configuration files
- **Blockchain Status**: Connection and functionality status
- **Recent Activity**: Latest obfuscated files and operations

### Interactive Obfuscation

Run obfuscation processes directly from the web interface:

- **File Selection**: Choose source files for obfuscation
- **Level Selection**: Select obfuscation levels (1-5)
- **Blockchain Toggle**: Enable/disable blockchain verification
- **Real-time Output**: View obfuscation progress and results

### File Management

Browse and manage your obfuscated files:

- **Recent Files**: View recently obfuscated files
- **File Details**: Size, modification time, and paths
- **Direct Access**: Download or view obfuscated files
- **Report Viewing**: Access detailed obfuscation reports

## API Endpoints

The dashboard provides a REST API for programmatic access:

### Status and Information

- `GET /api/status` - System status and health check
- `GET /api/config` - Current H5X configuration
- `GET /api/files` - List of recent files

### Operations

- `POST /api/obfuscate` - Run obfuscation process

Example API usage:

```bash
# Get system status
curl http://localhost:5000/api/status

# Run obfuscation
curl -X POST http://localhost:5000/api/obfuscate \
  -H "Content-Type: application/json" \
  -d '{
    "source_file": "/path/to/source.cpp",
    "level": 2,
    "enable_blockchain": true
  }'
```

## Configuration

The dashboard automatically detects H5X installation and configuration:

- **H5X CLI Path**: Auto-detected from project structure
- **Configuration File**: Uses `config/config.json`
- **Output Directory**: Uses `output/` for results
- **Logs Directory**: Uses `logs/` for log files

### Environment Variables

Optional environment variables for customization:

```bash
export H5X_CLI_PATH="/custom/path/to/h5x-cli"
export H5X_CONFIG_PATH="/custom/config.json"
export H5X_OUTPUT_PATH="/custom/output"
export FLASK_PORT=5000
export FLASK_HOST="0.0.0.0"
```

## Security Considerations

### Development vs Production

This dashboard is designed for development and testing environments. For production use, consider:

- **Authentication**: Add user authentication and authorization
- **HTTPS**: Use SSL/TLS encryption
- **Access Control**: Restrict network access appropriately
- **Input Validation**: Additional validation for file paths and parameters

### File System Access

The dashboard provides access to:
- Source files (read-only for obfuscation)
- Output files (read-only for browsing)
- Log files (read-only for viewing)
- Configuration files (read-only for display)

Ensure appropriate file system permissions are set.

## Development

### Project Structure

```
tools/h5x-dashboard/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates (auto-generated)
│   └── index.html     # Main dashboard template
└── README.md          # This file
```

### Adding Features

To add new features to the dashboard:

1. **Add API endpoints** in `app.py`
2. **Update the HTML template** for new UI elements
3. **Add JavaScript** for client-side functionality
4. **Update requirements.txt** if new dependencies are needed

### Customization

#### Styling

The dashboard uses inline CSS for simplicity. For extensive customization, consider:
- Moving CSS to separate files
- Using CSS frameworks like Bootstrap
- Adding custom themes

#### Functionality

Common customization points:
- **File filters**: Add filtering by file type or date
- **Batch operations**: Support for multiple file obfuscation
- **Advanced settings**: Expose more H5X configuration options
- **Real-time updates**: WebSocket support for live updates

## Troubleshooting

### Common Issues

**Dashboard won't start:**
```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :5000
```

**H5X CLI not found:**
- Verify H5X is built and available
- Check the H5X_CLI_PATH
- Ensure execute permissions

**Configuration errors:**
- Validate `config/config.json` syntax
- Check file permissions
- Verify all required configuration keys

**Blockchain connectivity issues:**
- Ensure Ganache is running
- Check RPC URL in configuration
- Verify network connectivity

### Debug Mode

Enable Flask debug mode for development:

```bash
export FLASK_DEBUG=1
python app.py
```

Debug mode provides:
- Automatic reloading on code changes
- Detailed error pages
- Enhanced logging

### Logging

The dashboard logs to stdout/stderr. For persistent logging:

```bash
python app.py 2>&1 | tee dashboard.log
```

## Integration with H5X

The dashboard integrates seamlessly with the H5X obfuscation engine:

### CLI Integration

- Automatically detects H5X CLI location
- Executes obfuscation commands
- Parses CLI output and results
- Displays version and help information

### Configuration Integration

- Reads H5X configuration files
- Validates configuration syntax
- Displays current settings
- Shows blockchain and other options

### File System Integration

- Monitors output directories
- Tracks obfuscated files
- Provides file access and downloads
- Manages temporary files

### Blockchain Integration

- Checks blockchain connectivity
- Displays verification status
- Shows transaction information
- Monitors smart contract interaction

## Performance Considerations

### Resource Usage

The dashboard is lightweight but consider:

- **Memory**: Flask application with minimal overhead
- **CPU**: Obfuscation processes may be CPU-intensive
- **Disk**: Monitor output directory for space usage
- **Network**: Blockchain operations require network access

### Scalability

For high-volume usage:

- **Process Queuing**: Implement background task queues
- **Load Balancing**: Use multiple dashboard instances
- **Database**: Consider persistent storage for metadata
- **Caching**: Cache status and file information

## Contributing

To contribute to the H5X dashboard:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## License

Same as H5X project - MIT License