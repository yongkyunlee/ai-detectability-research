# Compiling DuckDB 1.5 with certain `BUILD_EXTENSIONS` (e.g. `delta`) produces unusable binary

**Issue #21402** | State: closed | Created: 2026-03-16 | Updated: 2026-03-16
**Author:** OddBloke
**Labels:** needs triage

### What happens?

We build DuckDB with:

```
make -C . -j14 'V=1' 'GEN=ninja' 'BUILD_EXTENSIONS=autocomplete;httpfs;icu;json;tpch;delta'
```

and up to 1.5, this has been working (albeit using `CORE_EXTENSIONS` previously). However, when our automation attempted a build of 1.5, the resulting binary it built always errors out with:

```
Extension Autoloading Error: An error occurred while trying to automatically install the required extension 'parquet':
Extension "/root/.duckdb/extensions/v1.5.0/linux_amd64/parquet.duckdb_extension" not found.
Extension "parquet" is an existing extension.
```

The only fix I've found is to drop `delta` from our list of `BUILD_EXTENSIONS`, but there are no build errors when it's included to suggest why that might be the fix.

(As I only figured that out by iterating over the set of extensions we build, it's not clear to me if this is a `delta` problem, or a class of problem affecting other extensions we don't build, etc., hence filing this issue in core.)

### To Reproduce

Our package is built using the definition at https://github.com/wolfi-dev/os/blob/main/duckdb.yaml with this diff applied for 1.5.0:

```
diff --git a/os/duckdb.yaml b/os/duckdb.yaml
index 090c701f1b..48e3ce4e8e 100644
--- a/os/duckdb.yaml
+++ b/os/duckdb.yaml
@@ -1,7 +1,7 @@
 package:
   name: duckdb
-  version: "1.4.4"
-  epoch: 1 # go/wolfi-rsc/duckdb
+  version: "1.5.0"
+  epoch: 0 # go/wolfi-rsc/duckdb
   description: "DuckDB is an analytical in-process SQL database management system"
   copyright:
     - license: MIT
@@ -31,12 +31,12 @@ pipeline:
     with:
       repository: https://github.com/duckdb/duckdb
       tag: v${{package.version}}
-      expected-commit: 6ddac802ffa9bcfbcc3f5f0d71de5dff9b0bc250
+      expected-commit: 3a3967aa8190d0a2d1931d4ca4f5d920760030b4
 
   - uses: autoconf/make
     with:
       opts: |
-        GEN=ninja CORE_EXTENSIONS='autocomplete;httpfs;icu;json;tpch;delta'
+        GEN=ninja BUILD_EXTENSIONS='autocomplete;httpfs;icu;json;tpch;delta'
 
   - runs: install -Dm755 build/release/duckdb "${{targets.destdir}}"/usr/bin/duckdb
```

### OS:

Wolfi

### DuckDB Version:

25.0

### DuckDB Client:

N/A

### Hardware:

_No response_

### Full Name:

Dan Watkins

### Affiliation:

Chainguard

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**carlopi:**
Could you try the same, but adding parquet to the list?

Like:
```
BUILD_EXTENSIONS=autocomplete;httpfs;icu;json;tpch;parquet;delta'
```

Note: `parquet` being a `delta` dependency needs to come before `delta` in the list.

This is an undocumented hidden dependency, but this should allow you to move forward.

**OddBloke:**
This fixed our build, thanks!
