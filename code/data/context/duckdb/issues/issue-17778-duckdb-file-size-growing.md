# .duckdb file size growing

**Issue #17778** | State: open | Created: 2025-06-03 | Updated: 2026-03-03
**Author:** brianlagunas
**Labels:** reproduced

### What happens?

I am new to DuckDB, so excuse me if I am missing something. I am using DuckDB.NET as a cache database that stores a large amount of json data in a single field associated with a cache key.

```
CREATE TABLE IF NOT EXISTS query_cache (
    cache_key VARCHAR PRIMARY KEY,
    result_data JSON NOT NULL,
    user_id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    cached_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    metadata JSON,
    row_count BIGINT,
    column_count INTEGER
);
```

As my application runs, it adds new cache entries, and then as the cache entries expire, they are removed from the table.

The problem is that the file size will continue to grow and never shrink even as large cache items are being removed from the table.

Even if I delete everything in the table:
```
const string sql = "DELETE FROM query_cache";
using var command = connection.CreateCommand();
command.CommandText = sql;
var rowsDeleted = await command.ExecuteNonQueryAsync();
```

The file size does not get reclaimed. I have tried calling the CHECKPOINT command, but that doesn't have any impact on the file size. It just continues to grow and grow. My file grows by the GB in just a few minutes. I can have a completely empty table yet the files size is 2GB.

I've read the [Reclaiming Space](https://duckdb.org/docs/stable/operations_manual/footprint_of_duckdb/reclaiming_space.html) topic, but the `CHECKPOINT` call does not reclaim any space, and I would rather not create a new database and copy the existing cache into it for a number of reasons. Mainly because of the potential issue of poor end-user experience do to the copying process which could take a long time and result in data loss.

Also, I read the file size may grow in size, but if there is free space available (data was removed), the file will not grow until the free space is taken back up. However, that is not the case. Even with all rows deleted, the size will continue to grow when new cache entries are added.

Is there a way to keep the files size in proportion to the data within the .duckdb file?

### To Reproduce

I use DuckDb.NET to execute queries but it's pretty straight forward.

create the DB
```
using var connection = new DuckDBConnection(ConnectionString);
connection.Open();

// Configure DuckDB for optimal caching performance
ExecuteNonQuery(connection, $"SET memory_limit='{_config.MemoryLimit}';");
ExecuteNonQuery(connection, $"SET threads={_config.ThreadCount};");

// Create schema
ExecuteNonQuery(connection, CacheTableSchema);
```

Add rows to the table:
```
var now = DateTime.UtcNow;
var expiresAt = now.Add(_config.DefaultTtl);
var userId = userContext.UserId ?? "anonymous";
var tenantId = ExtractTenantId(userContext);
var datasetId = ExtractDatasetId(cacheKey);

var metadata = new Dictionary
{
    ["UserRoles"] = userContext.Roles ?? new List(),
    ["SetAt"] = now,
    ["TTL"] = _config.DefaultTtl.TotalSeconds,
};

using var connection = new DuckDBConnection(ConnectionString);
await connection.OpenAsync();

const string sql = @"
    INSERT OR REPLACE INTO query_cache 
    (cache_key, result_data, user_id, tenant_id, dataset_id, cached_at, expires_at, metadata, row_count, column_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

using var command = connection.CreateCommand();
command.CommandText = sql;
// Use positional parameters (no names), in the same order as the VALUES (?, ?, ..., ?)
command.Parameters.Add(new DuckDBParameter { Value = cacheKey });
command.Parameters.Add(new DuckDBParameter { Value = JsonSerializer.Serialize(result, _jsonOptions) });
command.Parameters.Add(new DuckDBParameter { Value = userId });
command.Parameters.Add(new DuckDBParameter { Value = tenantId });
command.Parameters.Add(new DuckDBParameter { Value = datasetId ?? "" });
command.Parameters.Add(new DuckDBParameter { Value = now });
command.Parameters.Add(new DuckDBParameter { Value = expiresAt });
command.Parameters.Add(new DuckDBParameter { Value = JsonSerializer.Serialize(metadata, _jsonOptions) });
command.Parameters.Add(new DuckDBParameter { Value = result.Rows.Count });
command.Parameters.Add(new DuckDBParameter { Value = result.Columns.Count });

await command.ExecuteNonQueryAsync();
```

When cache expires remove items:
```
using var connection = new DuckDBConnection(ConnectionString);
await connection.OpenAsync(cancellationToken);
const string expiredSql = "DELETE FROM query_cache WHERE expires_at <= (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')";
int expiredRows = 0;
using (var expiredCmd = connection.CreateCommand())
{
    expiredCmd.CommandText = expiredSql;
    expiredRows = await expiredCmd.ExecuteNonQueryAsync(cancellationToken);
}
```

### OS:

Windows x64

### DuckDB Version:

v1.3.0

### DuckDB Client:

.NET

### Hardware:

_No response_

### Full Name:

Brian Lagunas

### Affiliation:

Infragistics

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**brianlagunas:**
I have uploaded an [empty database file](https://infragisticsinc297-my.sharepoint.com/:u:/g/personal/blagunas_infragistics_com/EZEpE535b-JHvPVh27-Wzd4B3yBIs8f7yI3MMlGU9w4Ydg?e=aeaiud) that is roughly 150MB.

As you can see, calling `CHECKPOINT` does nothing for file size.

**mcphatty:**
This is a huge problem for us and is already documented in [14124](https://github.com/duckdb/duckdb/issues/14124). Unfortunately this ticket is 'under review' for quite a while now. Is there any chance this will be fixed in the nearer future? As a file format the duckdb database is nearly unusable when applying changes to it on a regular basis.

Thanks

**mcphatty:**
Just to add our workaround: We export the database to a new file, which seems to drop all unneeded space, and then replace the original file with this export. Which is a lot of overhead.

**Giorgi:**
@brianlagunas Not related to this issue but you can set db parameters in the connection string itself: [Connection String Parameters](https://duckdb.net/docs/connection-string.html#example-connections-strings)

**brianlagunas:**
> Just to add our workaround: We export the database to a new file, which seems to drop all unneeded space, and then replace the original file with this export. Which is a lot of overhead.

This is exactly what we don't want to do. This introduces a large overhead especially on a DB file that could be 20GB in size.

My work around was to only store the metadata about the cached data in the DB file, and then actually store the data results as json in a compressed zip file on disk. I store the path to the file in the DB file which keeps it very small. Clean-up is easy, as I remove the cache entry from the DB, I remove the compressed file on disk at the same time which will reclaim space. 

This did add a slight perf hit of about 20ms, but the ability to reclaim the disk space is worth it.

Now, this is only a temporary fix, because the next part of my cache strategy is actually syncing data form the source into DuckDB for actual analytics. I will create tables dynamically and then drop the tables after the cache expires. Then I will be right back in the same situation except I won't be able to use the same work-around I did for the key -> value based cache.

I'm honestly not sure how DuckDB is becoming so popular with such an important outstanding issue. I mean this is basically a show-stopper. I can try to run a background service late at night to rebuild the database when it reaches a certain size, but my problem is I need the database name to be the same. Which introduces some other challenges when trying to rebuild it.

@Giorgi thanks for the tip.

**Mytherin:**
Thanks for the report!

This is a separate issue from https://github.com/duckdb/duckdb/issues/14124. While it's an expected restriction that the size of the database file does not always shrink when performing mixed update/delete workloads - blocks should be added to the free list and re-used. The fact that that is not happening here is a bug. I've managed to reproduce an issue related to indexes and upserts - and there might be another issue related to handling of very large strings. We will investigate further.

**p1p1bear:**
I've also observed this issue, and I'm sure it's related to the ART index...
It seems that when ART exists, even if we delete the table, only the block corresponding to ART is reset to free list.

without ART, all good here.

**p1p1bear:**
I looked through the code and commit logs and this seems to be an expected behavior.

commit#8ce6cc7992486ac957faf3bd7c56aafa79d220eb 

PR: https://github.com/duckdb/duckdb/pull/7794

**fanvanzh:**
vacuum does not works with indexes.
This is because row_id and row_group are correlated. If row_groups are vacuumed, row_id will be an error id.
However, correcting row_id from the index is a huge overhead and is not worth doing.

**rayGoMoon:**
Thank you,  @p1p1bear. 

Thank you very much for the crucial information you provided.

I can confirm that the issue of the **duckdb database file growing unbounded is indeed caused by the ART index.**

I'm currently using a small, but frequently updated and deleted duckdb database. It contains only one table with approximately 1,500 rows.

After running the duckdb database for 24 hours, the duckdb database file grew wildly to **1.2GB**, with the total number of rows remaining virtually unchanged.

Running VACUUM or CHECKPOINT operations did nothing to reduce the database file size.

However, when I exported the database as a Parquet file, the Parquet file size was only **400kb**.

After seeing @p1p1bear mention that this issue was related to ART indexes, I consulted the official DuckDB documentation:

[https://duckdb.org/docs/stable/sql/indexes#adaptive-radix-tree-art](https://duckdb.org/docs/stable/sql/indexes#adaptive-radix-tree-art)

This section states:

> ART indexes ... are automatically created for columns with a UNIQUE or PRIMARY KEY constraint.

So I tried removing the only UNIQUE constraint in the original table.

And just like that, a miracle happened!

After 24 hours of operation, the DuckDB database file size remained at **2.3 MB**.

DuckDB is an excellent project. I am deeply grateful to all its developers and contributors.

Hopefully, DuckDB will resolve this issue in the near future.

I'm sharing my personal experience here in the hope that it will help any developer facing this headache.
