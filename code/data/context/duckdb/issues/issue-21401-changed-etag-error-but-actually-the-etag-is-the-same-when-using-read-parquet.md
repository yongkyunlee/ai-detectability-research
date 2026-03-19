# Changed ETag Error but actually the ETag is the same when using read_parquet()

**Issue #21401** | State: open | Created: 2026-03-16 | Updated: 2026-03-17
**Author:** thikoen
**Labels:** under review

### What happens?

When using `read_parquet()` with an S3 wildcard/pattern against S3-compatible object storage, DuckDB raises an HTTPException saying the file changed because the ETag changed.

However, the reported old/new ETag values are actually identical except for quoting:

- initial ETag: `99f26f12b7f315cbe6bde7a937cb94d9`
- new ETag: `"99f26f12b7f315cbe6bde7a937cb94d9"`

So this appears to be a false-positive ETag mismatch caused by comparing quoted vs unquoted ETag strings instead of normalized values.

This happens in a containerized Linux environment with DuckDB 1.5.0 and `httpfs` against S3-compatible storage.

### To Reproduce

A single concrete file works:

```sql
select count(*) from read_parquet('s3://example-bucket/path/to/file.parquet');
```

But the wildcard version fails:

```sql
select count(*) from read_parquet('s3://example-bucket/path/to/file_*.parquet');
```

With:

```text
_duckdb.HTTPException: HTTP Error: ETag on reading file "s3://example-bucket/path/to/file.parquet" was initially 99f26f12b7f315cbe6bde7a937cb94d9 and now it returned "99f26f12b7f315cbe6bde7a937cb94d9", this likely means the remote file has changed.
```

DuckDB suggests using:

```sql
SET unsafe_disable_etag_checks = true;
```

But that is not acceptable for workloads where Parquet files are updated frequently, because disabling ETag checks creates a real consistency risk.

Environment:
- DuckDB: 1.5.0
- Python client
- Linux container
- S3-compatible object storage
- custom endpoint
- custom CA bundle
- path-style URLs
- `httpfs` loaded

Python repro:

```python
import duckdb

con = duckdb.connect()
con.execute("install httpfs; load httpfs;")
con.execute("SET ca_cert_file='/path/to/ca-bundle.crt';")

con.execute("set s3_access_key_id='...';")
con.execute("set s3_secret_access_key='...';")
con.execute("set s3_endpoint='...';")
con.execute("set s3_use_ssl=true;")
con.execute("set s3_url_style='path';")

one = "s3://example-bucket/path/to/file.parquet"
pat = "s3://example-bucket/path/to/file_*.parquet"

print("direct:", con.execute(f"select count(*) from read_parquet('{one}')").fetchall())
print("pattern:", con.execute(f"select count(*) from read_parquet('{pat}')").fetchall())
```

### Actual result

The direct file works, but the wildcard query fails with the ETag mismatch above.

### Expected result

DuckDB should normalize ETag values before comparing them, so quoted and unquoted representations of the same ETag are treated as equal.

### Additional observations

- `glob('s3://...pattern...')` works
- `read_parquet('s3://...single-file.parquet')` works
- the failure is specific to `read_parquet()` with an S3 pattern/wildcard
- `disable_parquet_prefetching=true` alone does not fix it
- `unsafe_disable_etag_checks=true` works around the problem, but is not safe for workloads with frequently updated files

### Evidence that the backend returns a consistent quoted ETag

The same object was tested directly against the S3-compatible backend using boto3 and a presigned GET. In all successful cases, the ETag was consistently returned quoted:

```text
=== head_object ===
ETag repr: '"99f26f12b7f315cbe6bde7a937cb94d9"'
ETag raw : "99f26f12b7f315cbe6bde7a937cb94d9"

=== get_object Range=bytes=0-15 ===
ETag repr: '"99f26f12b7f315cbe6bde7a937cb94d9"'
ETag raw : "99f26f12b7f315cbe6bde7a937cb94d9"

=== get_object full headers only ===
ETag repr: '"99f26f12b7f315cbe6bde7a937cb94d9"'
ETag raw : "99f26f12b7f315cbe6bde7a937cb94d9"

=== GET Range via presigned URL ===
status: 206
ETag: '"99f26f12b7f315cbe6bde7a937cb94d9"'
```

This suggests the backend is returning a consistent quoted ETag, and DuckDB is likely normalizing or storing it inconsistently across different internal code paths.

### OS:

Linux

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Thilo Koenig

### Affiliation:

Aveniq

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**carlopi:**
I am not able to reproduce, but it would be handy to track this down.

Could you provide some extra informations?
For example, do: `CALL enable_logging('HTTP')` + run the queries + `FROM duckdb_logs_parsed('HTTP') SELECT request, response;` ?
