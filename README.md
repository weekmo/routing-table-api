# Routing Table API

![Tests](https://github.com/weekmo/routing-table-api/actions/workflows/ci.yml/badge.svg)
![Coverage](./coverage-badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-ff69b4?logo=github)](https://github.com/sponsors/weekmo)

High-performance routing table lookup service with **20,928x faster** lookups using radix tree and LPM (Longest Prefix Match) algorithm.

---

## ✨ Features

- 🚀 **Radix tree** with O(k) lookup complexity - 20,928x faster than linear scan
- ⚡ **LRU caching** (10K entries) - sub-5μs cached lookups
- 🔒 **Thread-safe** concurrent operations with RLock
- 📊 **Prometheus metrics** - full observability
- 🌐 **IPv4 & IPv6** support
- 🧪 **29 unit tests** with 39% code coverage
- 🤖 **GitHub Actions CI/CD** - automated testing, security scans, multi-version validation

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/weekmo/routing-table-api.git
cd routing-table-api
make install

# Run development server
make devrun

# Or use containers
make compose-up
```

**Access:** http://localhost:5000/docs

---

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/destination/{ip}` | GET | Route lookup (LPM) |
| `/prefix/{prefix}/nh/{nh}/metric/{m}` | PUT | Update route metric (orlonger) |
| `/prefix/{prefix}/nh/{nh}/metric/{m}/match/{type}` | PUT | Update with match type |
| `/metrics` | GET | Prometheus metrics |

**Full API docs:** http://localhost:5000/docs (Swagger UI)

---

## 🎯 Performance

| Method | Lookup Time | vs Linear Scan |
|--------|-------------|----------------|
| **Radix tree** | **15μs** | 20,928x faster ⚡ |
| **With cache** | **<5μs** | 61,400x faster 🚀 |
| Linear scan | 307ms | Baseline |

*Tested on 1,090,210 routes*

**Concurrency:** 167,227 lookups/sec (20 threads)

---

## 💻 Development

```bash
# Run tests
make test          # Unit tests (29 tests)
make test-cov      # With coverage report
make coverage-report  # Open HTML coverage

# Code quality
make lint          # Ruff linter
make format        # Auto-format code
make type-check    # Mypy type checking
make clean         # Clean artifacts
```

**Test Suite:** 
- **29 tests** total (39% coverage)
  - 20 unit tests (LPM algorithm)
  - 9 concurrency tests (thread safety)

**CI/CD:** GitHub Actions runs tests on Python 3.8-3.12, security scans, and container builds. See [CI/CD setup](.github/CICD_SETUP.md).

---

## 📦 Deployment

### Deployment Options

Multiple deployment options available:

| Method | Use Case | Complexity | Setup Time | High Availability |
|--------|----------|------------|------------|-------------------|
| **Podman Compose** | Local dev | Low | 2 min | No |
| **Podman Systemd** | Single server prod | Medium | 10 min | No |
| **Kubernetes** | Clustered prod | High | 30+ min | Yes |

### Local Development (Podman Compose)

```bash
make compose-up
```

**Details:** See [docker-compose.yml](docker-compose.yml)

### Production Single Server (Podman Systemd)

```bash
cp podman-systemd/*.service ~/.config/systemd/user/
systemctl --user enable --now routing-table-api.service
```

**Details:** See [podman-systemd/](podman-systemd/)

### Production Cluster (Kubernetes)

```bash
kubectl apply -f kubernetes-test.yaml
```

**What's included:**
- **ConfigMap** - Routes data configuration
- **Deployment** - 1 replica with health checks
  - Liveness probe: 30s interval, 30s timeout
  - Readiness probe: 10s interval, 20s initial delay
  - Resource limits: 512Mi-2Gi memory, 500m-2000m CPU
- **Service** - ClusterIP exposure on port 5000
- **Job** - Integration tests with wait-for-API init container
- **Ingress** (commented) - Optional external access with nginx

**Configuration:**
- Mounts routes.txt as read-only volume
- Environment variables: `PYTHONUNBUFFERED=1`, `PROC_NUM=4`
- Image: `routing-table-api:latest` (local)
- Test image: `routing-table-api:test`

**Prerequisites:**
- Kubernetes cluster (1.20+)
- Local images built: `podman build -t routing-table-api:latest .`
- Routes file at: `/path/to/routing-table-api/routes.txt`

**Deployment:**

```bash
# Update the hostPath in kubernetes-test.yaml to your routes.txt location
# Then apply:
kubectl apply -f kubernetes-test.yaml

# Check status
kubectl get pods -l app=routing-table-api
kubectl logs -l app=routing-table-api -f

# Run tests
kubectl get jobs
kubectl logs -l app=routing-table-api-tests -f

# Port forward for local testing
kubectl port-forward svc/routing-table-api 5000:5000
```

**Troubleshooting:**
- Pod stuck pending: Check resource availability (`kubectl describe node`)
- Tests failing: Verify routes.txt path and API readiness
- Connection refused: Ensure Service and Deployment are running

**Details:** See [kubernetes-test.yaml](kubernetes-test.yaml)

---

## ⚙️ Configuration

Environment variables (see [service/config.py](service/config.py)):

```bash
ROUTES_FILE=routes.txt  # Routing table CSV file path
PORT=5000               # HTTP listen port
HOST=0.0.0.0           # Listen address (0.0.0.0 for all interfaces)
MAX_METRIC=32768       # Maximum metric value (1-32768)
```

---

## 🔍 Algorithm Details

### Radix Tree (Patricia Trie)

**Time Complexity:**
- **Lookup:** O(k) where k = prefix length (32 for IPv4, 128 for IPv6)
- **Insert:** O(k)
- **Update:** O(k)

**Space Complexity:** O(n × k) where n = number of routes

**LPM Selection Priority:**
1. **Longest prefix match** (most specific route)
2. **Lowest metric** (tie-breaker)
3. **Lowest next-hop IP** (final tie-breaker)

### LRU Cache

- **Implementation:** `functools.lru_cache`
- **Capacity:** 10,000 entries
- **Cache key:** IP address string
- **Cache value:** (prefix, next_hop, metric) tuple
- **Eviction:** Automatic (least recently used)
- **Invalidation:** Cleared on route updates

---

## 📁 Project Structure

```
routing-table-api/
├── .github/
│   ├── workflows/           # CI/CD pipelines
│   │   ├── ci.yml          # Main CI (tests, linting, security)
│   │   ├── coverage-badge.yml
│   │   └── release.yml
│   ├── FUNDING.yml         # GitHub Sponsors config
│   └── CICD_SETUP.md       # CI/CD documentation
├── service/
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration settings
│   └── lib/
│       ├── data.py         # Data loading utilities
│       ├── models.py       # Pydantic models
│       └── radix_tree.py   # Radix tree implementation
├── tests/
│   ├── test_lpm.py         # LPM algorithm tests (20)
│   ├── test_concurrency.py # Thread safety tests (9)
│   └── test_service.py     # Integration tests
├── podman-systemd/         # Systemd service files
├── routes.txt              # Routing table data (1M+ routes)
├── Dockerfile              # Multi-stage container build
├── docker-compose.yml      # Compose configuration
├── kubernetes-test.yaml    # K8s deployment
├── pyproject.toml          # Project configuration
├── makefile                # Build automation
└── README.md               # This file
```

---

## 📊 Monitoring

### Prometheus Metrics

**Endpoint:** `GET /metrics`

**Available metrics:**
- `routing_lookups_total{status}` - Total lookups (success/error/not_found)
- `routing_lookup_latency_seconds` - Lookup latency histogram
- `routing_cache_hits_total` - Cache hit counter
- `routing_cache_misses_total` - Cache miss counter
- `routing_table_routes` - Current route count
- `routing_errors_total{error_type}` - Error counter by type
- `routing_updates_total{match_type,status}` - Update operations

### Health Checks

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "routes_loaded": 1090210,
  "uptime_seconds": 45.2
}
```

**Configuration:**
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start period:** 20 seconds (routes load in ~15s)
- **Retries:** 3 failures before unhealthy

### Logging

```bash
# Docker Compose
podman-compose logs -f api

# Systemd
journalctl --user -u routing-table-api.service -f

# Kubernetes
kubectl logs -l app=routing-table-api -f
```

---

## 🐛 Troubleshooting

### API Won't Start

```bash
# Check logs
podman-compose logs api

# Common issues:
# - routes.txt not found → Check volume mount/path
# - Out of memory → Increase limit (min 512MB)
# - Port conflict → Check if port 5000 is in use
```

### High Memory Usage

```bash
# Monitor memory
podman stats

# Expected usage:
# - Routes: ~300-500MB
# - With cache: 500MB-2GB
# - Set limits to prevent OOM
```

### Low Cache Hit Rate

```bash
# Check cache metrics
curl http://localhost:5000/metrics | grep cache

# Expected: 80-90% hit rate
# If low: Increase cache size in service/main.py
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, requirements, and the commit convention.

---

## 📦 Releases

### Latest Release: v0.2.0

**Release Date:** January 2026

**What's New:**
- ✨ Radix tree implementation with O(k) lookup complexity
- ⚡ LRU caching for sub-5μs cached lookups
- 🔒 Thread-safe concurrent operations
- 📊 Prometheus metrics integration
- 🌐 Full IPv4 and IPv6 support
- 🧪 Comprehensive test suite (29 tests, 39% coverage)
- 🤖 CI/CD pipeline with automated testing and security scans
- 📦 Automated package distribution and container registry publishing

### Download & Install

**Container Images (Recommended):**
```bash
# Pull from GitHub Container Registry
podman pull ghcr.io/weekmo/routing-table-api:latest
podman pull ghcr.io/weekmo/routing-table-api:v0.2.0

# Run container
podman run -d -p 5000:5000 -v ./routes.txt:/app/routes.txt ghcr.io/weekmo/routing-table-api:latest
```

**Python Package (GitHub Releases):**
```bash
# Download from releases page
wget https://github.com/weekmo/routing-table-api/releases/download/v0.2.0/routing_table_api-0.2.0-py3-none-any.whl
pip install routing_table_api-0.2.0-py3-none-any.whl

# Or install from source
pip install git+https://github.com/weekmo/routing-table-api.git@v0.2.0
```

**Source Code:**
```bash
# Clone specific release
git clone --branch v0.2.0 https://github.com/weekmo/routing-table-api.git
cd routing-table-api
make install
```

### Release Assets

Each release includes:
- 📦 **Python wheel** (`.whl`) - Universal Python 3 package
- 📄 **Source distribution** (`.tar.gz`) - Complete source code
- 🐳 **Docker images** - Multi-arch containers on ghcr.io
- 📝 **Release notes** - What's new and breaking changes

### Automated Release Process

Releases are automatically created via GitHub Actions:

1. **Tag pushed** (`v*.*.*`) triggers the release workflow
2. **Tests run** - Ensures all 29 tests pass
3. **Packages built** - Creates wheel and source distribution
4. **GitHub Release created** - With release notes and artifacts
5. **Docker images pushed** - To GitHub Container Registry (ghcr.io)
6. **Tags applied** - Both version tag and `latest`

**To create a release:** Push a semantic version tag:
```bash
git tag -a v0.3.0 -m "Release v0.3.0"
git push origin v0.3.0
```

### Release Notes

**All Releases:** [GitHub Releases](https://github.com/weekmo/routing-table-api/releases)

**Container Registry:** [GitHub Packages](https://github.com/weekmo/routing-table-api/pkgs/container/routing-table-api)

### Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Breaking API changes
- **MINOR** version: New features (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

**Current:** `0.2.0` (Beta - API may change)  
**Stable:** `1.0.0` (Coming Q2 2026)

---

## 💖 Sponsor

[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-❤️_on_GitHub-ff69b4?logo=github)](https://github.com/sponsors/weekmo)

Support this open-source project:

- ⭐ **Star the repository** - Increase visibility
- 🐛 **Report bugs** - Help improve stability
- 📝 **Improve docs** - Fix typos, add examples
- 🔧 **Submit PRs** - Implement features or fixes
- 💰 **[Become a sponsor](https://github.com/sponsors/weekmo)** - Sustain development

### Sponsor Tiers

- 🥉 **$5/month** - Individual supporter (name in README)
- 🥈 **$25/month** - Professional user (logo + link)
- 🥇 **$100/month** - Organization (priority support)
- 💎 **$500/month** - Enterprise (SLA, custom features)

### Commercial Support

For production deployments requiring:
- Custom features or integrations
- Priority bug fixes
- Consulting or training
- Service Level Agreements (SLAs)

**Contact:** Open GitHub issue with `[commercial]` tag

---

## 📄 License

**GPL-3.0-or-later** - See [LICENSE](LICENSE)

This project is open source and free to use. Sponsorship is optional and does not affect access.

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:5000/docs (Swagger)
- **Alternative Docs:** http://localhost:5000/redoc
- **CI/CD Setup:** [.github/CICD_SETUP.md](.github/CICD_SETUP.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issues & Bugs:** [GitHub Issues](https://github.com/weekmo/routing-table-api/issues)

---

**Version:** 0.2.0 | **Status:** Beta | **Maintained by:** [@weekmo](https://github.com/weekmo)
