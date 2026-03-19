# CSVs are not cached in the external file cache

**Issue #21088** | State: closed | Created: 2026-02-26 | Updated: 2026-03-02
**Author:** aschereT
**Labels:** reproduced

### What happens?

I have CSVs stored remotely, in S3. I expected the initial query to cache these CSVs in the external file cache, and for the cache to be used when the ETags are unchanged.

```sh
 ❯ curl -I https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.csv
HTTP/1.1 200 OK
x-amz-id-2: 71ueXiAturcHADhOmKy1An5Q+mikOBreVnebkyKGJrXVHlLIjjZoUd3Tvjkn4Y0yNM6RPp82Ngc=
x-amz-request-id: CZY07YTKVE7AM7T5
Date: Thu, 26 Feb 2026 00:48:07 GMT
Last-Modified: Wed, 15 Dec 2021 03:46:05 GMT
ETag: "5938097a22259524c20eaed5879fab85-11"
x-amz-storage-class: INTELLIGENT_TIERING
x-amz-version-id: ao8yrWV3N9v1vhgrztXlKfoYTJq7Ob9k
Accept-Ranges: bytes
Content-Type: text/csv
Content-Length: 83974211
Server: AmazonS3
```

However, no part of the CSV is ever cached. The external file cache is completely empty, and as such DuckDB will always have to re-download the entire CSV for every query.

Examples in this ticket uses public dataset from https://github.com/awslabs/open-data-registry/blob/main/datasets/cmip6.yaml

### To Reproduce

Queries:
```sql
SET enable_external_file_cache=true;
FROM 'https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.csv';
FROM duckdb_external_file_cache();
EXPLAIN ANALYZE FROM 'https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.csv';
```

Output:
```sql
D FROM duckdb_external_file_cache();
┌─────────┬──────────┬──────────┬─────────┐
│  path   │ nr_bytes │ location │ loaded  │
│ varchar │  int64   │  int64   │ boolean │
├─────────┴──────────┴──────────┴─────────┤
│                 0 rows                  │
└─────────────────────────────────────────┘
Run Time (s): real 0.001 user 0.000718 sys 0.000104
changes:   0   total_changes: 0

D EXPLAIN ANALYZE FROM 'https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.csv';
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
EXPLAIN ANALYZE FROM 'https://cmip6-pds.s3.amazonaws.com/pangeo-cmip6.csv';
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││         HTTPFS HTTP Stats         ││
││                                   ││
││            in: 80.0 MiB           ││
││            out: 0 bytes           ││
││              #HEAD: 1             ││
││              #GET: 3              ││
││              #PUT: 0              ││
││              #POST: 0             ││
││             #DELETE: 0            ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││               Total Time: 2.72s              ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│         Function:         │
│       READ_CSV_AUTO       │
│                           │
│        Projections:       │
│        activity_id        │
│       institution_id      │
│         source_id         │
│       experiment_id       │
│         member_id         │
│          table_id         │
│        variable_id        │
│         grid_label        │
│           zstore          │
│       dcpp_init_year      │
│          version          │
│                           │
│    Total Files Read: 1    │
│                           │
│        522,217 rows       │
│          (8.06s)          │
└───────────────────────────┘
Run Time (s): real 2.719 user 0.604667 sys 0.217242
changes:   0   total_changes: 0
```

### OS:

macOS Tahoe 26.3, aarch64

### DuckDB Version:

1.4.4 6ddac802ff

### DuckDB Client:

CLI

### Hardware:

Apple M3 Pro, 18GB

### Full Name:

Vincent Tan

### Affiliation:

PG Forsta

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**dentiny:**
I think if no surprises, it should as easy as adding a caching option at https://github.com/duckdb/duckdb/blob/0ae55359dd269c354022fb9902be34aa491d797b/src/execution/operator/csv_scanner/buffer_manager/csv_file_handle.cpp#L23 (as what do we for blob reader and json reader)
I'd like to take a look.

**aschereT:**
Ah OK, so something like this? (copying from `extension/json/json_reader.cpp`)
```cpp
unique_ptr CSVFileHandle::OpenFileHandle(FileSystem &fs, Allocator &allocator, const OpenFileInfo &file,
                                                     FileCompressionType compression) {
	FileOpenFlags flags = FileFlags::FILE_FLAGS_READ | options.compression;
	flags.SetCachingMode(CachingMode::CACHE_REMOTE_ONLY);
	auto regular_file_handle = fs.OpenFile(file, flags);
	file_handle = make_uniq(context, std::move(regular_file_handle), BufferAllocator::Get(context));
	if (file_handle->CanSeek()) {
		file_handle->Reset();
	}
	return file_handle;
}
```
