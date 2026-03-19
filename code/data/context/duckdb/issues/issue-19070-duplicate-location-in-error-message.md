# Duplicate location in error message

**Issue #19070** | State: open | Created: 2025-09-20 | Updated: 2026-03-18
**Author:** dpxcc
**Labels:** under review

### What happens?

Location is duplicated in error message

### To Reproduce

```
auto res = connection.Query("aaaaa");
if (res->HasError()) {
    res->ThrowError();
}
```
now outputs
```
Parser Error: syntax error at or near "aaaaa"

LINE 1: aaaaa
        ^

LINE 1: aaaaa
        ^
```
which used to be
```
Parser Error: syntax error at or near "aaaaa"

LINE 1: aaaaa
        ^
```

### OS:

Linux

### DuckDB Version:

1.4.0

### DuckDB Client:

n/a

### Hardware:

_No response_

### Full Name:

Cheng Chen

### Affiliation:

Mooncake Labs

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**KryptosAI:**
I'd like to take a crack at this one.

After tracing the code, the root cause appears to be in `ErrorData::AddErrorLocation()` (`src/common/error_data.cpp`). When `AddErrorLocation` formats the `LINE 1: ...` block into `raw_message`, it reads the `"position"` key from `extra_info` but never erases it afterward. So when `ThrowError()` re-throws the exception (encoding both the mutated `raw_message` and the still-present `"position"` key), any subsequent catch → `ErrorData(ex)` → `AddErrorLocation()` cycle appends the location block a second time.

The fix would be to erase `"position"` from `extra_info` after it's been consumed in `AddErrorLocation`, preventing double-application.

I'll put together a PR with the fix and a test.
