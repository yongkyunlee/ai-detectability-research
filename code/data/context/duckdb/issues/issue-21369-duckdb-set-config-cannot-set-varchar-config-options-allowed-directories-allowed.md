# `duckdb_set_config` cannot set `VARCHAR[]` config options (`allowed_directories`, `allowed_paths`)

**Issue #21369** | State: open | Created: 2026-03-13 | Updated: 2026-03-13
**Author:** joshkaplinsky
**Labels:** under review

### What happens?

`duckdb_set_config` accepts `const char *` for the value parameter, which works for scalar settings but doesn't handle `VARCHAR[]` options like `allowed_directories` and `allowed_paths`. These settings are registered as valid startup config flags via `duckdb_get_config_flag`, so it's reasonable to expect them to work with `duckdb_set_config`.

### To Reproduce

```ts
import { DuckDBInstance } from '@duckdb/node-api';

// Fails with "Failed to set config"
await DuckDBInstance.create(':memory:', { allowed_directories: '/tmp' }); // Note Node API only alows 
```

```ts
// Workaround:
const instance = await DuckDBInstance.create(':memory:');
const conn = await instance.connect();
await conn.run("SET allowed_directories = ['/tmp']");
await conn.run("SET enable_external_access = false");
await conn.run("SET lock_configuration = true");
```

### OS:

macOS (Darwin 25.2.0)

### DuckDB Version:

v1.5.0

### DuckDB Client:

Node API (1.5.0-r.1)

### Hardware:

_No response_

### Full Name:

Josh Kaplinsky

### Affiliation:

Immuta

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes
