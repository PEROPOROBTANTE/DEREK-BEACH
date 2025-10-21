# DEREK-BEACH Deployment Guide

Complete guide for deploying DEREK-BEACH in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Server](#production-server)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Scaling](#scaling)
8. [Security](#security)

---

## Local Development

For local development and testing.

### Setup

```bash
# Clone repository
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH

# Create development environment
python3 -m venv venv-dev
source venv-dev/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run validation
python3 validate_choreography.py

# Run tests
pytest tests/ -v --cov=.
```

### Development Server

```bash
# Activate environment
source venv-dev/bin/activate

# Run example
python3 example_usage.py

# Or run orchestrator
python3 orchestrator_example.py
```

---

## Docker Deployment

Containerized deployment for consistency across environments.

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Use official Python runtime
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    libpoppler-cpp-dev \
    poppler-utils \
    tesseract-ocr \
    default-jre \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run validation during build
RUN python3 validate_choreography.py

# Create non-root user
RUN useradd -m -u 1000 derekbeach && \
    chown -R derekbeach:derekbeach /app

USER derekbeach

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from metadata_service import MetadataService; MetadataService().load_all()" || exit 1

# Default command
CMD ["python3", "-u", "orchestrator_example.py"]
```

### Build and Run

```bash
# Build image
docker build -t derek-beach:latest .

# Run container
docker run -it --rm derek-beach:latest

# Run with volume mount (for data persistence)
docker run -it --rm \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    derek-beach:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  derek-beach:
    build: .
    image: derek-beach:latest
    container_name: derek-beach-app
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DEREK_BEACH_ENV=production
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python3", "-c", "from metadata_service import MetadataService; MetadataService().load_all()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Run with docker-compose:

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

---

## Production Server

Deployment on dedicated servers (Ubuntu/Debian).

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install system dependencies
sudo apt install -y \
    ghostscript \
    libpoppler-cpp-dev \
    poppler-utils \
    tesseract-ocr \
    default-jre \
    git \
    nginx \
    supervisor
```

### Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash derekbeach
sudo su - derekbeach

# Clone repository
cd /opt
sudo git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
sudo chown -R derekbeach:derekbeach /opt/DEREK-BEACH
cd /opt/DEREK-BEACH

# Create production environment
python3.12 -m venv venv-prod
source venv-prod/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run validation
python3 validate_choreography.py

# Run tests
pytest tests/ -v
```

### Supervisor Configuration

Create `/etc/supervisor/conf.d/derek-beach.conf`:

```ini
[program:derek-beach]
command=/opt/DEREK-BEACH/venv-prod/bin/python3 orchestrator_example.py
directory=/opt/DEREK-BEACH
user=derekbeach
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/derek-beach/app.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=10
environment=PATH="/opt/DEREK-BEACH/venv-prod/bin"
```

Start service:

```bash
# Create log directory
sudo mkdir -p /var/log/derek-beach
sudo chown derekbeach:derekbeach /var/log/derek-beach

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start derek-beach

# Check status
sudo supervisorctl status derek-beach
```

### Nginx Configuration (Optional)

If exposing via web interface:

```nginx
server {
    listen 80;
    server_name derek-beach.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Cloud Deployment

### AWS EC2

```bash
# Launch EC2 instance (Ubuntu 22.04, t3.medium or larger)
# Install dependencies (same as Production Server section)

# Configure security groups
# - Allow SSH (port 22)
# - Allow HTTP (port 80) if using web interface

# Set up application
# (Follow Production Server setup steps)
```

### Google Cloud Platform

```bash
# Create Compute Engine instance
gcloud compute instances create derek-beach-vm \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=n1-standard-2 \
    --zone=us-central1-a

# SSH into instance
gcloud compute ssh derek-beach-vm --zone=us-central1-a

# Install dependencies and setup
# (Follow Production Server setup steps)
```

### Azure VM

```bash
# Create VM
az vm create \
    --resource-group derek-beach-rg \
    --name derek-beach-vm \
    --image UbuntuLTS \
    --size Standard_B2s \
    --admin-username azureuser \
    --generate-ssh-keys

# SSH into VM
az vm run-command invoke \
    --resource-group derek-beach-rg \
    --name derek-beach-vm \
    --command-id RunShellScript \
    --scripts "apt-get update"

# Setup application
# (Follow Production Server setup steps)
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Application settings
DEREK_BEACH_ENV=production
LOG_LEVEL=INFO
DETERMINISTIC_SEED=42

# Data paths
DEREK_BEACH_DATA=/app/data
DEREK_BEACH_LOGS=/app/logs

# Metadata files
CUESTIONARIO_PATH=cuestionario.json
EXECUTION_MAPPING_PATH=execution_mapping.yaml
RUBRIC_SCORING_PATH=rubric_scoring.json

# Processing settings
MAX_WORKERS=4
TIMEOUT_SECONDS=300
```

Load in Python:

```python
import os
from pathlib import Path

# Load configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
data_path = Path(os.getenv('DEREK_BEACH_DATA', './data'))
```

### Logging Configuration

Create `logging_config.yaml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/derek-beach.log
    maxBytes: 10485760  # 10MB
    backupCount: 10

loggers:
  derek_beach:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

---

## Monitoring

### Application Metrics

Create monitoring script `monitor.py`:

```python
import time
import logging
from metadata_service import MetadataService
from traceability_service import TraceabilityService

def check_health():
    """Check application health."""
    try:
        # Check metadata service
        metadata = MetadataService()
        metadata.load_all()
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'questions_loaded': len(metadata.questions),
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time(),
        }

if __name__ == '__main__':
    health = check_health()
    print(health)
```

### Log Monitoring

```bash
# View recent logs
tail -f /var/log/derek-beach/app.log

# Search for errors
grep ERROR /var/log/derek-beach/app.log

# Monitor with journalctl (if using systemd)
journalctl -u derek-beach -f
```

### System Monitoring

```bash
# Monitor CPU and memory
htop

# Monitor disk usage
df -h

# Monitor specific process
ps aux | grep python
```

---

## Scaling

### Horizontal Scaling

For processing multiple analyses simultaneously:

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

def process_analysis(plan_data):
    """Process single analysis."""
    choreographer = EventDrivenChoreographer(...)
    return choreographer.start_analysis(**plan_data)

# Process multiple plans
plans = [plan1_data, plan2_data, plan3_data]

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_analysis, plan) for plan in plans]
    results = [f.result() for f in as_completed(futures)]
```

### Vertical Scaling

Increase resources for individual processing:

```python
# Configure for more memory/CPU
config = ChoreographyConfig(
    max_workers=8,  # Increase parallelism
    batch_size=50,  # Process more items per batch
)
```

---

## Security

### Best Practices

1. **Keep Dependencies Updated**
   ```bash
   pip list --outdated
   pip install --upgrade -r requirements.txt
   ```

2. **Use Virtual Environments**
   - Isolate dependencies
   - Prevent system-wide conflicts

3. **Secure Secrets**
   ```bash
   # Use environment variables for secrets
   export API_KEY=your_secret_key
   
   # Or use secrets management
   # AWS Secrets Manager, Azure Key Vault, etc.
   ```

4. **Limit File Permissions**
   ```bash
   chmod 600 .env
   chmod 700 venv/
   ```

5. **Regular Security Audits**
   ```bash
   pip install safety
   safety check
   
   pip install bandit
   bandit -r .
   ```

6. **Network Security**
   - Use firewalls
   - Restrict SSH access
   - Use VPN for admin access

7. **Monitor Logs**
   - Set up alerts for errors
   - Monitor access patterns
   - Track resource usage

### Security Checklist

- [ ] All dependencies are up-to-date
- [ ] Virtual environment is used
- [ ] Secrets are not in code
- [ ] File permissions are restricted
- [ ] Firewall is configured
- [ ] Logs are monitored
- [ ] Backups are configured
- [ ] Access is audited

---

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=/backups/derek-beach
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup metadata files
tar -czf $BACKUP_DIR/metadata_$DATE.tar.gz \
    cuestionario*.json \
    execution_mapping.yaml \
    rubric_scoring*.json

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Recovery

```bash
# Restore from backup
cd /opt/DEREK-BEACH
tar -xzf /backups/derek-beach/metadata_20250121_120000.tar.gz
tar -xzf /backups/derek-beach/data_20250121_120000.tar.gz

# Restart service
sudo supervisorctl restart derek-beach
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check supervisor logs
sudo tail -f /var/log/supervisor/derek-beach-stderr.log

# Check application logs
tail -f /var/log/derek-beach/app.log

# Check system resources
df -h
free -h
```

### Performance Issues

```bash
# Monitor CPU and memory
htop

# Check disk I/O
iostat -x 1

# Profile Python code
python -m cProfile -o profile.stats orchestrator_example.py
```

### Memory Leaks

```bash
# Use memory profiler
pip install memory-profiler
python -m memory_profiler orchestrator_example.py
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Monitor logs for errors
- Check disk space
- Verify service status

**Weekly:**
- Review performance metrics
- Check for dependency updates
- Analyze error patterns

**Monthly:**
- Security audit
- Backup verification
- Performance optimization review

**Quarterly:**
- Dependency updates
- Security patching
- Architecture review

---

## Additional Resources

- [Installation Guide](INSTALLATION.md)
- [Quick Start](QUICKSTART.md)
- [Architecture Overview](README.md)
- [API Documentation](CHOREOGRAPHY_PROTOCOL.md)

---

**Last Updated**: 2025-10-21  
**Version**: 1.0.0
