# Show HN: Csvdb – Git-friendly CSV directories that convert to SQLite or DuckDB

**HN** | Points: 3 | Comments: 1 | Date: 2026-02-04
**Author:** jeff-gorelick
**HN URL:** https://news.ycombinator.com/item?id=46889787
**Link:** https://github.com/jeff-gorelick/csvdb

I built csvdb because I kept running into the same problem: I had small relational datasets (config tables, rate tables, seed data) that I wanted to version control, but SQLite files produce useless git diffs.csvdb converts between a directory of CSV files and SQLite&#x2F;DuckDB databases. The CSV side is the source of truth you commit to git. The database side is what you query.  csvdb to-csvdb mydb.sqlite    # export to CSV directory
  vim mydb.csvdb&#x2F;rates.csv      # edit data
  git diff mydb.csvdb&#x2F;          # meaningful row-level diffs
  csvdb to-sqlite mydb.csvdb&#x2F;   # rebuild database

The key design decision is deterministic output. Rows are sorted by primary key, so identical data always produces identical CSV files. This means git diffs show only actual data changes, not row reordering noise.A few details that took some thought:- NULL handling: CSV has no native NULL. By default csvdb uses \N (the PostgreSQL convention) to distinguish NULL from empty string. Roundtrips are lossless.- Format-independent checksums: csvdb checksum produces the same SHA-256 hash whether the input is SQLite, DuckDB, or a csvdb directory. Useful for verifying conversions.- Schema preservation: indexes and views survive the roundtrip, not just tables.Written in Rust. Beta quality -- the file format may still change.https:&#x2F;&#x2F;github.com&#x2F;jeff-gorelick&#x2F;csvdb

## Top Comments

**chmaynard:**
I admire what you are doing. It obviously serves you well and you hope it helps others.I'm familiar with how to import CSV data with SQLite and I could probably learn how to do it with DuckDB with ease. Your tool introduces a new and rather shallow abstraction layer with commands that work for both databases.The world needs tools that provide a great deal of utility, are trustworthy, and keep getting more reliable and capable. I'm not sure that yours will qualify.
