## GitHub Actions CI/CD Setup Guide

### Overview

This project uses GitHub Actions for continuous integration and deployment with the following workflows:

1. **CI Workflow** (`.github/workflows/ci.yml`) - Main test and quality checks
2. **Coverage Badge** (`.github/workflows/coverage-badge.yml`) - Auto-updates coverage badge
3. **Dependabot** (`.github/dependabot.yml`) - Automated dependency updates

### Workflows

#### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main`, `master`, `develop`, or `refactor/*` branches
- Pull requests to `main`, `master`, `develop`

**Jobs:**

**a) Test Matrix**
- Runs on Python 3.8, 3.9, 3.10, 3.11, 3.12
- Executes unit and concurrency tests
- Generates coverage reports
- Uploads coverage to Codecov (Python 3.11 only)

**b) Code Quality (lint)**
- Runs ruff linter
- Checks code formatting
- Runs mypy type checker

**c) Security Scan**
- Safety check for vulnerable dependencies
- Bandit security scan for code vulnerabilities

**d) Build**
- Builds Docker container images
- Validates multi-stage Dockerfile
- Uses layer caching for faster builds

#### 2. Coverage Badge Workflow (`coverage-badge.yml`)

**Triggers:** Push to `main`/`master` branches

**Actions:**
- Runs tests with coverage
- Generates SVG badge
- Commits badge to repository

### Setup Instructions

#### Required Secrets

Add these to your GitHub repository secrets (Settings → Secrets and variables → Actions):

1. **`CODECOV_TOKEN`** (Optional but recommended)
   - Sign up at https://codecov.io
   - Add your repository
   - Copy the token
   - Add to GitHub secrets as `CODECOV_TOKEN`

#### Alternative: Shields.io Dynamic Badge

If you don't want to use Codecov, you can use shields.io with a GitHub Gist:

1. **Create a GitHub Gist:**
   - Go to https://gist.github.com
   - Create a new gist named `coverage-badge.json`
   - Content:
     ```json
     {
       "schemaVersion": 1,
       "label": "coverage",
       "message": "39.4%",
       "color": "yellow"
     }
     ```

2. **Get Gist ID:**
   - After creating, copy the gist ID from URL
   - Example: `https://gist.github.com/weekmo/abc123def456` → ID is `abc123def456`

3. **Update README.md:**
   - Replace `GIST_ID` in coverage badge URL with your actual gist ID
   - The workflow will update this gist automatically

4. **Create GitHub Token:**
   - Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `gist` scope
   - Add to repository secrets as `GIST_SECRET`

5. **Update `coverage-badge.yml`:**
   Add this step before "Commit badge":
   ```yaml
   - name: Update gist with coverage
     uses: schneegans/dynamic-badges-action@v1.7.0
     with:
       auth: ${{ secrets.GIST_SECRET }}
       gistID: YOUR_GIST_ID
       filename: coverage-badge.json
       label: coverage
       message: ${{ env.COVERAGE }}%
       color: ${{ env.COVERAGE_COLOR }}
   ```

### Badge URLs

Once workflows run successfully, update README.md badges:

**Tests Badge (Dynamic):**
```markdown
![Tests](https://github.com/USERNAME/REPO/actions/workflows/ci.yml/badge.svg)
```

**Coverage Badge Options:**

Option A - Codecov (recommended):
```markdown
![Coverage](https://codecov.io/gh/USERNAME/REPO/branch/main/graph/badge.svg)
```

Option B - Shields.io with Gist:
```markdown
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/coverage-badge.json)
```

Option C - Local SVG (from coverage-badge.yml):
```markdown
![Coverage](./coverage-badge.svg)
```

### Workflow Features

#### Caching
- Python dependencies cached via `setup-python@v5`
- Docker layers cached for faster builds

#### Matrix Testing
- Tests run on Python 3.8 through 3.12
- Ensures compatibility across versions

#### Security
- Automated dependency vulnerability scanning
- Code security analysis with Bandit

#### Performance
- `fail-fast: false` - All Python versions tested even if one fails
- Parallel job execution
- Efficient caching strategies

### Best Practices Implemented

1. ✅ **Version Pinning**: Uses latest stable action versions (v4, v5)
2. ✅ **Permissions**: Minimal required permissions per job
3. ✅ **Caching**: Dependency and build layer caching
4. ✅ **Matrix Testing**: Multiple Python versions
5. ✅ **Code Quality**: Linting, formatting, type checking
6. ✅ **Security**: Vulnerability scanning
7. ✅ **Coverage**: Automated coverage tracking and badges
8. ✅ **Container Builds**: Validates deployment artifacts
9. ✅ **Dependabot**: Automated dependency updates

### Triggering Workflows

**Manual Trigger:**
- Go to Actions tab → Select workflow → Run workflow

**Skip CI:**
- Add `[skip ci]` or `[ci skip]` to commit message

**Required Status Checks:**
- Go to Settings → Branches → Branch protection rules
- Add rule for `main` branch
- Enable "Require status checks to pass before merging"
- Select: `Test (Python 3.11)`, `Code Quality`, `Build Container`

### Monitoring

**View Workflow Runs:**
- GitHub repository → Actions tab
- Click on workflow run for detailed logs

**Coverage Reports:**
- Codecov: https://codecov.io/gh/USERNAME/REPO
- Or view coverage.svg in repository

**Build Status:**
- Badge shows current status (passing/failing)
- Click badge to see workflow runs

### Troubleshooting

**Workflow fails on first run:**
- Normal! Some secrets may need to be configured
- CODECOV_TOKEN is optional - workflow will continue if missing
- Check logs for specific failures

**Coverage badge not updating:**
- Ensure `coverage-badge.yml` has `contents: write` permission
- Check if gist secret is configured correctly
- Verify Python 3.11 test job completed successfully

**Tests pass locally but fail in CI:**
- Check Python version differences
- Verify all dependencies in `pyproject.toml`
- Review test file paths (case-sensitive in Linux CI)

### Local Testing

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
sudo apt install act  # Linux

# Run CI workflow
act -j test

# Run specific job
act -j lint

# List workflows
act -l
```

### Continuous Deployment (Future)

To add CD for automatic releases:

1. Create `.github/workflows/release.yml`
2. Trigger on version tags (e.g., `v*.*.*`)
3. Build and push Docker images to registry
4. Create GitHub release with changelog
5. Publish to PyPI (if public package)

Example trigger:
```yaml
on:
  push:
    tags:
      - 'v*.*.*'
```
