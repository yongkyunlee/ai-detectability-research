---
source_url: https://duckdb.org/2024/07/05/community-extensions.html
author: "The DuckDB team"
platform: duckdb.org (official blog)
scope_notes: "Full blog post on the DuckDB Community Extensions system. Original ~700 words; preserved nearly in full as it matches the target length well."
---

DuckDB extensions are now available as Community Extensions through a centralized repository. This system enables users to install extensions using the syntax `INSTALL extensionname FROM community`. Extension developers no longer bear the responsibility for compilation and distribution tasks.

## DuckDB Extensions

DuckDB prioritizes simplicity as a core design goal, maintaining a lightweight system suitable for constrained platforms like WebAssembly. This conflicts with requests for advanced features including spatial data analysis, vector indexes, database connectivity, and various data format support. Rather than bundling all features into one binary, DuckDB employs a powerful extension mechanism allowing users to add new functionality. Many popular features operate as extensions: the Parquet reader, JSON reader, and HTTPS/S3 connector all utilize this architecture.

Since version 0.3.2, extension discovery and installation have been simplified through a centralized repository. Installing the spatial extension requires:

```sql
INSTALL spatial; -- once
LOAD spatial;    -- on each use
```

DuckDB automatically downloads architecture-appropriate binaries and stores them in `~/.duckdb`. The system currently processes approximately six million extension downloads weekly with corresponding data transfers around 40 terabytes.

Previously, third-party extension publication was challenging, requiring developers to build for multiple platforms without official signing capabilities, forcing users to disable signature verification.

## DuckDB Community Extensions

The new Community Extensions repository provides safe software distribution similar to pip, conda, cran, npm, and brew. This lowers barriers for packaging utilities as DuckDB extensions.

The h3 extension (hierarchical hexagonal indexing for geospatial data) demonstrates the new process:

```sql
INSTALL h3 FROM community;
LOAD h3;

SELECT
    h3_latlng_to_cell(pickup_latitude, pickup_longitude, 9) AS cell_id,
    h3_cell_to_boundary_wkt(cell_id) AS boundary,
    count() AS cnt
FROM read_parquet('https://blobs.duckdb.org/data/yellow_tripdata_2010-01.parquet')
GROUP BY cell_id
HAVING cnt > 10;
```

Extension signatures verify platform compatibility and repository source. Extensions are built and signed for Linux, macOS, Windows, and WebAssembly.

### Developer Experience

The publication process requires minimal steps. Developers submit a pull request containing a `description.yml` file:

```yaml
extension:
  name: h3
  description: Hierarchical hexagonal indexing for geospatial data
  version: 1.0.0
  language: C++
  build: cmake
  license: Apache-2.0
  maintainers:
    - isaacbrodsky
repo:
  github: isaacbrodsky/h3-duckdb
  ref: 3c8a5358e42ab8d11e0253c70f7cc7d37781b2ef
```

CI builds and tests the extension automatically, after which it awaits approval and completion.

### Published Extensions

Current Community Extensions include:

| Extension | Description |
|-----------|-------------|
| crypto | Cryptographic hash functions and HMAC |
| h3 | Hierarchical hexagonal indexing for geospatial data |
| lindel | Z-Order, Hilbert, and Morton curve implementations |
| prql | Enables PRQL command execution within DuckDB |
| scrooge | Financial data aggregation functions and scanners |
| shellfs | Shell command input/output support |

**Important Security Note:** DuckDB Labs and the Foundation do not vet community extension code and cannot guarantee safety. Users can disable community extensions:

```sql
SET allow_community_extensions = false;
```

The DuckDB Community Extensions repository simplifies third-party extension installation. The team encourages developers to examine published extensions as examples and contribute via pull requests to the community repository.
