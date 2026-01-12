# Cleanup Implementation Plan

**Date:** 2026-01-12  
**Status:** Ready to Execute  
**Estimated Time:** 5 minutes

---

## Current Status After `make clean`

✅ **Completed by make clean:**
- Deleted all `__pycache__/` directories from filesystem
- Git now shows 8 .pyc files as deleted (need to commit)

⚠️ **Still Remaining:**
1. Commit deletion of .pyc files to git
2. Remove empty `service/utils/` directory
3. Remove unused `Optional` import from `service/lib/data.py`
4. Remove unused `lpm_itr()` function from `service/lib/data.py`

---

## Step 1: Commit Cache File Deletions (1 min)

The `make clean` deleted the files, now commit the deletions:

```bash
git add -u service/lib/__pycache__/ tests/__pycache__/
git commit -m "chore: Remove cached Python files from git tracking

- Remove 8 .pyc files that were accidentally committed
- Files are already in .gitignore and deleted by make clean
- Keeps git history clean of binary cache files"
```

**Verification:**
```bash
git ls-files | grep -E "(__pycache__|\.pyc)" | wc -l
# Should output: 0
```

---

## Step 2: Remove Empty service/utils/ Directory (30 sec)

```bash
rmdir service/utils/
git status  # Should show nothing about utils/
```

**Verification:**
```bash
ls service/utils/ 2>&1
# Should output: No such file or directory
```

---

## Step 3: Remove Unused Import from service/lib/data.py (1 min)

**File:** `service/lib/data.py` line 6

**Current:**
```python
"""Data loading and routing table utilities."""

import polars as pl
import ipaddress
import sys
from typing import Optional  # ← REMOVE THIS
from service.lib.radix_tree import RadixTree
```

**Change to:**
```python
"""Data loading and routing table utilities."""

import polars as pl
import ipaddress
import sys
from service.lib.radix_tree import RadixTree
```

**Verification:**
```bash
grep "Optional" service/lib/data.py
# Should output: (nothing)
```

---

## Step 4: Remove Unused lpm_itr() Function (1 min)

**File:** `service/lib/data.py` lines 123-150

**Remove entire function:**
```python
def lpm_itr(df: pl.DataFrame, ipaddr: ipaddress.IPv4Network) -> pl.DataFrame:
    """
    Perform LPM using iteration (legacy method).
    
    This is the slower O(n) approach, kept for compatibility.
    Consider using radix tree lookup instead.
    ...entire function...
    """
```

**Verification:**
```bash
grep -n "def lpm_itr" service/lib/data.py
# Should output: (nothing)

grep "lpm_itr" service/**/*.py tests/**/*.py
# Should output: (nothing)
```

---

## Step 5: Run Tests (1 min)

```bash
python3 -m pytest tests/test_lpm.py tests/test_concurrency.py -v

# Expected: 29 passed in ~0.5s
```

---

## Step 6: Final Commit (30 sec)

```bash
git add service/lib/data.py
git commit -m "refactor: Remove unused code and imports

- Remove unused Optional import from data.py
- Remove unused lpm_itr() function (legacy O(n) method)
- All functionality preserved (29 tests passing)
- Code is cleaner and more maintainable"
```

---

## Verification Checklist

After completing all steps:

```bash
# 1. No pycache in git
git ls-files | grep -E "(__pycache__|\.pyc)"
# Output: (empty)

# 2. No empty utils directory
ls -d service/utils/
# Output: ls: cannot access 'service/utils/': No such file or directory

# 3. No unused imports
grep "Optional" service/lib/data.py
# Output: (empty)

# 4. No unused functions
grep "lpm_itr" service/lib/data.py
# Output: (empty)

# 5. All tests pass
python3 -m pytest tests/test_lpm.py tests/test_concurrency.py -v
# Output: 29 passed in ~0.5s

# 6. Clean git status (except CLEANUP_ANALYSIS.md)
git status --short
# Output: ?? CLEANUP_ANALYSIS.md
#         ?? CLEANUP_IMPLEMENTATION_PLAN.md
```

---

## Summary

**Total Changes:**
- ✅ 8 .pyc files removed from git
- ✅ 1 empty directory removed
- ✅ 1 unused import removed
- ✅ 1 unused function removed (~28 lines)
- ✅ 2 commits created

**Impact:**
- Git history: Cleaner (no binary files)
- Code quality: Higher (no dead code)
- Maintainability: Better (less confusion)
- Functionality: Unchanged (all tests pass)

**Time:** ~5 minutes total

---

## Notes

- ✅ `lpm_lookup_radix` is USED (main.py:288) - keep it
- ✅ `lpm_map` is USED (main.py:136) - keep it  
- ✅ All other functions are used
- ⚠️ `CLEANUP_ANALYSIS.md` can be added to git or deleted (your choice)
- ⚠️ `CLEANUP_IMPLEMENTATION_PLAN.md` can be added to git or deleted (your choice)
