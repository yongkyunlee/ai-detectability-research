# Show HN: Go-duckfs – making DuckDB quack like a Gopher

**HN** | Points: 4 | Comments: 2 | Date: 2026-03-04
**Author:** achille-roussel
**HN URL:** https://news.ycombinator.com/item?id=47251496
**Link:** https://github.com/firetiger-oss/go-duckfs

I made this because I kept running into issues and limitations when trying to embed DuckDB in Go applications: because DuckDB and its extensions do their own I&#x2F;O in C++ land, integrating with the rest of my applications to get authentication or instrumentation working was really challenging. With go-duckfs, all this happens on the Go side, it's like a sandbox for all I&#x2F;O that happen during queries.It's kind of like https:&#x2F;&#x2F;duckdb.org&#x2F;docs&#x2F;stable&#x2F;guides&#x2F;python&#x2F;filesystems but for Go. I think it'll be useful to anyone who is using DuckDB in a Go application, let me know!

## Top Comments

**ncruces:**
Similar in vein with how my SQLite driver fully replaces the filesystem access layer (VFS) with Go code, and makes it available as Go APIs you can implement (including, in read-only mode, with any io.ReaderAt).https:&#x2F;&#x2F;github.com&#x2F;ncruces&#x2F;go-sqlite3&#x2F;blob&#x2F;main&#x2F;vfs&#x2F;readervf...
