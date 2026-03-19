# Moving from pandas to DuckDB for validating large CSV/Parquet files on S3, worth the complexity?

**r/dataengineering** | Score: 39 | Comments: 57 | Date: 2026-03-06
**Author:** CreamRevolutionary17
**URL:** https://www.reddit.com/r/dataengineering/comments/1rm828b/moving_from_pandas_to_duckdb_for_validating_large/

We currently load files into pandas DataFrame to run quality checks (null counts, type checks, range validation, regex patterns). Works fine for smaller files but larger CSVs are killing memory.

Looking at DuckDB since it can query S3 directly without hardcoding them.

Has anyone replaced a pandas-based validation pipeline with duckdb?
