# SIGILL in the testcase test/sqlite/test_sqllogictest.cpp

**Issue #21262** | State: open | Created: 2026-03-10 | Updated: 2026-03-16
**Author:** yurivict
**Labels:** needs triage

### What happens?

```
/usr/ports/databases/duckdb/work/duckdb-1.5.0/test/sqlite/test_sqllogictest.cpp:212: FAILED:
  {Unknown expression after the reported line}
due to a fatal error condition:
  SIGILL - Illegal instruction signal
```

Version: 1.5.0
FreeBSD 15 STABLE

### To Reproduce

run tests

### OS:

FreeBSD 15 STABLE

### DuckDB Version:

1.5.0

### DuckDB Client:

C++

### Hardware:

_No response_

### Full Name:

Yuri Vic

### Affiliation:

n/a

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**strophy:**
@yurivict Are you using gcc 15? I'm hitting the same problem on Alpine Linux, this patch fixes it for me:
```patch
diff --git a/src/execution/operator/join/physical_iejoin.cpp b/src/execution/operator/join/physical_iejoin.cpp
index fd392f3b9d..ecb89363ad 100644
--- a/src/execution/operator/join/physical_iejoin.cpp
+++ b/src/execution/operator/join/physical_iejoin.cpp
@@ -1367,6 +1367,9 @@ void IEJoinGlobalSourceState::Initialize() {
 
 bool IEJoinGlobalSourceState::TryPrepareNextStage() {
        //      Inside lock
+       if (stage == IEJoinSourceStage::DONE) {
+               return true;
+       }
        const auto stage_count = GetStageCount(stage);
        const auto stage_next = GetStageNext(stage).load();
        if (stage_next >= stage_count) {
```

**yurivict:**
I use clang-20.

**strophy:**
Does the patch fix it for you?
