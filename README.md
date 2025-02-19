# MCP Translation Server

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](docs/operations.md)

## Overview

MCP Translation Server is a high-performance machine translation system specialized for Manchu-Chinese translation. It implements the Model Context Protocol (MCP) based on the research paper "Exploring Linguistic Resources for Low-Resource Machine Translation with Large Language Models: A Case Study on Manchu".

## Key Features

- 🚀 High-performance translation engine
- 📚 Comprehensive dictionary support
- 🔍 Advanced morphological analysis
- 📖 Grammar-based translation assistance
- 💾 Efficient caching system
- 📊 Real-time performance monitoring
- 🔄 Parallel processing support
- 🎯 High accuracy with context awareness

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-translation-server.git
cd mcp-translation-server

# Start services using Docker Compose
docker-compose up -d
```

### Manual Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the server:
```bash
# Copy example configuration file
cp config.example.py config.py

# Edit config.py with your settings
vim config.py  # or use your preferred editor

# Set required environment variables
export MCP_SECRET_KEY="your-secure-random-string"  # Required
export MCP_API_TOKEN="your-api-token"            # Required
export MCP_REDIS_PASSWORD="your-redis-password"  # Optional
export MCP_SMTP_PASSWORD="your-smtp-password"    # Optional
```

4. Run the server:
```bash
python server.py
```

### Configuration

#### Environment Variables

The following environment variables are supported:

| Variable | Required | Description | Example |
|----------|----------|-------------|----------|
| `MCP_SECRET_KEY` | Yes | Secret key for session encryption | `openssl rand -hex 32` |
| `MCP_API_TOKEN` | Yes | API authentication token | `openssl rand -hex 32` |
| `MCP_REDIS_PASSWORD` | No | Redis server password | `your-redis-password` |
| `MCP_SMTP_PASSWORD` | No | SMTP server password | `your-smtp-password` |

#### Configuration File

The server can be configured by copying `config.example.py` to `config.py` and editing the values. The configuration file supports:

- API settings (host, port, debug mode)
- Security settings (secret key, API token)
- Rate limiting rules
- Cache configuration
- Model settings
- Resource paths
- Monitoring options
- Logging configuration
- Email notifications

**Important Security Notes:**

1. Never commit `config.py` to version control
2. Use strong, random values for `SECRET_KEY` and `API_TOKEN`
3. Store sensitive credentials in environment variables
4. Keep your `.env` file secure and never commit it
5. Regularly rotate security credentials

## Documentation

- [API Documentation](docs/api.md)
- [Usage Examples](docs/examples.md)
- [Operations Guide](docs/operations.md)
- [Contributing Guide](CONTRIBUTING.md)

## Architecture

### Core Components

1. Translation Engine
   - MT5-based neural translation
   - Context-aware processing
   - Batch processing support

2. Language Resources
   - Comprehensive dictionary
   - Grammar rule engine
   - Morphological analyzer
   - Parallel corpus

3. System Features
   - Efficient caching
   - Performance monitoring
   - Resource management
   - Error handling

## Performance

- Average translation latency: < 1s
- 95th percentile latency: < 2s
- Concurrent request handling: 100+ req/s
- Cache hit rate: > 80%

## Monitoring

- Real-time metrics via Prometheus
- Visualizations through Grafana
- Automated alerting system
- Performance tracking

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Research paper authors
- Open-source community
- Contributors and maintainers

## Contact

- GitHub Issues: For bug reports and feature requests
- Email: your.email@example.com
- Documentation: [Full Documentation](docs/)
   - Analysis (C^a)
   - Structure (C^a+s)
