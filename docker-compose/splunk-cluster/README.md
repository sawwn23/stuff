# Splunk Distributed Cluster - Standard Operating Procedure

## Overview

This Docker Compose setup deploys a medium-sized Splunk distributed environment with the following components:

- **1 Search Head** (sh1) - Handles search requests and user interface
- **3 Indexers** (idx1, idx2, idx3) - Store and index data with clustering
- **1 Cluster Master** (cm1) - Manages the indexer cluster
- **1 Deployment Server** (dep1) - Manages app and configuration deployments
- **1 Heavy Forwarder** (hf1) - Forwards data to indexers

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 3.6+
- Minimum 8GB RAM available for containers

## Quick Start

### 1. Environment Setup

Create or verify your `.env` file:

```bash
SPLUNK_PASSWORD=your_secure_password_here
SPLUNK_IMAGE=splunk/splunk:latest
```

### 2. Deploy the Cluster

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

**Default Credentials:**

- Username: `admin`
- Password: Value from `SPLUNK_PASSWORD` in `.env`

## Service Details

### Search Head (sh1)

- **Role**: User interface and search coordination
- **Ports**: 8000 (Web UI), 8089 (Management)
- **Dependencies**: Cluster Master, Indexers

### Indexers (idx1, idx2, idx3)

- **Role**: Data storage and indexing
- **Clustering**: 3-node cluster with replication factor 3
- **Ports**: 8000 (Web UI), 8089 (Management)
- **Dependencies**: Cluster Master

### Cluster Master (cm1)

- **Role**: Manages indexer cluster configuration
- **Ports**: 8000 (Web UI), 8089 (Management)
- **Critical**: Must be running before indexers

### Deployment Server (dep1)

- **Role**: Manages app and configuration deployments
- **Ports**: 8000 (Web UI), 8089 (Management)

### Heavy Forwarder (hf1)

- **Role**: Data forwarding and preprocessing
- **Ports**: 1514 (TCP input)
- **Target**: Forwards to all indexers

## Operations

### Starting the Cluster

```bash
# Start in correct order (recommended)
docker-compose up -d cm1
sleep 30
docker-compose up -d idx1 idx2 idx3
sleep 30
docker-compose up -d sh1 dep1 hf1

# Or start all at once (Docker Compose handles dependencies)
docker-compose up -d
```

### Stopping the Cluster

```bash
# Graceful shutdown
docker-compose down

# Force stop (if needed)
docker-compose down --timeout 60
```

### Data Ingestion

#### Via Heavy Forwarder

```bash
# Send data to heavy forwarder
echo "test log message" | nc localhost 1514
```
