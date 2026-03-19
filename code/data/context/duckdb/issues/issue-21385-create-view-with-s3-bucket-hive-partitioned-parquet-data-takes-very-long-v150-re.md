# CREATE VIEW with S3-Bucket, Hive-Partitioned Parquet Data takes very long | v1.5.0 Regression

**Issue #21385** | State: open | Created: 2026-03-15 | Updated: 2026-03-18
**Author:** its-felix
**Labels:** under review

### What happens?

After updating from v1.4.4 to v1.5.0, `CREATE VIEW` statements with hive-partitioned parquet data in S3 take very long.

Up until v1.4.4, I used to have `CREATE VIEW` statements like the following:
```sql
2026-03-15T04:21:41+01:00 Executing query: CREATE OR REPLACE VIEW flight_variant_history AS SELECT * FROM read_parquet('s3://my-bucket/history/airline_id=*/number_mod_10=*/*.parquet', hive_partitioning = true, hive_types = {'airline_id': UUID, 'number_mod_10': USMALLINT})
2026-03-15T04:21:41+01:00 Executed query, took 420.0875ms
2026-03-15T04:21:42+01:00 Executing query: 
CREATE OR REPLACE VIEW flight_variant_history_latest AS
SELECT
	*,
	CONCAT(
		IF(seats_first = 0, '', CONCAT('F', seats_first)),
		IF(seats_business = 0, '', CONCAT('C', seats_business)),
		IF(seats_premium = 0, '', CONCAT('E', seats_premium)),
		IF(seats_economy = 0, '', CONCAT('M', seats_economy))
	) AS aircraft_configuration_version
FROM read_parquet('s3://my-bucket/latest/year_utc=*/month_utc=*/day_utc=*/*.parquet', hive_partitioning = true, hive_types = {'year_utc': USMALLINT, 'month_utc': USMALLINT, 'day_utc': USMALLINT})

2026-03-15T04:21:42+01:00 Executed query, took 648.418709ms
```

Running the same queries in v1.5.0 takes *much* longer (3.5 minutes vs 1 second):
```sql
2026-03-15T04:13:13+01:00 Executing query: CREATE OR REPLACE VIEW flight_variant_history AS SELECT * FROM read_parquet('s3://my-bucket/history/airline_id=*/number_mod_10=*/*.parquet', hive_partitioning = true, hive_types = {'airline_id': UUID, 'number_mod_10': USMALLINT})
2026-03-15T04:13:13+01:00 Executed query, took 1m1.44280475s
2026-03-15T04:14:15+01:00 Executing query: 
CREATE OR REPLACE VIEW flight_variant_history_latest AS
SELECT
	*,
	CONCAT(
		IF(seats_first = 0, '', CONCAT('F', seats_first)),
		IF(seats_business = 0, '', CONCAT('C', seats_business)),
		IF(seats_premium = 0, '', CONCAT('E', seats_premium)),
		IF(seats_economy = 0, '', CONCAT('M', seats_economy))
	) AS aircraft_configuration_version
FROM read_parquet('s3://my-bucket/latest/year_utc=*/month_utc=*/day_utc=*/*.parquet', hive_partitioning = true, hive_types = {'year_utc': USMALLINT, 'month_utc': USMALLINT, 'day_utc': USMALLINT})

2026-03-15T04:14:15+01:00 Executed query, took 2m25.940457416s
```

This only happens when the partitions are explicitly named in the path (like above). When I remove the partitions from the path with `**` the timing is back to normal levels in v1.5.0:
```sql
2026-03-15T04:24:31+01:00 Executing query: CREATE OR REPLACE VIEW flight_variant_history AS SELECT * FROM read_parquet('s3://my-bucket/history/**/*.parquet', hive_partitioning = true, hive_types = {'airline_id': UUID, 'number_mod_10': USMALLINT})
2026-03-15T04:24:31+01:00 Executed query, took 434.444834ms
2026-03-15T04:24:32+01:00 Executing query: 
CREATE OR REPLACE VIEW flight_variant_history_latest AS
SELECT
	*,
	CONCAT(
		IF(seats_first = 0, '', CONCAT('F', seats_first)),
		IF(seats_business = 0, '', CONCAT('C', seats_business)),
		IF(seats_premium = 0, '', CONCAT('E', seats_premium)),
		IF(seats_economy = 0, '', CONCAT('M', seats_economy))
	) AS aircraft_configuration_version
FROM read_parquet('s3://my-bucket/latest/**/*.parquet', hive_partitioning = true, hive_types = {'year_utc': USMALLINT, 'month_utc': USMALLINT, 'day_utc': USMALLINT})

2026-03-15T04:24:32+01:00 Executed query, took 618.566458ms
```

### To Reproduce

- Create a dataset with a suitable number of partition values (i.e. daily partition with data over 2+ years)
- Make sure the files in every partition are not super small (a few MB should be enough)
- Make sure the dataset lives in some remote storage (i.e. S3) to create some latency
- Issue a create view statement with explicit partition naming like below:

```sql
CREATE OR REPLACE VIEW flight_variant_history_latest AS
SELECT *
FROM read_parquet('s3://your-bucket/dataset/date=*/*.parquet`, hive_partitioning = true, hive_types = {'date': DATE});
```

### OS:

macOS, linux

### DuckDB Version:

v1.5.0

### DuckDB Client:

Go, CLI

### Hardware:

MacBook Pro M1, AWS Lambda (ARM)

### Full Name:

Felix Wollschlaeger

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**Mytherin:**
Thanks for the report! This is likely the same issue as https://github.com/duckdb/duckdb/issues/21347. As a work-around you can run `SET s3_allow_recursive_globbing = false; `. We'll have a fix out for v1.5.1.

**carlopi:**
@its-felix: this was indeed connected to hierarchical globbing, as per @Mytherin workaround. In https://github.com/duckdb/duckdb-httpfs/pull/284 we worked towards improving the situation, and there is an in-flight PR with many more tests in actual public-available S3 buckets (at https://github.com/duckdb/duckdb-httpfs/pull/286).

Based on that PR, we have a signed development version of `httpfs` that you can install like:
```
FORCE INSTALL httpfs FROM core_nightly VERSION '927e499';
```
This will override the extension you might have locally.
Note this version is available and valid only for duckdb v1.5.0.

Then, if you could check on the reported bucket, it's expected the problem you reported should go away with default settings.

Expectation (based on the tests I ran, I am not exactly sure about the bucket setup) is that this issue should be solved via that build.
Validation would be great, thanks. The fixed version will be then part of the default extensions for v1.5.1.

To revert and restore the default `httpfs` extension, `FORCE INSTALL httpfs FROM core;`.

**its-felix:**
Hey @carlopi , thanks for the update!
In my real environment I'm actually using a selfbuilt version of DuckDB with the extensions I need statically linked (including httpfs), because I'm running DuckDB in AWS Lambda where dynamically loading extensions is not supported (see https://github.com/explore-flights/libduckdb ).

As far as I understand, all I would have to do in this case would be to replace the include:

```
include("/build/duckdb/.github/config/extensions/httpfs.cmake")
```
(this points to https://github.com/duckdb/duckdb/blob/main/.github/config/extensions/httpfs.cmake)

with 
```
duckdb_extension_load(httpfs
    LOAD_TESTS
    GIT_URL https://github.com/duckdb/duckdb-httpfs
    GIT_TAG 927e4991d8f31a58dda27cfe8616e3851276eea6
    APPLY_PATCHES
)
```

is that correct?
