# `QUALIFY ROW_NUMBER() OVER (...) = 1` causes ~50x more S3 requests in 1.5.0

**Issue #21348** | State: open | Created: 2026-03-12 | Updated: 2026-03-16
**Author:** tlinhart
**Labels:** reproduced

### What happens?

A query using `QUALIFY ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) = 1` on hive-partitioned Parquet files in S3 went from ~80 HTTP GET requests in v1.4.4 to over 4,200 in v1.5.0 with wall clock time nearly tripling.

Looking at the `EXPLAIN ANALYZE` output, it seems like v1.5.0 rewrites the `ROW_NUMBER() ... = 1` pattern into some kind of `arg_max` + `HASH_GROUP_BY` -> `SEMI JOIN` plan that scans the Parquet files twice – once to find the "winning" rows (lightweight, few columns), and again to fetch all columns for those rows. In v1.4.4, the plan used a single `TABLE_SCAN` followed by a `WINDOW` function. For S3-hosted Parquet files with many columns (~90 in my case), the second full-column scan seems to generate a separate HTTP range request per column chunk per file, which is where the ~4200 GET requests come from (roughly 39 files x ~90 columns x
~1-2 row groups). This issue is compounded by https://github.com/duckdb/duckdb/issues/21347 (hive partition pruning regression), which causes extra files to be discovered and probed during the scan.

Here's a basic performance comparison:
| Configuration                         | GET count   | Data      | Wall clock |
|---------------------------------------|--------|-----------|------------|
| v1.4.4 (original query)              | 81     | 87.5 MB  | 11.6s      |
| v1.5.0 (original query)              | 4214  | 91.7 MB  | 31.5s      |
| v1.5.0 + `MATERIALIZED` CTE            | 214    | 91.9 MB  | 41.4s      |
| v1.5.0 + `MATERIALIZED` + `s3_allow_recursive_globbing=false` | 82 | 91.9 MB | 11.5s |

The `MATERIALIZED` CTE forces a single scan (preventing the double-scan rewrite), and combined with disabling the hierarchical globbing, performance matches that of v1.4.4.

What I think is happening
1. The optimizer rewrites `ROW_NUMBER() ... = 1` into an `arg_max` + `SEMI JOIN` strategy that requires scanning the remote files twice.
2. The second scan (all ~90 columns) doesn't seem to benefit from the same request coalescing/prefetching as a normal scan – instead of fetching entire row groups in a few large range requests, it appears to issue individual HTTP requests per column chunk.
3. For local files this is probably fine (disk seeks are cheap), but for S3 where each HTTP request has significant latency overhead (TLS, auth signing, round-trip), the thousands of small requests dominate.

### To Reproduce

You need hive-partitioned Parquet files on S3 with a wide schema (many columns). The more columns, the more pronounced the effect.

```sql
-- ~40 Parquet files on S3, ~90 columns each, hive-partitioned by year/month
-- ~3M total rows across all files

SELECT
    * EXCLUDE (min_date, max_date, month, year),
    least(max_date, DATE '2026-12-31')::DATE AS date
FROM (
    SELECT *
    FROM read_parquet('s3://my-bucket/data/*/*/data.parquet')
    WHERE
        last_day(make_date(year, month, 1)) >= DATE '2023-01-01' AND
        make_date(year, month, 1) = DATE '2023-01-01' AND
        min_date::DATE  `WINDOW` -> `FILTER`. In v1.5.0 it shows two `TABLE_SCAN`s joined by a `HASH_JOIN` (`SEMI`), with a `HASH_GROUP_BY` using `arg_max_nulls_last` on the right side.

As a workaround, wrap the scan in a `MATERIALIZED` CTE to force a single scan, and optionally disable recursive globbing:

```sql
SET s3_allow_recursive_globbing = false;
WITH scanned AS MATERIALIZED (
    SELECT *
    FROM read_parquet('s3://my-bucket/data/*/*/data.parquet')
    WHERE
        last_day(make_date(year, month, 1)) >= DATE '2023-01-01' AND
        make_date(year, month, 1) = DATE '2023-01-01' AND
        min_date::DATE <= DATE '2026-12-31'
)
SELECT
    * EXCLUDE (min_date, max_date, month, year),
    least(max_date, DATE '2026-12-31')::DATE AS date
FROM scanned
QUALIFY row_number() OVER (PARTITION BY id ORDER BY max_date DESC) = 1;
```

### OS:

Linux (Ubuntu 24.04.4 LTS), x86_64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967a

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Tomáš Linhart

### Affiliation:

–

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**hawkfish:**
Hi @tlinhart  - Thanks for the report. This is caused by a new optimiser rule `top_n_window_elimination`. If you disable that rule by:

```sql
SET disabled_optimizers='top_n_window_elimination';
```

you should get the old plan.

We have two new window elimination rules, and the other one is careful about the inputs. I'm less familiar with this one, but I'll have a look to see if it is being less careful.

**tlinhart:**
Hi @hawkfish, I've just tried disabling the optimizer as you suggested. You are right that I got the old plan, however there are still some issues:

- The number of GET requests is still high (214 in v1.5.0 vs. 81 in v1.4.4).
- The total time is high (~20 seconds in v1.5.0 vs. ~10 seconds in v1.4.4). Using `EXPLAIN ANALYZE` shows the timing difference in the `WINDOW` function (~24 seconds in v1.5.0 vs. ~14 seconds in v1.4.4).

Interestingly, if a also disable recursive globbing via

```sql
SET s3_allow_recursive_globbing = false;
```

I get the results on par with v1.4.4 – total run time ~10 seconds and GET request count 82.

I'm not sure how to proceed now:

- I still find this issue as a regression but I might be wrong and it's supposed to work like this in v1.5.0 and we just need to pay more attention to how we prepare queries so they are still performant in v1.5.0.
- I'm not sure how could the recursive globbing affect this issue and if it's somehow related to the other issue I opened (https://github.com/duckdb/duckdb/issues/21347). I'm a bit hesitant because in this case, the `TABLE_SCAN` showed `Scanning Files: 39/39` even before disabling recursive globbing. However, disabling it later clearly made a difference in GET request count and the total run time. So there might be a different issue.

**hawkfish:**
Hi @tlinhart - Yes we are looking into it, but I'm glad you now have some workarounds!

**Mytherin:**
Thanks for reporting - I've made some generic improvements to the Parquet reader in the presence of filters that should help reduce the number of requests - see https://github.com/duckdb/duckdb/pull/21373

For the Top-N optimizer rewrite it would help us if you could provide a representative dataset (perhaps generated to look similar to yours) so that we could run and profile this ourselves.

**tlinhart:**
Hi @Mytherin, here's a script that can be used to create a dataset similar to my real one (in terms of key parameters like total row count, column types, distinct `id` values per Parquet file etc.):

```sql
INSTALL httpfs;
LOAD httpfs;

INSTALL fakeit FROM community;
LOAD fakeit;

SET timezone = 'UTC';

CREATE TEMP TABLE offers AS
SELECT
    uuid()::VARCHAR AS id,
    start_date,
    least(
        start_date + INTERVAL (least(1 + (-ln(1.0 - random()) * 500.0)::INTEGER, 2282)) DAY,
        DATE '2026-03-31'
    )::DATE AS end_date,
    least(
        CASE WHEN random()  o.start_date AND o.num_price_changes > 0
),
deduped_changes AS (
    SELECT DISTINCT ON (id, change_date) id, start_date, end_date, change_date
    FROM change_points ORDER BY id, change_date
),
all_starts AS (
    SELECT id, start_date AS seg_start, end_date AS offer_end, 0 AS sort_key
    FROM offers
    UNION ALL
    SELECT id, change_date AS seg_start, end_date AS offer_end, 1 AS sort_key
    FROM deduped_changes
),
numbered AS (
    SELECT
        id,
        seg_start,
        coalesce(
            (lead(seg_start) OVER w - INTERVAL '1 day')::DATE,
            offer_end
        ) AS seg_end,
        row_number() OVER w AS seg_num
    FROM all_starts
    WINDOW w AS (PARTITION BY id ORDER BY seg_start, sort_key)
)
SELECT
    id,
    seg_num,
    seg_start,
    seg_end,
    10 + (random() * 9990)::INTEGER AS price
FROM numbered
WHERE seg_start = m.month_start
    ),
    with_times AS (
        SELECT
            *,
            make_timestamptz(year(clipped_start), month(clipped_start),
                day(clipped_start), 0, 0, 0, 'UTC') AS start_day_ts,
            make_timestamptz(year(clipped_end), month(clipped_end),
                day(clipped_end), 0, 0, 0, 'UTC') AS end_day_ts,
            (random() * 86399)::INTEGER AS time_offset_a,
            (random() * 86399)::INTEGER AS time_offset_b
        FROM expanded
    )
    SELECT
        id,
        price,
        CASE WHEN clipped_start = clipped_end
            THEN start_day_ts + to_seconds(least(time_offset_a, time_offset_b))
            ELSE start_day_ts + to_seconds(time_offset_a)
        END::TIMESTAMPTZ AS min_date,
        CASE WHEN clipped_start = clipped_end
            THEN start_day_ts + to_seconds(greatest(time_offset_a, time_offset_b))
            ELSE end_day_ts + to_seconds(time_offset_b)
        END::TIMESTAMPTZ AS max_date,
        fakeit_words_sentence() AS title,
        fakeit_hipster_paragraph() AS description,
        fakeit_image_url() AS url,
        fakeit_image_url() AS image_url,
        fakeit_hacker_noun() AS category,
        fakeit_company_company() AS brand,
        fakeit_name_full() AS seller_name,
        round(1.0 + random() * 4.0, 1) AS seller_rating,
        fakeit_currency_short() AS currency,
        price + (random() * price * 0.5)::INTEGER AS original_price,
        (random() * 5000)::INTEGER AS review_count,
        round(1.0 + random() * 4.0, 1) AS rating,
        fakeit_bool() AS is_marketplace,
        fakeit_bool() AS is_available,
        fakeit_internet_domain_name() AS source_site,
        CASE WHEN clipped_start = clipped_end
            THEN start_day_ts + to_seconds(greatest(time_offset_a, time_offset_b))
            ELSE end_day_ts + to_seconds(time_offset_b)
        END::TIMESTAMPTZ AS last_updated,
        year,
        month
    FROM with_times
) TO 'my-bucket/data/' (FORMAT parquet, COMPRESSION zstd, PARTITION_BY (year, month));
```

There are two subtle differences compared to the one I'm actually using:
- The generated one contains only ~20 columns where the real one has ~90 columns. This might make a difference in the timing I guess.
- The generated dataset uses `COPY ... TO` with `PARTITION_BY (year, month)` to create the hive-partitioned structure while the real one is constructed one Parquet file per partition at a time during the ETL. This should not however make any difference since `year` and `month` columns are not present in the final Parquet files in neither case.

When testing this databaset in v1.4.4 vs. v1.5.0 myself, v1.5.0 is slower but the timing difference was not that substantial compared to the original dataset, presumably due to the difference in the column count. However, it reproduces well the big difference in GET request count.

If this dataset is not enough, I could theoretically let you access the original dataset somehow.

**rohitmannur007:**
Hi @tlinhart , @hawkfish  @Mytherin ,

I was able to reproduce the optimizer behavior locally while investigating this issue.

Using a simplified example:

```sql
EXPLAIN
SELECT *
FROM (
    SELECT *, row_number() OVER (PARTITION BY id ORDER BY ts DESC) rn
    FROM (SELECT i % 10 AS id, i AS ts FROM range(1000) tbl(i))
) t
WHERE rn = 1;
```

With the default optimizer enabled, DuckDB rewrites the query into a plan using:

* `HASH_GROUP_BY`
* `max()` aggregation
* elimination of the `WINDOW` operator

When disabling the rule:

```
SET disabled_optimizers='top_n_window_elimination';
```

the plan changes back to the expected:

```
RANGE → WINDOW → FILTER
```

which confirms that `top_n_window_elimination` is responsible for replacing the `ROW_NUMBER() = 1` pattern with the aggregate-based plan.

From inspecting the implementation in `src/optimizer/topn_window_elimination.cpp`, it appears the rewrite is triggered purely based on the logical pattern (ROW_NUMBER with a filter) without considering storage characteristics.

In the S3 / Parquet case described in this issue, the resulting plan seems to require a second scan to fetch the full rows, which likely explains the explosion in HTTP range requests for wide schemas.

I'm currently experimenting with reproducing the issue using the synthetic dataset shared above and comparing the two execution strategies (`WINDOW` vs rewritten aggregate plan). If it helps, I can also explore whether adding heuristics (e.g., avoiding the rewrite for wide projections or remote scans) could mitigate the regression.

If there are specific areas of the optimizer or Parquet reader that would be useful to inspect further, I'd be happy to dig into those as well.

**hawkfish:**
> I was able to reproduce the optimizer behavior locally while investigating this issue.

Hi @rohitmannur007 - Yes this is what we have been discussing for several days now, including all the suggestions from your bot.  While we appreciate your interest and engagement, could you refrain from posting wordy, vague LLM generated output that ignores the rest of the conversation? Thx.

**rohitmannur007:**
Hi @hawkfish 
Thanks for the clarification and sorry for the noise earlier I’ll run some targeted profiling comparing the WINDOW plan vs the rewritten plan on the synthetic dataset to better understand where the extra requests are coming from. If I find anything useful I’ll share the results
