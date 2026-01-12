# Contributing to Routing Table API

Contributions are welcome! Please follow these guidelines to ensure high quality code and smooth collaboration.

---

## 🚀 Quick Start

```bash
# Fork and clone
git clone https://github.com/yourusername/routing-table-api.git
cd routing-table-api
make install

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
make test-cov  # Must maintain ≥35% coverage
make lint      # Must pass
make type-check # Must pass

# Commit using conventional commits
git commit -m "feat: add amazing feature"
```

---

## ✅ Requirements

All contributions must meet these criteria:

- ✅ **All tests pass** (29/29)
- ✅ **Coverage maintained** (≥35%)
- ✅ **Linter passes** (`make lint`)
- ✅ **Type hints** for new code
- ✅ **Google-style docstrings**
- ✅ **PEP 8 compliance** (enforced by ruff)

---

## 📝 Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

| Type | Use Case |
|------|----------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code refactoring |
| `test:` | Adding/updating tests |
| `chore:` | Build/tooling changes |
| `perf:` | Performance improvement |

**Examples:**
```bash
git commit -m "feat: add IPv6 support to radix tree"
git commit -m "fix: handle edge case in LPM lookup"
git commit -m "docs: add Kubernetes deployment guide"
git commit -m "test: add concurrency tests for thread safety"
```

---

## 🧪 Testing

### Run All Tests

```bash
make test          # Run all 29 tests
make test-cov      # With coverage report
make coverage-report  # Open HTML coverage in browser
```

### Test Structure

- **test_lpm.py** - 20 unit tests for LPM algorithm
- **test_concurrency.py** - 9 thread safety tests
- **test_service.py** - Integration tests

### Coverage Requirements

- **Minimum:** 35%
- **Target:** 50%+
- **Check:** `make test-cov` shows coverage

---

## 🔧 Code Quality

### Linting

```bash
make lint        # Check with ruff
make format      # Auto-format code
make type-check  # Type checking with mypy
```

### Code Style

- **Style Guide:** PEP 8 (via ruff)
- **Type Hints:** Required for all functions
- **Docstrings:** Google-style format

**Example:**
```python
def lookup(ip: str) -> tuple[str, str, int]:
    """
    Perform longest prefix match lookup.
    
    Args:
        ip: IPv4 or IPv6 address string
        
    Returns:
        Tuple of (prefix, next_hop, metric)
        
    Raises:
        ValueError: If IP format is invalid
    """
    # implementation...
```

---

## 📋 Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/name`
3. **Make changes** following the guidelines
4. **Test** thoroughly: `make test-cov`
5. **Lint & format**: `make lint && make format`
6. **Type check**: `make type-check`
7. **Commit** with conventional commits
8. **Push** to your fork
9. **Create PR** with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issues
Closes #123

## Changes
- Change 1
- Change 2

## Testing
- [ ] Tests pass (29/29)
- [ ] Coverage maintained (≥35%)
- [ ] Linter passes
- [ ] Type checking passes

## Types of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation
```

---

## 🐛 Reporting Issues

### Bug Report

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
What should happen

## Actual Behavior
What actually happened

## Environment
- Python version
- OS (Linux/Mac/Windows)
- Docker/K8s version (if applicable)

## Logs/Output
Include relevant error messages
```

### Feature Request

```markdown
## Description
Explain the feature and why it's needed

## Use Case
When would this feature be useful?

## Proposed Solution
How should it work?

## Alternatives
Are there other approaches?
```

---

## 📚 Development Guidelines

### Adding a New Feature

1. **Create tests first** (TDD approach)
2. **Implement the feature**
3. **Ensure all tests pass**
4. **Update documentation**
5. **Add type hints**
6. **Write docstrings**

### Modifying Existing Code

1. **Run existing tests** - Ensure they pass
2. **Make changes** carefully
3. **Add/update tests** if behavior changed
4. **Check coverage** - Don't decrease it
5. **Update docs** if public API changed

### Performance Considerations

- Radix tree lookup is O(k) - don't add linear operations
- LRU cache is critical for performance - don't remove caching
- Thread safety must be maintained - use locks appropriately
- Memory usage is important - keep data structures efficient

---

## 🔍 Code Review

### What We Look For

- ✅ **Correctness** - Does it work as intended?
- ✅ **Efficiency** - Are there performance concerns?
- ✅ **Readability** - Is the code clear and maintainable?
- ✅ **Testing** - Are there adequate tests?
- ✅ **Documentation** - Is it well documented?
- ✅ **Style** - Does it follow our conventions?

### Review Process

1. **Automated checks** - Linting, testing, coverage
2. **Code review** - Manual review by maintainers
3. **Feedback loop** - Address comments/suggestions
4. **Approval** - At least one approval required
5. **Merge** - Merge to main branch

---

## 🚀 Releasing

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking API changes (v1.0.0 → v2.0.0)
- **MINOR** - New features (backward compatible) (v1.0.0 → v1.1.0)
- **PATCH** - Bug fixes (backward compatible) (v1.0.0 → v1.0.1)

### Creating a Release

1. **Update version** in relevant files
2. **Update CHANGELOG** with release notes
3. **Create git tag**: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. **Push tag**: `git push origin v1.0.0`
5. **GitHub Actions** automatically creates release with:
   - Python wheel and source distribution
   - Docker images on ghcr.io
   - Release notes on GitHub

---

## 📚 Resources

- **API Docs:** http://localhost:5000/docs (Swagger)
- **Algorithm Details:** See [README.md](README.md#-algorithm-details)
- **CI/CD Setup:** [.github/CICD_SETUP.md](.github/CICD_SETUP.md)
- **Project Structure:** See [README.md](README.md#-project-structure)

---

## ❓ Questions?

- **GitHub Issues** - Ask a question with `[question]` tag
- **Discussions** - Open GitHub Discussion for ideas
- **Email** - Contact maintainer for private matters

---

## 📄 Code of Conduct

Be respectful, inclusive, and professional. We welcome contributors of all backgrounds and experience levels.

---

**Thank you for contributing! 🙏**
# Contributing to Routing Table API

Contributions are welcome! Please follow these guidelines to ensure high quality code and smooth collaboration.

---

## 🚀 Quick Start

```bash
# Fork and clone
git clone https://github.com/yourusername/routing-table-api.git
cd routing-table-api
make install

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
make test-cov  # Must maintain ≥35% coverage
make lint      # Must pass
make type-check # Must pass

# Commit using conventional commits
git commit -m "feat: add amazing feature"
```

---

## ✅ Requirements

All contributions must meet these criteria:

- ✅ **All tests pass** (29/29)
- ✅ **Coverage maintained** (≥35%)
- ✅ **Linter passes** (`make lint`)
- ✅ **Type hints** for new code
- ✅ **Google-style docstrings**
- ✅ **PEP 8 compliance** (enforced by ruff)

---

## 📝 Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

| Type | Use Case |
|------|----------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code refactoring |
| `test:` | Adding/updating tests |
| `chore:` | Build/tooling changes |
| `perf:` | Performance improvement |

**Examples:**
```bash
git commit -m "feat: add IPv6 support to radix tree"
git commit -m "fix: handle edge case in LPM lookup"
git commit -m "docs: add Kubernetes deployment guide"
git commit -m "test: add concurrency tests for thread safety"
```

---

## 🧪 Testing

### Run All Tests

```bash
make test          # Run all 29 tests
make test-cov      # With coverage report
make coverage-report  # Open HTML coverage in browser
```

### Test Structure

- **test_lpm.py** - 20 unit tests for LPM algorithm
- **test_concurrency.py** - 9 thread safety tests
- **test_service.py** - Integration tests

### Coverage Requirements

- **Minimum:** 35%
- **Target:** 50%+
- **Check:** `make test-cov` shows coverage

---

## 🔧 Code Quality

### Linting

```bash
make lint        # Check with ruff
make format      # Auto-format code
make type-check  # Type checking with mypy
```

### Code Style

- **Style Guide:** PEP 8 (via ruff)
- **Type Hints:** Required for all functions
- **Docstrings:** Google-style format

**Example:**
```python
def lookup(ip: str) -> tuple[str, str, int]:
    """
    Perform longest prefix match lookup.
    
    Args:
        ip: IPv4 or IPv6 address string
        
    Returns:
        Tuple of (prefix, next_hop, metric)
        
    Raises:
        ValueError: If IP format is invalid
    """
    # implementation...
```

---

## 📋 Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/name`
3. **Make changes** following the guidelines
4. **Test** thoroughly: `make test-cov`
5. **Lint & format**: `make lint && make format`
6. **Type check**: `make type-check`
7. **Commit** with conventional commits
8. **Push** to your fork
9. **Create PR** with clear description

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issues
Closes #123

## Changes
- Change 1
- Change 2

## Testing
- [ ] Tests pass (29/29)
- [ ] Coverage maintained (≥35%)
- [ ] Linter passes
- [ ] Type checking passes

## Types of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation
```

---

## 🐛 Reporting Issues

### Bug Report

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2

## Expected Behavior
What should happen

## Actual Behavior
What actually happened

## Environment
- Python version
- OS (Linux/Mac/Windows)
- Docker/K8s version (if applicable)

## Logs/Output
Include relevant error messages
```

### Feature Request

```markdown
## Description
Explain the feature and why it's needed

## Use Case
When would this feature be useful?

## Proposed Solution
How should it work?

## Alternatives
Are there other approaches?
```

---

## 📚 Development Guidelines

### Adding a New Feature

1. **Create tests first** (TDD approach)
2. **Implement the feature**
3. **Ensure all tests pass**
4. **Update documentation**
5. **Add type hints**
6. **Write docstrings**

### Modifying Existing Code

1. **Run existing tests** - Ensure they pass
2. **Make changes** carefully
3. **Add/update tests** if behavior changed
4. **Check coverage** - Don't decrease it
5. **Update docs** if public API changed

### Performance Considerations

- Radix tree lookup is O(k) - don't add linear operations
- LRU cache is critical for performance - don't remove caching
- Thread safety must be maintained - use locks appropriately
- Memory usage is important - keep data structures efficient

---

## 🔍 Code Review

### What We Look For

- ✅ **Correctness** - Does it work as intended?
- ✅ **Efficiency** - Are there performance concerns?
- ✅ **Readability** - Is the code clear and maintainable?
- ✅ **Testing** - Are there adequate tests?
- ✅ **Documentation** - Is it well documented?
- ✅ **Style** - Does it follow our conventions?

### Review Process

1. **Automated checks** - Linting, testing, coverage
2. **Code review** - Manual review by maintainers
3. **Feedback loop** - Address comments/suggestions
4. **Approval** - At least one approval required
5. **Merge** - Merge to main branch

---

## 🚀 Releasing

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking API changes (v1.0.0 → v2.0.0)
- **MINOR** - New features (backward compatible) (v1.0.0 → v1.1.0)
- **PATCH** - Bug fixes (backward compatible) (v1.0.0 → v1.0.1)

### Creating a Release

1. **Update version** in relevant files
2. **Update CHANGELOG** with release notes
3. **Create git tag**: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. **Push tag**: `git push origin v1.0.0`
5. **GitHub Actions** automatically creates release with:
   - Python wheel and source distribution
   - Docker images on ghcr.io
   - Release notes on GitHub

---

## 📚 Resources

- **API Docs:** http://localhost:5000/docs (Swagger)
- **Algorithm Details:** See [README.md](README.md#-algorithm-details)
- **CI/CD Setup:** [.github/CICD_SETUP.md](.github/CICD_SETUP.md)
- **Project Structure:** See [README.md](README.md#-project-structure)

---

## ❓ Questions?

- **GitHub Issues** - Ask a question with `[question]` tag
- **Discussions** - Open GitHub Discussion for ideas
- **Email** - Contact maintainer for private matters

---

## 📄 Code of Conduct

Be respectful, inclusive, and professional. We welcome contributors of all backgrounds and experience levels.

---

**Thank you for contributing! 🙏**
