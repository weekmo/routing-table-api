# Routing Table API

![Tests](https://github.com/weekmo/routing-table-api/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/YOUR_USERNAME/GIST_ID/raw/coverage-badge.json)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-ff69b4)](https://github.com/sponsors/weekmo)

High-performance routing table lookup service with **20,928x faster** lookups using radix tree and LPM (Longest Prefix Match) algorithm.

## ✨ Features

- 🚀 **Radix tree** with O(k) lookup complexity - 20,928x faster than linear scan
- ⚡ **LRU caching** (10K entries) - sub-5μs cached lookups
- 🔒 **Thread-safe** concurrent operations with RLock
- 📊 **Prometheus metrics** - full observability
- 🌐 **IPv4 & IPv6** support
- 🧪 **29 unit tests** with 39% coverage
- 🤖 **GitHub Actions CI/CD** - automated testing, security scans, multi-version validation

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

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/destination/{ip}` | GET | Route lookup (LPM) |
| `/prefix/{prefix}/nh/{nh}/metric/{m}` | PUT | Update route metric |
| `/metrics` | GET | Prometheus metrics |

**Full API docs:** http://localhost:5000/docs (Swagger UI)

## 🎯 Performance

| Method | Lookup Time | vs Linear Scan |
|--------|-------------|----------------|
| **Radix tree** | **15μs** | 20,928x faster ⚡ |
| **With cache** | **<5μs** | 61,400x faster 🚀 |
| Linear scan | 307ms | Baseline |

*Tested on 1,090,210 routes*

**Concurrency:** 167,227 lookups/sec (20 threads)

## 💻 Development

```bash
# Run tests
make test          # Unit tests
make test-cov      # With coverage
make coverage-report  # Open HTML report

# Code quality
make lint          # Ruff linter
make format        # Auto-format
make type-check    # Mypy types
make clean         # Clean artifacts
```

**Test Suite:** 29 tests (39% coverage) - 20 unit + 9 concurrency

**CI/CD:** GitHub Actions runs tests on Python 3.8-3.12, security scans, and builds. See [CI/CD setup](.github/CICD_SETUP.md).

## 📦 Deployment

Multiple deployment options available:

| Method | Use Case | Complexity | Setup Time |
|--------|----------|------------|------------|
| **Podman Compose** | Local dev | Low | 2 min |
| **Podman Systemd** | Single server prod | Medium | 10 min |
| **Kubernetes** | Clustered prod | High | 30+ min |

**Quick Deploy:**
```bash
# Local development
make compose-up

# Production (systemd)
cp podman-systemd/*.service ~/.config/systemd/user/
systemctl --user enable --now routing-table-api.service
```

See deployment guides: [docker-compose.yml](docker-compose.yml) | [podman-systemd/](podman-systemd/) | [kubernetes-test.yaml](kubernetes-test.yaml)

## ⚙️ Configuration

Environment variables (see [service/config.py](service/config.py)):

```bash
ROUTES_FILE=routes.txt  # CSV file path
PORT=5000               # Listen port
HOST=0.0.0.0           # Listen address
MAX_METRIC=32768       # Max metric value
```

## 🔍 Algorithm

**Radix Tree (Patricia Trie):**
- **Lookup:** O(k) where k = prefix length (32 for IPv4, 128 for IPv6)
- **Insert/Update:** O(k)
- **Space:** O(n × k) where n = routes

**LPM Selection:**
1. Longest prefix match
2. Lowest metric (tie-break)
3. Lowest next-hop IP (final tie-break)

## 📁 Project Structure

```
routing-table-api/
├── .github/workflows/  # CI/CD pipelines
├── service/
│   ├── main.py         # FastAPI app
│   ├── config.py       # Settings
│   └── lib/
│       ├── data.py     # Data utilities
│       ├── models.py   # Pydantic models
│       └── radix_tree.py  # Core algorithm
├── tests/              # Test suite (29 tests)
├── routes.txt          # Routing table data
├── Dockerfile          # Multi-stage build
└── pyproject.toml      # Project config
```

## 🤝 Contributing

Uses `functools.lru_cache` with 10,000 entry limit:
- Cache key: IP address string
- Cache value: (prefix, next_hop, metric) tuple
- Auto-eviction: Least recently used entries removed when full
- Cache invalidation: Cleared on any route update

---

## 🚀 Deployment Comparison

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

## 📊 Monitoring

**Prometheus Metrics:** `GET /metrics`
- `routing_lookups_total`, `routing_lookup_latency_seconds`
- `routing_cache_hits_total`, `routing_cache_misses_total`
- `routing_table_routes`, `routing_errors_total`

**Health Checks:** `GET /health` (30s interval, 20s start period)
```json
{"status": "healthy", "routes_loaded": 1090210, "uptime_seconds": 45.2}
```

**Logs:**
```bash
# Docker Compose
podman-compose logs -f api

# Systemd
journalctl --user -u routing-table-api.service -f

# Kubernetes
kubectl logs -l app=routing-table-api -f
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

**Quick Start:**
```bash
# Fork, clone, and setup
git clone https://github.com/yourusername/routing-table-api.git
cd routing-table-api
make install

# Create branch and make changes
git checkout -b feature/amazing-feature

# Test and validate
make test-cov  # Must maintain ≥35% coverage
make lint
make type-check

# Commit using conventional commits
git commit -m "feat: add amazing feature"
```

**Requirements:**
- ✅ Tests pass (29/29) with coverage ≥35%
- ✅ Linter passes (`make lint`)
- ✅ Type hints for new code
- ✅ Google-style docstrings
- ✅ Follow PEP 8 (enforced by ruff)

**Commit Types:** `feat:` `fix:` `docs:` `refactor:` `test:` `chore:` `perf:`

See [Contributing Guide](.github/CONTRIBUTING.md) for details.

## 💖 Sponsor

[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-❤️_on_GitHub-ff69b4)](https://github.com/sponsors/weekmo)

Support this project:
- ⭐ Star the repo
- 🐛 Report bugs & improve docs
- 💰 [Become a sponsor](https://github.com/sponsors/weekmo)
- 💼 Commercial support available (contact via GitHub Issues with `[commercial]` tag)

## 📄 License

GPL-3.0-or-later - See [LICENSE](LICENSE)
