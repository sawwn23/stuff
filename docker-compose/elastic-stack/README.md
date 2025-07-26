# Elastic Stack Log Processing - Standard Operating Procedure (SOP)

## Overview

This setup provides a complete Elastic Stack (Elasticsearch + Kibana) environment with Logstash configurations for processing various log formats including firewall logs, threat logs, and JSON-based logs.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- Log files prepared in the specified formats

## Quick Start

### 1. Environment Setup

```bash
# Navigate to the elastic-stack directory
cd docker-compose/elastic-stack

# Review and modify environment variables if needed
cp .env.example .env  # if .env doesn't exist
```

### 2. Start the Elastic Stack

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Services

- **Elasticsearch**: https://localhost:9200
- **Kibana**: http://localhost:5601

**Default Credentials:**

- Username: `elastic`
- Password: `ChangeMe`

## Log Processing Configurations

### Available Logstash Configurations

| Configuration File    | Purpose                     | Input Format                 | Elasticsearch Index |
| --------------------- | --------------------------- | ---------------------------- | ------------------- |
| `csv-checkpoint.conf` | CheckPoint firewall logs    | CSV with semicolon separator | `cptraffic`         |
| `csv-gp.conf`         | GlobalProtect threat logs   | CSV                          | `pathreat`          |
| `csv-traffic.conf`    | Palo Alto traffic logs      | CSV                          | `patraffic`         |
| `skel.conf`           | Cloudflare logs             | NDJSON                       | `gitlab`            |
| `skel.json`           | Windows authentication logs | JSON                         | `window_auth`       |

### Data Directory Structure

Prepare your log files in the following directory structure:

```
/data/
├── checkpoint/
│   └── fwlog*
├── fw.log/
│   └── Threat-log-Oct-01-to-27/
│       └── *.csv
├── traffic_log/
│   └── FW01_traffic_2023_10_24*
├── logs/
│   └── cloudflarelogs.ndjson
├── chainsaw/
│   └── login_all.json
└── sincedb/
    ├── trafficsince.db
    └── since.db
```

## Running Logstash with Specific Configurations

### Method 1: Using Docker Run

```bash
# For CheckPoint logs
docker run --rm -it \
  -v /path/to/your/data:/data \
  -v $(pwd)/csv-checkpoint.conf:/usr/share/logstash/pipeline/logstash.conf \
  --network elastic-stack_default \
  docker.elastic.co/logstash/logstash:8.12.0

# For threat logs
docker run --rm -it \
  -v /path/to/your/data:/data \
  -v $(pwd)/csv-gp.conf:/usr/share/logstash/pipeline/logstash.conf \
  --network elastic-stack_default \
  docker.elastic.co/logstash/logstash:8.12.0
```

### Method 2: Adding Logstash to Docker Compose

Add this service to your `docker-compose.yml`:

```yaml
logstash:
  depends_on:
    es01:
      condition: service_healthy
  image: docker.elastic.co/logstash/logstash:8.12.0
  volumes:
    - certs:/usr/share/logstash/config/certs
    - ./csv-checkpoint.conf:/usr/share/logstash/pipeline/logstash.conf
    - /path/to/your/data:/data
  environment:
    - xpack.monitoring.enabled=false
  networks:
    - default
```

## Configuration Details

### CSV Log Processing

All CSV configurations include:

- **Header skipping**: `skip_header => true`
- **Column mapping**: Predefined column names for each log type
- **Elasticsearch output**: SSL disabled for local development

### JSON Log Processing

- **Automatic parsing**: JSON messages are automatically parsed
- **Flexible schema**: Supports nested JSON structures

## Troubleshooting

### Common Issues

1. **Memory Issues**

   ```bash
   # Increase memory limit in .env file
   MEM_LIMIT=2147483648  # 2GB
   ```

2. **SSL Certificate Issues**

   ```bash
   # Recreate certificates
   docker-compose down -v
   docker-compose up setup
   ```

3. **Permission Issues**

   ```bash
   # Fix file permissions
   sudo chown -R 1000:1000 /path/to/your/data
   ```

4. **Logstash Pipeline Issues**

   ```bash
   # Check Logstash logs
   docker-compose logs logstash

   # Test configuration syntax
   docker run --rm -it \
     -v $(pwd)/csv-checkpoint.conf:/tmp/logstash.conf \
     docker.elastic.co/logstash/logstash:8.12.0 \
     logstash -f /tmp/logstash.conf --config.test_and_exit
   ```

### Health Checks

```bash
# Check Elasticsearch health
curl -k -u elastic:ChangeMe https://localhost:9200/_cluster/health

# Check indices
curl -k -u elastic:ChangeMe https://localhost:9200/_cat/indices?v

# Check Kibana status
curl http://localhost:5601/api/status
```

## Data Management

### Index Management

```bash
# List all indices
curl -k -u elastic:ChangeMe https://localhost:9200/_cat/indices?v

# Delete an index
curl -k -u elastic:ChangeMe -X DELETE https://localhost:9200/index_name

# Check index mapping
curl -k -u elastic:ChangeMe https://localhost:9200/index_name/_mapping
```
