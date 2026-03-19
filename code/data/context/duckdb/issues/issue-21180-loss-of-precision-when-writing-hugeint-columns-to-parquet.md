# Loss of Precision when Writing HUGEINT Columns to Parquet

**Issue #21180** | State: open | Created: 2026-03-04 | Updated: 2026-03-06
**Author:** zdenko-tm
**Labels:** reproduced

### What happens?

When a table containing a HUGEINT column is written to a Parquet file, the HUGEINT value is incorrectly converted to a floating-point DOUBLE, which results in a loss of precision. For example, inserting the large value 999999999999999999999999999999 and then reading it back yields 1e+30.

I believe the issue stems from the following:

The HUGEINT logical type is [mapped to the INT128 physical type](https://github.com/duckdb/duckdb/blob/main/src/common/types.cpp#L95), similar to DECIMAL. However, unlike DECIMAL, when writing INT128 for a HUGEINT to Parquet, it appears to be [converted into a floating-point DOUBLE](https://github.com/duckdb/duckdb/blob/main/extension/parquet/parquet_writer.cpp#L90) instead of being stored as a fixed-length byte array.

### To Reproduce

```
duckdb -c "
CREATE TABLE test (huge_integer HUGEINT);
INSERT INTO test VALUES ('999999999999999999999999999999'::HUGEINT);
COPY test TO 'hugeint.parquet' (FORMAT 'parquet');
SELECT * FROM 'hugeint.parquet';
"
```

Actual Result
```
┌──────────────┐
│ huge_integer │
│    double    │
├──────────────┤
│        1e+30 │
└──────────────┘
```

Inspection of the Parquet file's schema using parquet-tools confirms that the underlying physical type for the HUGEINT column is DOUBLE:
```
$ parquet-tools inspect hugeint.parquet
########## file meta data ##########
created_by: DuckDB version v1.1.3 (build 19864453f7)
num_columns: 1
num_rows: 1
num_row_groups: 1
format_version: 1.0
serialized_size: 140

########## Columns ##########
huge_integer

########## Column(huge_integer) ##########
name: huge_integer
path: huge_integer
max_definition_level: 1
max_repetition_level: 0
physical_type: DOUBLE
logical_type: None
converted_type (legacy): NONE
compression: SNAPPY (space_saved: -6%)
```

### OS:

Linux 5.15.0-171-generic #181-Ubuntu SMP Fri Feb 6 22:44:50 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux

### DuckDB Version:

latest (1.4.4)

### DuckDB Client:

NA - can be reproduced with duckdb CLI tool

### Hardware:

_No response_

### Full Name:

Zdenko Pulitika

### Affiliation:

Thought Machine

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**SartorialOffense:**
Parquet can't store 128 bit int's directly so duckdb would need to do a conversion. You can store Decimal(38,0) which should get you there though. I have not done this myself.

2^128=3.4028237e+38

**adamshone:**
> Parquet can't store 128 bit int's directly so duckdb would need to do a conversion. You can store Decimal(38,0) which should get you there though. I have not done this myself.
> 
> 2^128=3.4028237e+38

This does work, but the reason it works is that Decimals [large enough to use INT128 as their physical type](https://github.com/duckdb/duckdb/blob/main/src/common/types.cpp#L112) are mapped to a fixed length byte array when written to Parquet [here](https://github.com/duckdb/duckdb/blob/main/extension/parquet/parquet_writer.cpp#L129).

But HUGEINTs are always converted to doubles when written to Parquet [here](https://github.com/duckdb/duckdb/blob/main/extension/parquet/parquet_writer.cpp#L90).

This seems inconsistent given that they have the same underlying physical type, and it doesn't seem right to represent an int value as a floating point because of precision loss.
