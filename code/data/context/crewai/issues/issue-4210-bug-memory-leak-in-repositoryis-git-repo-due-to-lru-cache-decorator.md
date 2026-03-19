# [BUG] Memory leak in Repository.is_git_repo() due to @lru_cache decorator

**Issue #4210** | State: open | Created: 2026-01-10 | Updated: 2026-03-14
**Author:** AI-God-Dev
**Labels:** bug, no-issue-activity

### Description

Found a memory leak in the CLI's Repository class. The is_git_repo() method uses @lru_cache which holds references to self and prevents garbage collection. There's actually a TODO comment in the code acknowledging this issue but it hasn't been fixed yet.

This becomes a problem in long-running processes or scripts that create multiple Repository instances - the memory just keeps growing.

### Steps to Reproduce

1. Create a script that instantiates Repository objects multiple times
2. Run it in a loop (like in an automated CI/CD process)
3. Monitor memory usage - it keeps climbing
4. Repository instances never get garbage collected even after going out of scope

### Expected behavior

Repository instances should be properly garbage collected when they go out of scope. The caching should happen at the instance level, not in a decorator that holds references to self.

### Screenshots/Code snippets

The problematic code is in `lib/crewai/src/crewai/cli/git.py` around line 43:

@lru_cache(maxsize=None)  # noqa: B019
def is_git_repo(self) -> bool:
    """Check if the current directory is a git repository.
    
    Notes:
      - TODO: This method is cached to avoid redundant checks, 
        but using lru_cache on methods can lead to memory leaks
    """The TODO comment shows the devs were aware of this.

### Operating System

Other (specify in additional context)

### Python Version

3.10

### crewAI Version

Latest (main branch)

### crewAI Tools Version

N/A - this is in core, not tools

### Virtual Environment

Venv

### Evidence

The decorator @lru_cache on an instance method is a well-known Python gotcha. 
The cache dictionary holds references to self, preventing the garbage collector 
from cleaning up instances. You can verify this by running a simple test with 
weakref to show instances aren't being collected.

### Possible Solution

Replace the @lru_cache decorator with instance-level caching:

- Add `self._is_git_repo_cache: bool | None = None` in __init__
- Remove the @lru_cache decorator
- Check the cache at the start of is_git_repo() and populate it if None

This keeps the same O(1) performance but allows proper garbage collection. 
Happy to submit a PR with tests if this approach sounds good.

### Additional context

This affects anyone running long-lived processes or automation scripts that 
repeatedly check git repos. The memory leak is gradual but adds up over time.

I have a complete fix ready with tests if you'd like me to submit it.

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
The `@lru_cache` decorator on instance methods is a well-known Python gotcha. The cache dictionary holds references to `self`, preventing the garbage collector from cleaning up Repository instances even after they go out of scope.

**The Fix:**
1. Removed the `@lru_cache` decorator and `functools` import
2. Added an instance-level cache attribute: `self._is_git_repo_cache: bool | None = None`
3. Modified `is_git_repo()` to check and populate the cache manually

```python
def is_git_repo(self) -> bool:
    if self._is_git_repo_cache is not None:
        return self._is_git_repo_cache

    try:
        subprocess.check_output(...)
        self._is_git_repo_cache = True
    except subprocess.CalledProcessError:
        self._is_git_repo_cache = False

    return self._is_git_repo_cache
```

**Benefits:**
- Same O(1) performance for repeated calls
- Proper garbage collection of Repository instances
- Resolves the TODO comment that was already in the code

**Testing:**
Added regression tests using `weakref` to verify instances are properly garbage collected after the fix.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.
