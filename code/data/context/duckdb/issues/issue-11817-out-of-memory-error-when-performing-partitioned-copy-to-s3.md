# Out-of-memory error when performing partitioned copy to S3

**Issue #11817** | State: open | Created: 2024-04-24 | Updated: 2026-03-14
**Author:** jankramer
**Labels:** under review

### What happens?

When performing a `COPY` to S3 using hive partitioning, memory usage is higher than expected. 

For example, copying a table with 2 `int64` columns with 30 partitions of 1k rows to S3 already fails when the memory limit is set to 2GiB, even though the entire table easily fits in memory. Copying to local disk, or copying to a single file in S3 both work fine. The format does not seem to matter, both Parquet and CSV exhibit the same issue.

Platforms tested (all with DuckDB CLI v0.10.2):

- Linux x86-64
- Linux aarch64
- MacOS aarch64



### To Reproduce

```sql
SET memory_limit = '2GiB';

-- Settings below do not seem to make a difference, but trying to maximize reproducibility
SET threads = 1;
SET s3_uploader_thread_limit = 1;
SET preserve_insertion_order = false;

-- Create a table with 30 partitions of 1000 records each
CREATE TABLE test AS SELECT UNNEST(RANGE(30000)) x, x//1000 AS y;

COPY test TO 's3:///path' (FORMAT PARQUET, PARTITION_BY (y));
-- Out of Memory Error: could not allocate block of size 76.5 MiB (1.9 GiB/2.0 GiB used)
```

### OS:

Linux x86-64

### DuckDB Version:

0.10.2

### DuckDB Client:

CLI

### Full Name:

Jan Kramer

### Affiliation:

N/A

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [X] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [X] Yes, I have

## Comments

**jankramer:**
Small update: the issue can be reproduced in the test suite by increasing the number of partitions the following test generates, e.g. by changing `i%2` to `i%10`: https://github.com/duckdb/duckdb/blob/v0.10.2/test/sql/copy/s3/hive_partitioned_write_s3.test_slow#L38.

**github-actions[bot]:**
This issue is stale because it has been open 90 days with no activity. Remove stale label or comment or this will be closed in 30 days.

**elephantmetropolis:**
We are having the exact same problem. Trying to copy with partition on remote S3 always ends up with OOM, no matter the size of the data. Local partitioned copy works fine afaik.
However we end up with `Out of Memory Error: could not allocate block of size 1 KiB (50.0 GiB/50.0 GiB used)`
Is there any workaround ?

Edit: Problem has been solved, it was happening because we tried to push dataset containing multiple millions partitions that was not intended. After moving back to a normal amount of partitions, it worked

**chauthinhhuynh:**
We are having the exact same problem. Trying to copy with partition on remote S3 always ends up with OOM, same issues with copy files to GCS.
Is there any workaround ?

**nabriski:**
same problem here as well on version 1.1.0

**mozarik:**
> We are having the exact same problem. Trying to copy with partition on remote S3 always ends up with OOM, same issues with copy files to GCS. Is there any workaround ?

@chauthinhhuynh currently maybe you can manually set something like this https://github.com/duckdb/duckdb/issues/8981#issue-1900930059

**rahulJuspay:**
same problem here with version 1.1.3, I have a json file which contains data spread across last 20days, I am trying to partition by year, month, day, hour and getting mom. original file is 180MB gzip compressed json file, I tried to run on 2GB, 4GB, 6GB keep getting oom.
I even tried PRAGMA temp_directory='/path/to/tmp.tmp'
but keeps going getting Out of Memory Error: failed to pin block of size 256.0 KiB (1.8 GiB/1.8 GiB used)

**diwu-sf:**
I hit the same problem, and just had to run repeated `COPY ...` commands with subquery filtering the source table down to just a specific partition. I suspect the reason this problem exists is that when exporting thousands of partitions simultaneously, the parquet buffered writers are all just kept in-memory uncompressed and not flushed until the row group size is met.

Iterating over the partitions one by one means there's a single parquet writer buffer at a time, so memory is easy to control.

**olle:**
We're really struggling with something that seems to be this issue. We're running an archiving job and are ending up with lots of partitions on `year/month/date` over about 20-100MB of CSV data. When doing consecutive `COPY...TO` statements, writing to S3 we end up getting `Out of Memory Error: could not allocate block of size 76.5 MiB (3.6 GiB/3.7 GiB used)`. We're rather constrained in the production runtime with only 4GB RAM in total available. We're currently using v1.4.4.0 with JDBC.

I've built a variant, as suggested by @diwu-sf - but where the _composite_ query was O(1) and RAM bound, iterating the partitions seems to take forever in our production env. We're just cramped on CPU/RAM.

I'm wondering if there has been any success in reproducing this problem, and if there are any other news on the progress? Or does anyone have any other great ideas on the subject. I could look into building a setup more like ours to reproduce the problem, if it would help. Cheers.

**olle:**
Hi I've created a small Spring Boot application that can reproduce our scenario, and configure how much data to archive as well as the number of days it's spread over.

https://github.com/olle/apartitions

I guess this isn't technically a bug or exceptional issue, perhaps there's some more or better information to be provided regarding expectations on memory usage when writing hive-partitioned data. There's a simple scenario in my project that shows how ~15MB of data, over 30 days leads to OOM when DuckDB has 1GB `memory_limit`. It's really easy to get started and run.

https://github.com/olle/apartitions?tab=readme-ov-file#example-scenario

Cheers.
