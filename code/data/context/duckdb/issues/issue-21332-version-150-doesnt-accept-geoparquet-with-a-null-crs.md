# Version 1.5.0 doesn't accept geoparquet with a null CRS

**Issue #21332** | State: closed | Created: 2026-03-12 | Updated: 2026-03-18
**Author:** philippechataignon
**Labels:** reproduced

### What happens?

According [geoparquet specification](https://geoparquet.org/releases/v1.1.0), CRS field can be *null*. It indicates that there is no CRS assigned to this column (CRS is undefined or unknown) and it's different as no CRS which means default value OGC:CRS84. Actually, version 1.5.0 returns an error (but \< 1.5.0 doesn't) when geoparquet file has a null CRS.

### To Reproduce

```         
from 'https://raw.githubusercontent.com/geoarrow/geoarrow-data/v0.2.0/example/files/example_point_geo.parquet';
```

```
Invalid Input Error:
Geoparquet column 'geometry' has invalid CRS
```

### OS:

Linux Debian 13 x86_64

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Philippe Chataignon

### Affiliation:

Individual

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Fixed by https://github.com/duckdb/duckdb/pull/21333 - thanks
