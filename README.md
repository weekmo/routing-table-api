# Routing Table API

![Tests](https://github.com/weekmo/routing-table-api/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/weekmo/GIST_ID/raw/coverage-badge.json)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-pink?logo=github)](https://github.com/sponsors/weekmo)

Routing table lookup service implementing Longest Prefix Match (LPM) using a radix tree. Provides REST API for route lookups and metric updates with Prometheus monitoring.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Service](#running-the-service)
- [API Documentation](#api-documentation)
  - [Health Check](#1-health-check)
  - [Route Lookup](#2-route-lookup)
  - [Update Metric (orlonger)](#3-update-route-metric-orlonger)
  - [Update Metric (match type)](#4-update-route-metric-with-match-type)
  - [Prometheus Metrics](#5-prometheus-metrics)
- [Performance](#performance)
- [Development](#development)
- [Algorithm Details](#algorithm-details)
- [Configuration](#configuration)
- [Deployment](#deployment)
  - [Docker Compose](#docker-compose-development)
  - [Podman Pod](#podman-pod)
  - [Podman Systemd](#podman-systemd)
  - [Kubernetes](#kubernetes)
  - [Deployment Comparison](#deployment-comparison)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Sponsor](#sponsor)
- [License](#license)

## Features

- Radix tree implementation with O(k) lookup complexity (k = prefix length)
- LRU cache (10,000 entries) for frequent lookups
- Thread-safe concurrent operations
- Prometheus metrics export
- IPv4 and IPv6 support
- 29 unit tests with 39% code coverage (20 unit + 9 concurrency)
- **Automated CI/CD** with GitHub Actions (multi-version testing, coverage tracking, security scans)

## Quick Start

### Prerequisites

- Python 3.8+ (3.11+ recommended)
- Podman or Docker (for containerized deployment)
- ~200MB disk space (100MB for routes.txt + dependencies)
- 512MB RAM minimum (2GB recommended for production)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd routing-table-api

# Install in editable mode with dev dependencies
make install

# Or manually:
pip install -e ".[dev]"
```

### Running the Service

**Development mode (with auto-reload):**
```bash
make devrun
# Or: uvicorn service.main:app --reload --host 0.0.0.0 --port 5000
```

**Docker:**
```bash
# Build and run with docker-compose
make compose-up

# Or build and run manually
make build
make run
```

**Access the API:**
- Interactive docs: http://localhost:5000/docs
- Alternative docs: http://localhost:5000/redoc
- Metrics: http://localhost:5000/metrics

## API Documentation

### 1. Health Check

Check service health and routing table status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "routes_loaded": 1090210,
  "radix_tree_routes": 1090210
}
```

**Status codes:**
- `200 OK`: Service is healthy

---

### 2. Route Lookup

Perform routing table lookup using Longest Prefix Match (LPM).

**Endpoint:** `GET /destination/{ip_address}`

**Parameters:**
- `ip_address` (path): IP address to lookup (e.g., `192.168.1.100`)

**Example requests:**
```bash
# IPv4 lookup
curl http://localhost:5000/destination/192.168.1.100

# IPv6 lookup
curl http://localhost:5000/destination/2001:db8::1
```

**Response (200 OK):**
```json
{
  "dst": "192.168.1.0/24",
  "nh": "10.0.0.1"
}
```

**Error responses:**
```json
// 400 Bad Request - Invalid IP
{
  "detail": "The given prefix is not correct: ..."
}

// 404 Not Found - No route
{
  "detail": "No route is found"
}
```

**Selection criteria (in order):**
1. **Longest prefix match** (e.g., /24 preferred over /16)
2. **Lowest metric** (if multiple routes with same prefix length)
3. **Lowest next-hop IP** (tie-breaker)

---

### 3. Update Route Metric (orlonger)

Update metric for all routes matching the specified prefix and next hop.

**Endpoint:** `PUT /prefix/{prefix}/nh/{next_hop}/metric/{metric}`

**Parameters:**
- `prefix` (path, URL-encoded): Network prefix in CIDR notation (e.g., `10.0.0.0%2F8`)
- `next_hop` (path): Next hop IP address (e.g., `192.168.1.1`)
- `metric` (path): New metric value (1-32768, lower is preferred)

**Match behavior:** Uses `orlonger` by default - updates the exact prefix AND all more-specific subnets.

**Example:**
```bash
# Update 10.0.0.0/8 and all subnets (10.1.0.0/16, 10.1.1.0/24, etc.)
curl -X PUT "http://localhost:5000/prefix/10.0.0.0%2F8/nh/192.168.1.1/metric/100"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "updated_routes": 5
}
```

**Error responses:**
```json
// 400 Bad Request - Invalid metric
{
  "detail": "Metric must be between 1 and 32768"
}

// 404 Not Found - No matching routes
{
  "detail": "No route is found"
}
```

---

### 4. Update Route Metric (with match type)

Update metric with explicit match type control.

**Endpoint:** `PUT /prefix/{prefix}/nh/{next_hop}/metric/{metric}/match/{match_type}`

**Parameters:**
- `prefix` (path, URL-encoded): Network prefix in CIDR notation
- `next_hop` (path): Next hop IP address
- `metric` (path): New metric value (1-32768)
- `match_type` (path): `exact` or `orlonger`

**Match types:**
- `exact`: Only update routes with exactly this prefix
- `orlonger`: Update this prefix AND all more-specific subnets

**Examples:**
```bash
# Update ONLY 10.0.0.0/8 (not subnets)
curl -X PUT "http://localhost:5000/prefix/10.0.0.0%2F8/nh/192.168.1.1/metric/100/match/exact"

# Update 10.0.0.0/8 and all subnets
curl -X PUT "http://localhost:5000/prefix/10.0.0.0%2F8/nh/192.168.1.1/metric/100/match/orlonger"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "updated_routes": 1
}
```

---

### 5. Prometheus Metrics

Expose Prometheus-compatible metrics for monitoring.

**Endpoint:** `GET /metrics`

**Available metrics:**
- `routing_lookups_total{status}`: Total lookups (counter) - labels: success, error, not_found
- `routing_lookup_latency_seconds`: Lookup latency histogram (seconds)
- `routing_updates_total{match_type,status}`: Total updates (counter)
- `routing_cache_hits_total`: Cache hits (counter)
- `routing_cache_misses_total`: Cache misses (counter)
- `routing_table_routes`: Current route count (gauge)
- `routing_errors_total{error_type}`: Error count by type (counter)

**Example response:**
```
# HELP routing_lookups_total Total number of routing lookups
# TYPE routing_lookups_total counter
routing_lookups_total{status="success"} 15234.0
routing_lookups_total{status="not_found"} 42.0

# HELP routing_lookup_latency_seconds Routing lookup latency in seconds
# TYPE routing_lookup_latency_seconds histogram
routing_lookup_latency_seconds_bucket{le="0.001"} 14892.0
routing_lookup_latency_seconds_bucket{le="0.01"} 15234.0
routing_lookup_latency_seconds_sum 2.456
routing_lookup_latency_seconds_count 15234.0

# HELP routing_cache_hits_total Total number of cache hits
# TYPE routing_cache_hits_total counter
routing_cache_hits_total 12543.0
```

---

## Performance

### Benchmark Results

**Radix Tree vs Linear Scan:**

| Method | Average Lookup Time | Performance |
|--------|-------------------|-------------|
| Radix tree | 15μs | Baseline |
| Linear scan | 307ms | 20,928x slower |

**Note:** Benchmark performed on 1,090,210 routes. Actual performance varies with dataset size and hardware.

**With LRU Cache:**
- Cache hit rate: ~80-90% for typical workloads
- Cached lookups: **<5μs**

**Concurrency:**
- Thread-safe operations with RLock
- Stress test: **167,227 lookups/sec** (20 concurrent threads)
- Full routing table (1,090,210 routes) loaded in ~16 seconds

---

## Development

### Running Tests

```bash
# Run all unit tests (excluding integration tests)
make test

# Run specific test files
pytest tests/test_lpm.py -v
pytest tests/test_concurrency.py -v

# Run with coverage report
make test-cov

# Open HTML coverage report in browser
make coverage-report
```

**Test coverage (29 unit + concurrency tests):**
- 20 unit tests (LPM algorithm correctness in test_lpm.py)
- 9 concurrency tests (thread safety in test_concurrency.py)
- **Current coverage: 39.4%** (service/lib/radix_tree.py: 94%, service/lib/models.py: 73%)
- Integration tests (test_service.py) require running service container

### Code Quality

```bash
# Run linter
make lint

# Format code
make format

# Type checking
make type-check

# Clean cache files
make clean
```

### Project Structure

```
routing-table-api/
├── .github/
│   ├── workflows/           # GitHub Actions CI/CD
│   │   ├── ci.yml          # Main CI pipeline
│   │   ├── coverage-badge.yml # Coverage tracking
│   │   └── release.yml     # Release automation
│   ├── dependabot.yml      # Dependency updates
│   └── CICD_SETUP.md       # CI/CD documentation
├── service/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   └── lib/                 # Core library modules
│       ├── __init__.py
│       ├── data.py          # Data loading and utilities
│       ├── models.py        # Pydantic models
│       └── radix_tree.py    # RadixTree implementation
├── tests/
│   ├── __init__.py
│   ├── test_lpm.py          # LPM algorithm tests
│   ├── test_concurrency.py # Thread safety tests
│   └── test_service.py      # Integration tests
├── routes.txt               # Routing table (1M+ routes)
├── pyproject.toml           # Project configuration
├── docker-compose.yml       # Podman Compose config
├── Dockerfile               # Multi-stage container build
├── makefile                 # Build automation
├── kubernetes-test.yaml     # Kubernetes deployment
├── podman-pod.yaml          # Podman pod configuration
├── podman-systemd/          # Systemd service files
└── README.md                # This file
```

### CI/CD Pipeline

The project includes a comprehensive GitHub Actions pipeline:

**Automated Checks on Every Push/PR:**
- ✅ Tests on Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ Code quality (ruff linting, formatting, mypy type checking)
- ✅ Security scanning (Safety, Bandit)
- ✅ Container build validation
- ✅ Coverage tracking and badge updates

**Setup Instructions:**
See [.github/CICD_SETUP.md](.github/CICD_SETUP.md) for complete CI/CD configuration guide.

**Badge Configuration:**
- Tests badge updates automatically with workflow status
- Coverage badge requires one-time setup (Codecov or GitHub Gist)
- See CI/CD setup guide for detailed instructions

---

## Algorithm Details

### Longest Prefix Match (LPM)

The service implements RFC 1812 routing lookup using a **binary radix tree (Patricia trie)**:

1. Convert IP address to binary representation
2. Traverse tree bit-by-bit following the prefix
3. Track the longest matching prefix encountered
4. Apply tie-breaking rules (metric, next-hop)

**Time Complexity:**
- Lookup: O(prefix_length) - typically 32 bits for IPv4, 128 for IPv6
- Insert: O(prefix_length)
- Update: O(prefix_length)

**Space Complexity:** O(n × prefix_length) where n = number of routes

### LRU Cache

Uses `functools.lru_cache` with 10,000 entry limit:
- Cache key: IP address string
- Cache value: (prefix, next_hop, metric) tuple
- Auto-eviction: Least recently used entries removed when full
- Cache invalidation: Cleared on any route update

---

## Configuration

Configuration via environment variables or `service/config.py`:

```python
# Default settings
ROUTES_FILE = "routes.txt"
PORT = 5000
HOST = "0.0.0.0"
MAX_METRIC = 32768
```

**Environment variables:**
```bash
export ROUTES_FILE=/path/to/routes.txt
export PORT=8080
export MAX_METRIC=65535
```

---

## Deployment

The Routing Table API supports multiple deployment methods depending on your environment and requirements.

### Docker Compose (Development)

**Best for:** Local development and testing

**File:** `docker-compose.yml`

#### Usage
```bash
# Build and run with tests
podman-compose up --build --abort-on-container-exit

# Run in background
podman-compose up -d

# View logs
podman-compose logs -f api
podman-compose logs -f tests

# Stop
podman-compose down

# Rebuild without cache
podman-compose build --no-cache
```

#### Features
- Automatic health checks
- Test runner waits for API to be ready
- Volume mount for routes.txt (no rebuild needed)
- Multi-stage build optimization
- Two services: `api` (runtime) and `tests` (development)

---

### Podman Pod

**Best for:** Local testing with Kubernetes-like pod structure

**File:** `podman-pod.yaml`

#### Usage
```bash
# Build images first
podman build -t routing-table-api:latest --target runtime .
podman build -t routing-table-api:test --target development .

# Run the pod
podman play kube podman-pod.yaml

# Check status
podman pod ps
podman ps -a --pod

# View logs
podman logs -f routing-table-api-pod-api
podman logs -f routing-table-api-pod-tests

# Stop and remove
podman pod stop routing-table-api-pod
podman pod rm routing-table-api-pod

# Or use play kube to clean up
podman play kube --down podman-pod.yaml
```

#### Features
- Containers share network namespace (communicate via localhost)
- Single pod unit (like Kubernetes)
- Compatible with `podman generate kube` for migration
- Health checks with liveness and readiness probes
- Resource limits defined

**Key Difference from Docker Compose:** Containers in the pod share the same network namespace, so they communicate via `localhost` instead of service names.

---

### Podman Systemd

**Best for:** Production deployments on single servers, auto-restart, system services

**Directory:** `podman-systemd/`

#### Installation
```bash
# For rootless (user services) - recommended
mkdir -p ~/.config/systemd/user/
cp podman-systemd/*.service ~/.config/systemd/user/

# Update ROUTES_FILE path in routing-table-api.service
vi ~/.config/systemd/user/routing-table-api.service
# Change: Environment=ROUTES_FILE=/path/to/routing-table-api/routes.txt

# Reload systemd
systemctl --user daemon-reload

# Enable auto-start on boot
systemctl --user enable routing-table-api.service

# Start the service
systemctl --user start routing-table-api.service
```

#### Usage
```bash
# Check status
systemctl --user status routing-table-api.service

# View logs (live tail)
journalctl --user -u routing-table-api.service -f

# Run tests
systemctl --user start routing-table-api-test.service

# Restart API
systemctl --user restart routing-table-api.service

# Stop
systemctl --user stop routing-table-api.service
```

#### Features
- **Automatic restart on failure:** Service restarts automatically if it crashes
- **Boot on startup:** Service starts automatically on system boot
- **Resource limits:** CPU (200%) and memory (2GB) enforced by systemd
- **Integrated logging:** Centralized logging via journald
- **Health checks:** Container health monitoring built-in
- **Rootless support:** Can run as non-root user

---

### Kubernetes

**Best for:** Production clusters, high availability, horizontal scaling

**File:** `kubernetes-test.yaml`

#### Local Testing with Minikube

```bash
# Start minikube
minikube start

# Use minikube's Docker daemon
eval $(minikube docker-env)

# Build images
docker build -t routing-table-api:latest --target runtime .
docker build -t routing-table-api:test --target development .

# Deploy
kubectl apply -f kubernetes-test.yaml

# Check deployment status
kubectl get deployments
kubectl get pods -l app=routing-table-api

# View API logs
kubectl logs -l app=routing-table-api -f

# Access API (port forward to localhost)
kubectl port-forward service/routing-table-api 5000:5000

# Clean up
kubectl delete -f kubernetes-test.yaml
```

#### Production Deployment

For production clusters:
1. Push images to container registry
2. Update `kubernetes-test.yaml` with registry URLs
3. Replace hostPath with PersistentVolume or ConfigMap
4. Adjust resource requests/limits
5. Add Ingress for external access (optional)
6. Deploy with `kubectl apply -f kubernetes-test.yaml`

#### Features
- **High availability:** Multi-replica deployments with automatic pod rescheduling
- **Load balancing:** Service distributes traffic across pods
- **Health checks:** Liveness and readiness probes for automatic recovery
- **Resource management:** CPU and memory requests/limits
- **Rolling updates:** Zero-downtime deployments
- **Horizontal pod autoscaling:** Scale based on CPU/memory (optional)

---

### Deployment Comparison

| Feature | Docker Compose | Podman Pod | Podman Systemd | Kubernetes |
|---------|---------------|------------|----------------|------------|
| **Use Case** | Development | Local Testing | Production (Single Host) | Production (Cluster) |
| **Complexity** | Low | Low | Medium | High |
| **Setup Time** | Minutes | Minutes | 10-15 minutes | Hours |
| **High Availability** | No | No | No | Yes |
| **Auto-restart** | Yes | Yes | Yes | Yes |
| **Boot on Startup** | Optional | No | Yes | Yes |
| **Horizontal Scaling** | No | No | No | Yes |
| **Load Balancing** | No | No | No | Yes |
| **Health Checks** | Yes | Yes | Yes | Yes |
| **Resource Limits** | Optional | Yes | Yes | Yes |
| **Multi-host** | No | No | No | Yes |

**Recommendations:**
- **Local Development:** Use Docker Compose for simplicity
- **CI/CD Testing:** Use Docker Compose or Podman Pod
- **Single Server Production:** Use Podman Systemd for reliability
- **Clustered Production:** Use Kubernetes for scale and high availability

---

## Monitoring

### Prometheus Metrics

All deployments expose Prometheus metrics at `GET /metrics`

#### Scraping Configuration

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'routing-table-api'
    static_configs:
      - targets: ['routing-table-api:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**For Kubernetes:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: routing-table-api
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "5000"
    prometheus.io/path: "/metrics"
```

#### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `routing_lookups_total` | Counter | Total number of IP lookups performed |
| `routing_lookup_latency_seconds` | Histogram | Lookup latency distribution |
| `routing_cache_hits_total` | Counter | Number of cache hits |
| `routing_cache_misses_total` | Counter | Number of cache misses |
| `routing_table_routes` | Gauge | Current number of routes loaded |
| `routing_errors_total` | Counter | Total errors by type |
| `routing_metric_updates_total` | Counter | Total metric update operations |

### Logging

**Docker Compose:**
```bash
podman-compose logs -f api
```

**Podman Systemd:**
```bash
journalctl --user -u routing-table-api.service -f
```

**Kubernetes:**
```bash
kubectl logs -l app=routing-table-api -f
```

### Health Checks

All deployments include health checks to ensure the service is ready before accepting traffic.

**Health Endpoint:** `GET /health`

**Expected Response:** HTTP 200 with JSON:
```json
{
  "status": "healthy",
  "routes_loaded": 1090210,
  "cache_size": 0,
  "uptime_seconds": 45.2
}
```

**Configuration:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Interval** | 30 seconds | How often to check |
| **Timeout** | 10 seconds | Request timeout |
| **Start Period** | 20 seconds | Grace period (route loading takes ~15s) |
| **Retries** | 3 | Failures before marked unhealthy |

**Why Health Checks Matter:** The API loads 1,090,210 routes on startup (12-15 seconds). Health checks prevent traffic before routes are loaded.

---

## Troubleshooting

### API Won't Start

```bash
# Check logs
podman-compose logs api
# or
journalctl --user -u routing-table-api.service
# or
kubectl logs -l app=routing-table-api

# Common issues:
# - routes.txt not found: Check volume mount path
# - Out of memory: Increase memory limit (need ~512MB minimum)
# - Port already in use: Check if another service is on port 5000
```

### Tests Failing

```bash
# Ensure API is healthy first
curl http://localhost:5000/health

# Check test logs
podman-compose logs tests
# or
kubectl logs job/routing-table-api-tests

# Common issues:
# - API not ready: Increase health check start period
# - Wrong API_URL: Verify environment variable
# - Network issues: Check connectivity between containers
```

### Health Check Failing

```bash
# Test health endpoint manually
curl http://localhost:5000/health

# If it times out:
# - Routes still loading (wait 20-30 seconds after startup)
# - Not enough memory (check container memory)
# - Application crashed (check logs)
```

### High Memory Usage

```bash
# Monitor memory
podman stats
# or
kubectl top pods

# Routes table uses ~300-500MB
# With cache: Can grow to 1-2GB
# Set resource limits to prevent OOM
```

### Slow Lookups

**Check cache statistics:**
```bash
# View Prometheus metrics
curl http://localhost:5000/metrics | grep cache

# Expected cache hit rate: 80-90%
# If low, increase cache size in service/main.py
```

---

## Sponsor

💖 **Support this project's development!**

This project is open source and maintained by volunteers. If you find it useful and want to support continued development, consider becoming a sponsor!

### GitHub Sponsors

⭐ **[Become a GitHub Sponsor](https://github.com/sponsors/weekmo)** ⭐

**Benefits of sponsoring:**
- Help sustain active maintenance and development
- Influence the project roadmap and priorities
- Get your name/logo in the README (for higher tiers)
- Priority support for issues and feature requests
- Feel good about supporting open source!

**Sponsor tiers:**
- 🥉 **$5/month** - Individual supporter (name in README)
- 🥈 **$25/month** - Professional user (logo + link in README)
- 🥇 **$100/month** - Organization sponsor (prominent logo, priority support)
- 💎 **$500/month** - Enterprise sponsor (custom features, SLA support)

### How to Enable GitHub Sponsors

**For maintainers:** To activate the sponsor button:

1. **Join GitHub Sponsors:**
   - Visit [github.com/sponsors](https://github.com/sponsors)
   - Complete the signup process (requires Stripe account)
   - Set up sponsor tiers and benefits

2. **Update FUNDING.yml:**
   ```yaml
   # In .github/FUNDING.yml, uncomment and update:
   github: weekmo
   ```

3. **The sponsor button will appear automatically** in the repository header

### Alternative Ways to Support

If you find this project useful, here are other ways to help:

- ⭐ **Star the repository** on GitHub to increase visibility
- 🐛 **Report bugs** and help improve stability  
- 📝 **Improve documentation** - fix typos, add examples, clarify instructions
- 🔧 **Submit pull requests** - implement features or fix bugs
- 📢 **Share with others** who might benefit from this project
- 💬 **Answer questions** in Issues and Discussions
- 📊 **Provide feedback** on your usage and requirements
- ☕ **[Buy me a coffee](https://buymeacoffee.com/weekmo)** (one-time donation)

### Commercial Support

**For companies using this in production:**

If your organization uses this project in production and would like:
- Custom features or integrations
- Priority bug fixes
- Consulting or training
- Service Level Agreements (SLAs)
- Dedicated support

Please contact the maintainers via GitHub Issues with the `[commercial]` tag or email directly.

### Current Sponsors

_Thank you to our amazing sponsors!_ 🙏

<!-- 
Sponsors will be listed here automatically once GitHub Sponsors is enabled.
Alternatively, update this section manually:

#### 💎 Enterprise Sponsors
- [Your Company Logo](https://example.com)

#### 🥇 Organization Sponsors  
- [Company Name](https://example.com)

#### 🥈 Professional Sponsors
- [@username](https://github.com/username)
-->

### Recognition

All contributors and sponsors are recognized in:
- Git commit history
- GitHub contributors page
- Release notes (for significant contributions)
- This README (for sponsors)

**Interested in corporate sponsorship?** Contact us via:
- Email: See maintainer contact in `pyproject.toml`
- GitHub: Open an issue with `[sponsorship]` tag

---

_This project is licensed under GPL-3.0-or-later. Sponsorship is completely optional and does not affect access to the project._
