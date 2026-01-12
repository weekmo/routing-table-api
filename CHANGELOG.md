# CHANGELOG

All notable changes to this project are documented in this file.

## [v0.2.0] - January 2026

### Added
- Radix tree implementation with O(k) lookup complexity
- LRU caching for sub-5μs cached lookups
- Thread-safe concurrent operations
- Prometheus metrics integration
- Full IPv4 and IPv6 support
- CI/CD pipeline with automated testing and container publishing

### Packaging
- Python wheel and source distribution are produced by CI
- Docker images are published to GitHub Container Registry: `ghcr.io/weekmo/routing-table-api`

---

## Release Process

Releases are created via GitHub Actions and include:

1. Tag pushed (`v*.*.*`) triggers release workflow
2. Tests run across supported Python versions
3. Packages built (wheel and sdist)
4. Docker images pushed to `ghcr.io/weekmo/routing-table-api`
5. GitHub Release created with artifacts and notes

To create a release locally:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

For container deployments, CI publishes images to GitHub Container Registry. Use pinned tags in production (for example `ghcr.io/weekmo/routing-table-api:v1.0.0`) instead of `:latest` and set `imagePullPolicy` accordingly.

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).
