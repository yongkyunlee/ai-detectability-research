---
source_url: https://duckdb.org/2025/03/14/preview-amazon-s3-tables.html
author: "Sam Ansmink, Tom Ebergen, Gabor Szarnyas"
platform: duckdb.org (official blog)
scope_notes: "Full blog post on reading Amazon S3 Tables via Iceberg REST Catalogs. Original ~800 words; preserved nearly in full as it matches the target length well."
---

This post introduces a new preview capability allowing DuckDB to support Apache Iceberg REST Catalogs, which enables connections to Amazon S3 Tables and Amazon SageMaker Lakehouse.

## Iceberg Ahead!

The Iceberg open table format has grown increasingly popular among major data warehouse platforms. Databricks, Snowflake, Google BigQuery, and AWS have all implemented support for Iceberg tables. DuckDB has supported reading Iceberg tables since September 2023 via the iceberg extension. The new preview feature allows attaching to Iceberg REST catalogs. DuckDB's support for Iceberg REST Catalog endpoints in Amazon S3 Tables is the result of a collaboration between AWS and DuckDB Labs.

## Setting Up

Install the bleeding edge versions of required extensions from the core_nightly repository:

```sql
FORCE INSTALL aws FROM core_nightly;
FORCE INSTALL httpfs FROM core_nightly;
FORCE INSTALL iceberg FROM core_nightly;
```

## Reading Amazon S3 Tables with DuckDB

Querying S3 Tables requires establishing AWS credentials. Use the Secrets Manager to detect credentials from your default AWS profile:

```sql
CREATE SECRET (
    TYPE s3,
    PROVIDER credential_chain
);
```

Alternatively, set credentials manually:

```sql
CREATE SECRET (
    TYPE s3,
    KEY_ID 'AKIAIOSFODNN7EXAMPLE',
    SECRET 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    REGION 'us-east-1'
);
```

Next, point DuckDB to your S3 table bucket using the ATTACH command with the S3 Tables ARN:

```sql
ATTACH 'arn:aws:s3tables:us-east-1:111122223333:bucket/bucket-name'
    AS my_s3_tables_catalog (
        TYPE iceberg,
        ENDPOINT_TYPE s3_tables
    );
```

Display available tables:

```sql
SHOW ALL TABLES;
```

Query tables as ordinary DuckDB tables:

```sql
FROM my_s3_tables_catalog.ducks.duck_species;
```

Use `s3_tables` endpoint type for basic read access to a single S3 table bucket. Use `glue` endpoint type for a unified view across all tabular data in AWS:

```sql
ATTACH 'account_id:s3tablescatalog/namespace_name'
AS (
    TYPE iceberg,
    ENDPOINT_TYPE glue
);
```

## Schema Evolution

A key Iceberg feature is schema evolution -- the ability to follow changes in table schema. Adding a new column in Athena and inserting additional data:

```sql
ALTER TABLE duck_species
    ADD COLUMNS (conservation_status STRING);

INSERT INTO duck_species VALUES
    (1, 'Anas eatoni', 'Eaton''s pintail', 'Vulnerable'),
    (2, 'Histrionicus histrionicus', 'Harlequin duck', 'Least concern');
```

Running the query again in DuckDB automatically picks up the new column:

```
┌───────┬───────────────────────────┬─────────────────┬─────────────────────┐
│  id   │       english_name        │   latin_name    │ conservation_status │
│ int32 │          varchar          │     varchar     │       varchar       │
├───────┼───────────────────────────┼─────────────────┼─────────────────────┤
│     1 │ Anas eatoni               │ Eaton's pintail │ Vulnerable          │
│     2 │ Histrionicus histrionicus │ Harlequin duck  │ Least concern       │
│     0 │ Anas nivis                │ Snow duck       │ NULL                │
└───────┴───────────────────────────┴─────────────────┴─────────────────────┘
```

## Conclusion

The preview release of the DuckDB iceberg extension enables direct reading of tables using Iceberg REST endpoints, facilitating queries against Amazon S3 Tables and Amazon SageMaker Lakehouse. The extension is currently experimental and under active development, with a stable release planned later this year.
