# Deployment Guide

## Overview

This guide covers deploying the Road Safety Intervention GPT system to production environments.

---

## Prerequisites

- Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- 8GB+ RAM (16GB recommended)
- 50GB+ disk space
- Python 3.8+
- Neo4j 5.x
- Ollama with required models
- Domain name (for web deployment)
- SSL certificate (for HTTPS)

---

## Production Architecture

```
                    ┌─────────────┐
                    │   Nginx     │  (Reverse Proxy)
                    │   SSL/TLS   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Gunicorn  │  (WSGI Server)
                    │   Workers   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐      ┌──────▼──────┐   ┌──────▼──────┐
    │ Neo4j  │      │   Ollama    │   │   Flask     │
    │  DB    │      │   LLM       │   │   Backend   │
    └────────┘      └─────────────┘   └─────────────┘
```

---

## Deployment Steps

### 1. Server Setup

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.8 python3-pip python3-venv nginx git

# Install Docker (for Neo4j)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

#### CentOS/RHEL
```bash
# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python38 python38-pip nginx git

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/road-safety-gpt
cd /opt/road-safety-gpt

# Clone repository
git clone https://github.com/yourusername/road-safety-gpt.git .

# Set permissions
sudo chown -R $USER:$USER /opt/road-safety-gpt
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production WSGI server
pip install gunicorn
```

### 4. Neo4j Deployment

#### Option A: Docker (Recommended)

```bash
# Pull Neo4j image
docker pull neo4j:5.12

# Create data directory
mkdir -p /opt/neo4j/data

# Run Neo4j
docker run -d \
  --name neo4j-roadsafety \
  -p 7474:7474 -p 7687:7687 \
  -v /opt/neo4j/data:/data \
  -e NEO4J_AUTH=neo4j/your_secure_password \
  --restart unless-stopped \
  neo4j:5.12
```

#### Option B: Native Installation

```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Install Neo4j
sudo apt update
sudo apt install neo4j

# Configure
sudo nano /etc/neo4j/neo4j.conf
# Uncomment: dbms.default_listen_address=0.0.0.0

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

#### Import Data

```bash
# Copy CSV to Neo4j import folder
docker cp GPT_Input_DB.csv neo4j-roadsafety:/var/lib/neo4j/import/

# Import using Cypher
docker exec -it neo4j-roadsafety cypher-shell -u neo4j -p your_secure_password
```

```cypher
LOAD CSV WITH HEADERS FROM 'file:///GPT_Input_DB.csv' AS row
CREATE (i:InfrastructureIssue {
  s_no: toInteger(row.`S. No.`),
  problem: row.problem,
  category: row.category,
  type: row.type,
  data: row.data,
  code: row.code,
  clause: row.clause
});
```

### 5. Ollama Deployment

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.1:8b
ollama pull VSSKSN/Llama_RSIGPT

# Create systemd service
sudo nano /etc/systemd/system/ollama.service
```

```ini
[Unit]
Description=Ollama LLM Service
After=network.target

[Service]
Type=simple
User=ollama
ExecStart=/usr/local/bin/ollama serve
Restart=always
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=multi-user.target
```

```bash
# Start Ollama service
sudo systemctl daemon-reload
sudo systemctl start ollama
sudo systemctl enable ollama
```

### 6. Configure Application

Create production configuration file:

```bash
nano /opt/road-safety-gpt/config.py
```

```python
import os

class ProductionConfig:
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Neo4j
    NEO4J_URI = "neo4j://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    
    # Ollama
    OLLAMA_HOST = "http://localhost:11434"
    
    # File paths (absolute paths for production)
    BASE_DIR = "/opt/road-safety-gpt"
    CHUNKS_FILE = f"{BASE_DIR}/data/road_safety_chunks.json"
    EMBEDDINGS_FILE = f"{BASE_DIR}/data/road_safety_embeddings.json"
    METADATA_FILE = f"{BASE_DIR}/data/vector_metadata.json"
    
    # Performance
    MAX_WORKERS = 4
    TIMEOUT = 30
```

Update `backend-server.py` to use config:

```python
from config import ProductionConfig

app.config.from_object(ProductionConfig)
```

### 7. Gunicorn Setup

Create Gunicorn configuration:

```bash
nano /opt/road-safety-gpt/gunicorn_config.py
```

```python
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '/var/log/road-safety-gpt/access.log'
errorlog = '/var/log/road-safety-gpt/error.log'
loglevel = 'info'

# Process naming
proc_name = 'road-safety-gpt'

# Server mechanics
daemon = False
pidfile = '/var/run/road-safety-gpt.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None
```

Create log directory:
```bash
sudo mkdir -p /var/log/road-safety-gpt
sudo chown $USER:$USER /var/log/road-safety-gpt
```

### 8. Systemd Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/road-safety-gpt.service
```

```ini
[Unit]
Description=Road Safety Intervention GPT
After=network.target neo4j.service ollama.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/road-safety-gpt
Environment="PATH=/opt/road-safety-gpt/venv/bin"
ExecStart=/opt/road-safety-gpt/venv/bin/gunicorn \
    --config /opt/road-safety-gpt/gunicorn_config.py \
    backend-server:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start road-safety-gpt
sudo systemctl enable road-safety-gpt

# Check status
sudo systemctl status road-safety-gpt
```

### 9. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/road-safety-gpt
```

```nginx
# Upstream to Gunicorn
upstream road_safety_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend (static files)
    location / {
        root /opt/road-safety-gpt/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # Backend API
    location /api/ {
        proxy_pass http://road_safety_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_http_version 1.1;
    }

    # Logs
    access_log /var/log/nginx/road-safety-gpt-access.log;
    error_log /var/log/nginx/road-safety-gpt-error.log;
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/road-safety-gpt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Monitoring & Maintenance

### Monitoring Tools

#### Systemd Status
```bash
# Check all services
sudo systemctl status road-safety-gpt neo4j ollama nginx

# View logs
sudo journalctl -u road-safety-gpt -f
```

#### Application Logs
```bash
# Access logs
tail -f /var/log/road-safety-gpt/access.log

# Error logs
tail -f /var/log/road-safety-gpt/error.log
```

#### System Resources
```bash
# Monitor resources
htop

# Check disk space
df -h

# Check memory
free -h
```

### Health Checks

Create a health check script:

```bash
nano /opt/road-safety-gpt/scripts/health_check.sh
```

```bash
#!/bin/bash

# Check Neo4j
nc -zv localhost 7687 || echo "Neo4j DOWN"

# Check Ollama
curl -s http://localhost:11434/api/tags > /dev/null || echo "Ollama DOWN"

# Check Application
curl -s http://localhost:5000/api/health | grep "healthy" || echo "Application DOWN"
```

```bash
chmod +x /opt/road-safety-gpt/scripts/health_check.sh
```

Add to crontab:
```bash
crontab -e
```

```cron
*/5 * * * * /opt/road-safety-gpt/scripts/health_check.sh
```

### Backup Strategy

#### Neo4j Backup
```bash
# Create backup script
nano /opt/road-safety-gpt/scripts/backup_neo4j.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Neo4j database
docker exec neo4j-roadsafety neo4j-admin database dump neo4j \
  --to-path=/backup/neo4j_backup_$DATE.dump

# Copy from container
docker cp neo4j-roadsafety:/backup/neo4j_backup_$DATE.dump $BACKUP_DIR/

# Keep only last 7 days
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
```

#### Application Backup
```bash
# Backup embeddings and data
tar -czf /opt/backups/app-data-$(date +%Y%m%d).tar.gz \
  /opt/road-safety-gpt/data/
```

---

## Scaling

### Horizontal Scaling

Deploy multiple Gunicorn instances:

```nginx
upstream road_safety_backend {
    least_conn;
    server 192.168.1.10:5000;
    server 192.168.1.11:5000;
    server 192.168.1.12:5000;
}
```

### Database Scaling

- Use Neo4j clustering for high availability
- Implement read replicas
- Use connection pooling

### Caching

Add Redis for response caching:

```python
from redis import Redis
cache = Redis(host='localhost', port=6379)

@app.route('/api/chat', methods=['POST'])
def chat():
    query = request.json.get('message')
    cache_key = f"query:{hash(query)}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))
    
    # Generate response
    response = generate_response(query)
    
    # Cache for 1 hour
    cache.setex(cache_key, 3600, json.dumps(response))
    
    return jsonify(response)
```

---

## Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Deny Neo4j external access (only localhost)
sudo ufw deny 7474
sudo ufw deny 7687
```

### Environment Variables

```bash
# Create .env file
nano /opt/road-safety-gpt/.env
```

```bash
NEO4J_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
```

Load in application:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Regular Updates

```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Python packages
pip install --upgrade -r requirements.txt

# Docker images
docker pull neo4j:5.12
```

---

## Troubleshooting

### Common Issues

#### 502 Bad Gateway
- Check if Gunicorn is running
- Verify Nginx upstream configuration
- Check application logs

#### Slow Responses
- Increase Gunicorn workers
- Add caching layer
- Optimize Neo4j queries

#### High Memory Usage
- Reduce Gunicorn workers
- Limit Ollama model size
- Add swap space

---

## Support

For deployment issues:
- Check logs: `/var/log/road-safety-gpt/`
- Test components individually
- Review systemd service status
- Consult GitHub Issues
