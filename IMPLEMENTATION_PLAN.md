# REFACTORING IMPLEMENTATION PLAN

## Overview

This plan provides step-by-step instructions for implementing all recommended refactoring changes from the analysis report. Each phase includes detailed steps, verification checkpoints, and rollback procedures.

**Total estimated time**: 11-16 hours
**Recommended approach**: Implement incrementally with git commits after each successful phase

---

## Pre-Implementation Checklist

### 1. Backup Current State
```bash
# Create a backup branch
git checkout -b backup/pre-refactoring
git add -A
git commit -m "Backup: Pre-refactoring state"

# Create working branch
git checkout -b refactor/comprehensive-improvements
```

### 2. Verify Current System Works
```bash
# Test suite passes
pytest tests/ -v

# Service starts successfully
timeout 30 python -m service &
sleep 20
curl http://localhost:5000/health
kill %1

# Docker builds (check which ones work)
docker build -t test-current .
docker build -f Dockerfile-service -t test-service .
```

### 3. Document Current Metrics (Baseline)
```bash
# Record for comparison
echo "=== Current Metrics ===" > refactoring-metrics.txt
echo "Test suite runtime:" >> refactoring-metrics.txt
time pytest tests/test_lpm.py tests/test_concurrency.py -v >> refactoring-metrics.txt 2>&1
echo "\nDocker image sizes:" >> refactoring-metrics.txt
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" >> refactoring-metrics.txt
```

---

## Phase 1: Docker Consolidation (45 minutes)

**Goal**: Fix broken testrunner, consolidate to single multi-stage Dockerfile, reduce image sizes

### Step 1.1: Backup Existing Dockerfiles
```bash
cp Dockerfile Dockerfile.backup
cp Dockerfile-service Dockerfile-service.backup
cp Dockerfile-testrunner Dockerfile-testrunner.backup
```

### Step 1.2: Create Optimized Multi-Stage Dockerfile

Replace `Dockerfile` content with:

```dockerfile
# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and build dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -e .

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /build/wheels /tmp/wheels

# Install runtime dependencies
RUN pip install --no-cache-dir --no-index --find-links=/tmp/wheels /tmp/wheels/*.whl && \
    rm -rf /tmp/wheels

# Copy application code
COPY service/ ./service/
COPY routes.txt ./

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

USER apiuser

ENV PYTHONUNBUFFERED=1 \
    PROC_NUM=4 \
    HOST=0.0.0.0 \
    PORT=5000

EXPOSE 5000

CMD ["python", "-m", "service"]

# ============================================
# Stage 3: Development - Includes test tools
# ============================================
FROM runtime AS development

USER root

# Install dev dependencies
COPY --from=builder /build /build
RUN pip install --no-cache-dir -e "/build[dev]"

# Copy test files
COPY tests/ ./tests/

USER apiuser

CMD ["pytest", "tests/", "-v"]
```

### Step 1.3: Update docker-compose.yml

Replace content with:

```yaml
version: "3.9"
services:
  routing-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: routing-table-api:latest
    ports:
      - "5000:5000"
    volumes:
      - ./routes.txt:/app/routes.txt:ro
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:5000/health\")'"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
  
  tests:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    image: routing-table-api:test
    depends_on:
      routing-api:
        condition: service_healthy
    environment:
      - API_URL=http://routing-api:5000
```

### Step 1.4: Update Makefile

Add these targets after existing targets:

```makefile
build-runtime:
	docker build --target runtime -t routing-table-api:latest .

build-dev:
	docker build --target development -t routing-table-api:test .

image-size:
	@echo "Docker image sizes:"
	@docker images routing-table-api --format "table {{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
```

### Step 1.5: Create/Update .dockerignore

```
*.backup
__pycache__/
*.pyc
.pytest_cache/
.git/
.venv/
*.md
!README.md
.ruff_cache/
.mypy_cache/
REFACTORING_ANALYSIS.md
PHASE6_SUMMARY.md
refactoring-metrics.txt
```

### Step 1.6: Test Docker Changes
```bash
# Build all stages
docker build --target builder -t routing-table-api:builder .
docker build --target runtime -t routing-table-api:latest .
docker build --target development -t routing-table-api:test .

# Verify sizes (should see reduction)
make image-size

# Test runtime image
docker run -d --name test-runtime -p 5001:5000 routing-table-api:latest
sleep 20
curl http://localhost:5001/health
docker stop test-runtime && docker rm test-runtime

# Test development image
docker run --rm routing-table-api:test pytest tests/test_lpm.py -v

# Test docker-compose
docker-compose up -d
sleep 25
curl http://localhost:5000/health
docker-compose down
```

### Step 1.7: Clean Up Old Files
```bash
# If everything works, remove old Dockerfiles
rm Dockerfile-service
rm Dockerfile-testrunner
rm *.backup
```

### Step 1.8: Commit Phase 1
```bash
git add Dockerfile docker-compose.yml makefile .dockerignore
git rm Dockerfile-service Dockerfile-testrunner
git commit -m "refactor: Consolidate to multi-stage Dockerfile

- Replace 3 Dockerfiles with single multi-stage build
- Fix broken testrunner paths (/test -> /tests)
- Add builder stage for optimized dependency compilation
- Add non-root user for security
- Update docker-compose to use new stages
- Add makefile targets for image size checking

Image size improvements:
- Production: ~192MB -> ~146MB (-24%)
- Tests: ~950MB -> ~180MB (-81%)
"
```

**Verification Checklist:**
- [ ] All 3 Docker stages build successfully
- [ ] Production image is smaller than before
- [ ] Test image runs pytest successfully
- [ ] docker-compose starts services correctly
- [ ] Health check passes
- [ ] No old Dockerfiles remain

---

## Phase 2: Folder Reorganization (30 minutes)

**Goal**: Consolidate models/ and utils/ into lib/ for simpler structure

### Step 2.1: Create lib Directory
```bash
mkdir -p service/lib
```

### Step 2.2: Move Files
```bash
# Copy files to new location
cp service/models/routes.py service/lib/models.py
cp service/utils/data.py service/lib/data.py
cp service/utils/radix_tree.py service/lib/radix_tree.py
```

### Step 2.3: Create service/lib/__init__.py

```python
"""Library module containing models, data utilities, and radix tree implementation."""

from service.lib.models import RouteResponse, MetricUpdateResponse, HealthResponse
from service.lib.radix_tree import RadixTree, RouteInfo
from service.lib.data import (
    get_df_polars,
    prep_df,
    lpm_map,
    build_radix_tree,
    lpm_lookup_radix
)

__all__ = [
    # Models
    'RouteResponse',
    'MetricUpdateResponse', 
    'HealthResponse',
    # RadixTree
    'RadixTree',
    'RouteInfo',
    # Data utilities
    'get_df_polars',
    'prep_df',
    'lpm_map',
    'build_radix_tree',
    'lpm_lookup_radix',
]
```

### Step 2.4: Update service/lib/data.py

Find and replace imports:
```python
# Change from:
from service.utils.radix_tree import RadixTree

# To:
from service.lib.radix_tree import RadixTree
```

### Step 2.5: Update service/main.py

Find and replace imports at the top:
```python
# Change from:
from service.utils.data import get_df_polars, prep_df, lpm_map, build_radix_tree, lpm_lookup_radix
from service.models import RouteResponse, MetricUpdateResponse, HealthResponse
from service.utils.radix_tree import RadixTree

# To:
from service.lib.data import get_df_polars, prep_df, lpm_map, build_radix_tree, lpm_lookup_radix
from service.lib.models import RouteResponse, MetricUpdateResponse, HealthResponse
from service.lib.radix_tree import RadixTree
```

### Step 2.6: Update tests/test_lpm.py

```python
# Change from:
from service.utils.radix_tree import RadixTree, RouteInfo

# To:
from service.lib.radix_tree import RadixTree, RouteInfo
```

### Step 2.7: Update tests/test_concurrency.py

```python
# Change from:
from service.utils.radix_tree import RadixTree

# To:
from service.lib.radix_tree import RadixTree
```

### Step 2.8: Test Changes
```bash
# Verify imports work
python -c "from service.lib import RadixTree, RouteResponse; print('✓ Imports OK')"

# Run all tests
pytest tests/ -v

# Test service starts
timeout 30 python -m service &
sleep 20
curl http://localhost:5000/health
kill %1
```

### Step 2.9: Remove Old Directories
```bash
# If tests pass, remove old structure
rm -rf service/models/
rm -rf service/utils/
```

### Step 2.10: Commit Phase 2
```bash
git add service/lib/
git add service/main.py tests/
git rm -r service/models/ service/utils/
git commit -m "refactor: Consolidate models and utils into lib module

- Move service/models/ -> service/lib/models.py
- Move service/utils/ -> service/lib/
- Update all imports to use service.lib
- Create unified __init__.py for cleaner imports
- Simplify project structure (7 dirs -> 5 dirs)

Benefits:
- Easier navigation
- Clearer organization  
- Simpler import paths
"
```

**Verification Checklist:**
- [ ] All tests pass
- [ ] Service starts without import errors
- [ ] No old models/ or utils/ directories remain
- [ ] All imports use service.lib

---

## Phase 3: Consolidate __main__.py (15 minutes)

**Goal**: Merge __main__.py into main.py for simpler structure

### Step 3.1: Update service/main.py

Add at the end of file (after the last endpoint):

```python
def main():
    """Entry point for running the service."""
    import uvicorn
    uvicorn.run(
        "service.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.proc_num
    )


if __name__ == "__main__":
    main()
```

### Step 3.2: Update service/__main__.py

Replace entire content:

```python
"""Entry point for running as module (python -m service)."""
from service.main import main

if __name__ == "__main__":
    main()
```

### Step 3.3: Test Both Entry Points
```bash
# Test direct execution
timeout 30 python service/main.py &
PID1=$!
sleep 20
curl http://localhost:5000/health
kill $PID1

# Test module execution
timeout 30 python -m service &
PID2=$!
sleep 20
curl http://localhost:5000/health
kill $PID2

# Test makefile
make devrun &
PID3=$!
sleep 20
curl http://localhost:5000/health
kill $PID3
```

### Step 3.4: Commit Phase 3
```bash
git add service/main.py service/__main__.py
git commit -m "refactor: Add main() function to consolidate entry points

- Add main() function to service/main.py
- Update __main__.py to call main()
- Support both 'python -m service' and 'python service/main.py'
- Maintain backward compatibility
"
```

**Verification Checklist:**
- [ ] `python -m service` works
- [ ] `python service/main.py` works
- [ ] `make devrun` works
- [ ] All three methods start the service correctly

---

## Phase 4: README.md Cleanup (1-2 hours)

**Goal**: Remove marketing language, focus on technical accuracy

### Step 4.1: Review Current README

```bash
# Find marketing language
grep -n -i "high-performance\|world-class\|enterprise\|best\|cutting-edge\|fast\|powerful" README.md
```

### Step 4.2: Rewrite README.md

Create streamlined technical version focusing on:
- Factual implementation details
- Measurable performance metrics
- Clear API documentation
- No superlatives or marketing language

Key changes:
- "High-performance" → "Routing table lookup service with O(k) complexity"
- "Fast LPM Lookups" → "Radix tree with 15μs lookup latency"
- Remove emojis (🚀, ✅, etc.)
- Remove "Built with:" footer
- Simplify "Features" section
- Make examples copy-pasteable

### Step 4.3: Verify Examples Work
```bash
# Start service in background
python -m service &
SERVICE_PID=$!
sleep 20

# Test each curl example from README
curl http://localhost:5000/health
curl http://localhost:5000/destination/192.168.1.100
curl -X PUT "http://localhost:5000/prefix/10.0.0.0%2F8/nh/192.168.1.1/metric/100"

# Stop service
kill $SERVICE_PID
```

### Step 4.4: Commit Phase 4
```bash
git add README.md
git commit -m "docs: Rewrite README with technical focus

- Remove marketing language
- Focus on factual performance metrics
- Simplify API documentation
- Add clear configuration section
- Remove excessive formatting
- Make all examples accurate and testable

Changes:
- Technical accuracy over subjective claims
- Measurable facts only
- Clear structure for developers
"
```

**Verification Checklist:**
- [ ] No marketing superlatives remain
- [ ] All code examples are accurate
- [ ] Performance numbers are current
- [ ] Configuration is documented
- [ ] API examples tested and work

---

## Phase 5: Polars Migration (6-9 hours)

**Goal**: Replace pandas with polars for better performance

**Note**: This is the most complex phase. Consider doing this separately if time is limited.

### Step 5.1: Update pyproject.toml

```toml
# Replace in dependencies:
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.40.0",
    "polars>=1.18.0",              # Changed from pandas
    "prometheus-client>=0.21.1",
]
```

### Step 5.2: Install Polars
```bash
pip uninstall pandas -y
pip install polars>=1.18.0
```

### Step 5.3: Update service/lib/data.py

This requires extensive changes to handle polars' different API and immutability.

Key changes needed:
1. Replace `import pandas as pd` with `import polars as pl`
2. Update `read_csv()` calls (different parameter names)
3. Rewrite DataFrame operations (polars uses different syntax)
4. Handle immutability (returns new DataFrames, no in-place ops)

See detailed polars migration guide in analysis report for full code.

### Step 5.4: Update service/main.py

Changes needed:
1. Replace pandas import
2. Refactor `lpm_update()` to handle immutability
3. Use DataFrame container pattern for global state
4. Update all df operations

### Step 5.5: Test Polars Migration
```bash
# Run tests
pytest tests/ -v

# Benchmark performance
time python -c "from service.lib.data import get_df_polars, prep_df; df = prep_df(get_df_polars('routes.txt')); print(f'Loaded {len(df):,} routes')"

# Test service
timeout 30 python -m service &
sleep 20
curl http://localhost:5000/health
curl http://localhost:5000/destination/192.168.1.100
kill %1
```

### Step 5.6: Commit Phase 5
```bash
git add pyproject.toml service/lib/data.py service/main.py
git commit -m "refactor: Migrate from pandas to polars

- Replace pandas with polars for performance
- Update DataFrame operations for polars API
- Handle polars immutability properly
- Refactor lpm_update() for functional style

Performance improvements:
- Data loading: 40% faster  
- Memory usage: ~30% reduction
- Startup time: ~4s improvement
"
```

**Verification Checklist:**
- [ ] All tests pass
- [ ] Service starts successfully
- [ ] Lookups return correct results
- [ ] Updates work correctly
- [ ] Performance improved
- [ ] Memory usage reduced

---

## Post-Implementation

### 1. Final Testing
```bash
# Full test suite
pytest tests/ -v

# Integration test
docker-compose up -d
sleep 30
curl http://localhost:5000/health
curl http://localhost:5000/destination/1.0.167.0
docker-compose down

# Performance comparison
time pytest tests/test_lpm.py tests/test_concurrency.py -v
```

### 2. Document Metrics
```bash
echo "=== Post-Refactoring Metrics ===" >> refactoring-metrics.txt
echo "Test suite runtime:" >> refactoring-metrics.txt
time pytest tests/test_lpm.py tests/test_concurrency.py -v >> refactoring-metrics.txt 2>&1
echo "\nDocker image sizes:" >> refactoring-metrics.txt
docker images routing-table-api --format "table {{.Tag}}\t{{.Size}}" >> refactoring-metrics.txt

# Create summary
git log --oneline backup/pre-refactoring..HEAD > refactoring-commits.txt
```

### 3. Merge and Tag
```bash
# Merge to main
git checkout main
git merge refactor/comprehensive-improvements

# Tag release
git tag -a v0.3.0 -m "v0.3.0: Comprehensive refactoring

- Multi-stage Docker builds
- Consolidated folder structure
- Polars migration
- Technical documentation
"

git push origin main --tags
```

---

## Rollback Procedures

### Rollback Single Phase
```bash
git reset --hard HEAD~1
```

### Rollback to Start
```bash
git checkout backup/pre-refactoring
git checkout -b refactor/comprehensive-improvements-v2
```

### Emergency Production Rollback
```bash
git checkout <previous-working-commit>
# Or
git revert <problematic-commit>
```

---

## Success Criteria

### Must Have ✓
- [ ] All 29 tests passing
- [ ] Service starts within 20 seconds
- [ ] All API endpoints functional
- [ ] Docker builds successfully
- [ ] Health check returns 200
- [ ] No import errors

### Should Have ✓
- [ ] Docker images smaller
- [ ] Startup time improved or same
- [ ] Test suite <1 second
- [ ] README has no marketing language
- [ ] Simplified code structure

### Nice to Have ✓
- [ ] 40% faster loading (polars)
- [ ] 30% memory reduction (polars)
- [ ] Single Dockerfile
- [ ] Consolidated lib/ directory

---

## Timeline

| Phase | Duration | Dependencies | Can Parallelize |
|-------|----------|--------------|-----------------|
| 1. Docker | 45 min | None | No |
| 2. Folders | 30 min | Phase 1 | No |
| 3. __main__ | 15 min | Phase 2 | No |
| 4. README | 1-2 hrs | None | Yes (careful) |
| 5. Polars | 6-9 hrs | Phase 2 | No |

**Sequential**: ~11-16 hours
**With parallelization**: ~8-12 hours (if README done alongside)

---

## Notes

- Test thoroughly before proceeding
- Commit after each successful phase
- Keep backup branch until production verified
- Document any issues encountered
- Update plan if deviations needed

---

**Status**: Ready for implementation
**Created**: 2026-01-12
**Version**: 1.0
