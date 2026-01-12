# Routing Table API

High-performance routing table lookup service with LPM (Longest Prefix Match) algorithm. Uses radix tree for O(prefix_length) lookups with caching and Prometheus monitoring.

## Features

- **Fast LPM Lookups**: Radix tree implementation achieving ~15μs lookups (20,928x faster than linear scan)
- **LRU Caching**: 10,000-entry cache for frequent destination lookups
- **Thread-Safe**: Concurrent read/write operations with threading locks
- **Prometheus Metrics**: Built-in monitoring for latency, cache hits, errors
- **IPv4 & IPv6 Support**: Full support for both IP versions
- **Comprehensive Testing**: 29 unit and concurrency tests with 100% pass rate

## Quick Start

### Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

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
- Radix tree: **15μs** average lookup time
- Linear scan: **307ms** average lookup time
- **Speedup: 20,928x faster**

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
# Run all tests
make test

# Run specific test files
pytest tests/test_lpm.py -v
pytest tests/test_concurrency.py -v

# Run with coverage
pytest tests/ --cov=service --cov-report=html
```

**Test coverage:**
- 20 unit tests (LPM algorithm correctness)
- 9 concurrency tests (thread safety)
- 5 integration tests (API endpoints)

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
├── service/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── __main__.py          # Module entry point
│   ├── models/
│   │   ├── __init__.py
│   │   └── routes.py        # Pydantic models
│   └── utils/
│       ├── __init__.py
│       ├── data.py          # Data loading utilities
│       └── radix_tree.py    # RadixTree implementation
├── tests/
│   ├── __init__.py
│   ├── test_lpm.py          # LPM algorithm tests
│   ├── test_concurrency.py # Thread safety tests
│   └── test_service.py      # Integration tests
├── routes.txt               # Routing table (1M+ routes)
├── pyproject.toml           # Project configuration
├── docker-compose.yml       # Docker Compose config
├── Dockerfile-service       # Service container
├── makefile                 # Build automation
└── README.md                # This file
```

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

## Docker Deployment

### Using docker-compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker

```bash
# Build
docker build -f Dockerfile-service -t routing-table-api:latest .

# Run
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/routes.txt:/testwork/routes.txt \
  --name routing-api \
  routing-table-api:latest

# Stop and remove
docker stop routing-api && docker rm routing-api
```

---

## Monitoring with Prometheus

**Sample Prometheus configuration:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'routing-api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Key metrics to monitor:**
- `routing_lookup_latency_seconds`: Response time SLO
- `routing_cache_hits_total / (routing_cache_hits_total + routing_cache_misses_total)`: Cache hit rate
- `routing_errors_total`: Error rate
- `routing_table_routes`: Route count stability

---

## Troubleshooting

### Service won't start

**Error:** `FileNotFoundError: routes.txt`
```bash
# Ensure routes.txt is in the correct location
ls -l routes.txt

# Or set custom path
export ROUTES_FILE=/path/to/routes.txt
```

### Slow lookups

**Check cache statistics:**
```bash
# View Prometheus metrics
curl http://localhost:5000/metrics | grep cache

# Expected cache hit rate: 80-90%
# If low, increase cache size in service/main.py:
@lru_cache(maxsize=50000)  # Increase from 10000
```

### High memory usage

**With 1M routes:**
- DataFrame: ~150MB
- Radix tree: ~200MB
- Total: ~400-500MB expected

**Reduce memory:**
```python
# Decrease cache size
@lru_cache(maxsize=1000)  # Reduce from 10000
```

---

## License

GPL-3.0-or-later

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`make test`)
4. Run linter (`make lint`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## Changelog

### v0.2.0 (2026-01-12)

**Added:**
- Radix tree implementation (20,928x speedup)
- LRU caching (10,000 entries)
- Prometheus metrics integration
- Thread safety with RLock
- Comprehensive test suite (29 tests)
- Enhanced API documentation
- Type hints throughout codebase
- Health check endpoint

**Fixed:**
- matchd parameter bug (was hardcoded to "orlonger")
- Thread safety issues with concurrent DataFrame access
- Polars API compatibility issues
- Missing validation for metric ranges
- Error handling for invalid IPs

**Changed:**
- Removed polars dependency (using pandas only)
- Updated to use pyproject.toml instead of requirements.txt
- Makefile now uses docker-compose instead of podman
- Enhanced logging throughout service

---

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Email: support@example.com

---

**Built with:** FastAPI • Python • Pandas • Prometheus • Docker
