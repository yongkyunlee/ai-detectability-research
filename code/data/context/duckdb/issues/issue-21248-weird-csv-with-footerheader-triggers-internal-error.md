# Weird CSV with footer/header triggers internal error

**Issue #21248** | State: closed | Created: 2026-03-09 | Updated: 2026-03-12
**Author:** matixlol
**Labels:** reproduced

### What happens?

When trying to parse two CSV files with invalid footers and `union_by_name=true`, DuckDB crashes.

### To Reproduce

Full repro repo: https://github.com/matixlol/duckdb-union-by-name-repro

## CSV1
```
id_comercio|id_bandera|comercio_cuit|comercio_razon_social|comercio_bandera_nombre|comercio_bandera_url|comercio_ultima_actualizacion|comercio_version_sepa
2004|1|30710411502|"Coppel S.A."|"Coppel S.A."|www.coppel.com.ar|2021-04-30T19:51:27.730|1.0

"Ultima actualizacion: 2025-05-28T18:00:02-03:00"
```
## CSV2
```
id_comercio|id_bandera|comercio_cuit|comercio_razon_social|comercio_bandera_nombre|comercio_bandera_url|comercio_ultima_actualizacion|comercio_version_sepa
12|1|30548083156|COTO|COTO|http://www.coto.com.ar/|2025-05-29T01:05:48-03:00|1.0

Ultima actualizacion: 2025-05-29T01:05:48-03:00
```
## repro

```
duckdb -c "DESCRIBE SELECT * FROM read_csv(['normal.csv','quoted-footer-bom.csv'], union_by_name = true, ignore_errors = true, strict_mode = false, filename = true, all_varchar = true);"
```

### OS:

Apple aarch64

### DuckDB Version:

1.4.4

### DuckDB Client:

CLI & Node

### Hardware:

_No response_

### Full Name:

Matias

### Affiliation:

Hobbist

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@matixlol Thanks, I could reproduce this both on DuckDB v1.4 and v1.5.
