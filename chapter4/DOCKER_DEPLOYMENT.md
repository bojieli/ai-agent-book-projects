# Docker Deployment Guide for MCP Servers

This guide explains how to deploy the three MCP servers (execution-tools, perception-tools, collaboration-tools) using Docker.

## Overview

All three MCP servers are containerized with Docker support, making them:
- **Portable**: Run anywhere Docker is available
- **Isolated**: Each server runs in its own environment
- **Reproducible**: Consistent behavior across different machines
- **Easy to deploy**: Simple setup with docker-compose

## Prerequisites

1. **Docker** (version 20.10 or later)
2. **Docker Compose** (version 2.0 or later)
3. **API Keys** for external services (OpenAI, Google, etc.)

## Quick Start

### 1. Set Up Environment Variables

Copy the example environment file and configure your API keys:

```bash
cd /Users/boj/ai-agent-book/projects/week4
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-key
# ... other keys
```

### 2. Build and Run All Services

Use the provided script:

```bash
./build_and_run.sh
```

Or manually:

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Build Individual Services

To build/run a single service:

```bash
# Build execution-tools only
docker-compose build execution-tools

# Run execution-tools only
docker-compose up -d execution-tools
```

## Service Details

### Execution Tools

**Purpose**: Multi-language code execution with scientific computing support

**Languages Supported**:
- Python 3.11 (with NumPy, Pandas, Scikit-learn, etc.)
- JavaScript/Node.js 20.x
- TypeScript (with tsx/ts-node)
- Go 1.21
- Java 17 (OpenJDK)
- C++ (GCC)
- Rust
- PHP
- Bash

**Volume Mounts**:
- `execution-workspace:/workspace` - Code execution workspace

**Key Environment Variables**:
- `WORKSPACE_DIR`: Working directory for code execution
- `AUTO_VERIFY_CODE`: Automatically verify code before execution
- `AUTO_SUMMARIZE_COMPLEX_OUTPUT`: Summarize long outputs

### Perception Tools

**Purpose**: Document processing, web search, and data retrieval

**Features**:
- PDF/document processing
- Web search (Google, Arxiv)
- Data extraction and analysis
- OCR support (Tesseract)

**Volume Mounts**:
- `perception-data:/data` - Processed document storage

**Key Environment Variables**:
- `DATA_DIR`: Data storage directory
- `GOOGLE_API_KEY`: Google search API key
- `GOOGLE_CSE_ID`: Custom Search Engine ID

### Collaboration Tools

**Purpose**: Browser automation, Excel processing, HITL interactions

**Features**:
- Headless browser automation (Chromium)
- Excel file processing
- Human-in-the-loop interactions
- Chess game analysis
- Timer and notification tools

**Volume Mounts**:
- `collaboration-workspace:/workspace` - Working directory

**Key Environment Variables**:
- `WORKSPACE_DIR`: Working directory
- `DISPLAY`: X11 display (for headless browser)

## Local Development

For local development without Docker:

### Execution Tools

```bash
cd execution-tools
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python server.py
```

### Perception Tools

```bash
cd perception-tools
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your settings
python src/main.py
```

### Collaboration Tools

```bash
cd collaboration-tools
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Edit .env with your settings
python src/main.py
```

## Testing Multi-Language Code Execution

Once the execution-tools service is running, you can test different languages:

### Python Example
```python
code = """
import numpy as np
import pandas as pd

data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(data.describe())
"""
# Execute via MCP: code_interpreter(code=code, language="python")
```

### JavaScript Example
```javascript
code = """
console.log('Hello from Node.js!');
const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((a, b) => a + b, 0);
console.log('Sum:', sum);
"""
# Execute via MCP: code_interpreter(code=code, language="javascript")
```

### Go Example
```go
code = """
package main
import "fmt"

func main() {
    fmt.Println("Hello from Go!")
    sum := 0
    for i := 1; i <= 10; i++ {
        sum += i
    }
    fmt.Printf("Sum: %d\\n", sum)
}
"""
# Execute via MCP: code_interpreter(code=code, language="go")
```

## Docker Commands Reference

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec execution-tools bash

# Remove all containers and volumes
docker-compose down -v

# Rebuild a service
docker-compose up -d --build [service-name]
```

## Troubleshooting

### Issue: Service won't start

Check logs:
```bash
docker-compose logs [service-name]
```

### Issue: Permission denied

Ensure volumes have correct permissions:
```bash
docker-compose down -v
docker-compose up -d
```

### Issue: Out of memory

Increase Docker memory limit in Docker Desktop settings or add to docker-compose.yml:
```yaml
services:
  execution-tools:
    mem_limit: 4g
```

### Issue: Python packages missing

Rebuild the image:
```bash
docker-compose build --no-cache execution-tools
```

## Security Considerations

1. **Never commit .env files** with real API keys
2. **Use non-root users** in containers (already configured)
3. **Limit resource usage** with Docker resource constraints
4. **Keep images updated** regularly rebuild with latest security patches
5. **Use secrets management** for production deployments (Docker Swarm secrets, Kubernetes secrets)

## Production Deployment

For production deployments, consider:

1. **Orchestration**: Use Kubernetes or Docker Swarm
2. **Secrets Management**: Use external secret stores (Vault, AWS Secrets Manager)
3. **Monitoring**: Add Prometheus/Grafana for metrics
4. **Logging**: Centralized logging with ELK or Loki
5. **Resource Limits**: Set proper CPU/memory limits
6. **Health Checks**: Already configured in docker-compose.yml
7. **Auto-restart**: Already configured with `restart: unless-stopped`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Client (Claude)                    │
└────────────┬────────────┬────────────┬──────────────────┘
             │            │            │
             │ stdio      │ stdio      │ stdio
             │            │            │
   ┌─────────▼───────┐ ┌─▼──────────┐ ┌▼────────────────┐
   │ execution-tools │ │ perception-│ │ collaboration-  │
   │   Container     │ │   tools    │ │   tools         │
   │                 │ │ Container  │ │   Container     │
   │ • Python 3.11   │ │ • Doc Proc │ │ • Browser       │
   │ • Node.js 20    │ │ • Search   │ │ • Excel         │
   │ • Go 1.21       │ │ • OCR      │ │ • HITL          │
   │ • Java 17       │ │ • APIs     │ │ • Timers        │
   │ • C++/Rust/PHP  │ │            │ │                 │
   └────────┬────────┘ └─┬──────────┘ └┬────────────────┘
            │            │             │
            ▼            ▼             ▼
      /workspace      /data       /workspace
       (volume)      (volume)      (volume)
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review this documentation
3. Check the individual README files in each service directory
