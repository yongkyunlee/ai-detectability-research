# Request to test network stack changes in duckdb-httpfs between v1.4 and v1.5

**Issue #20977** | State: closed | Created: 2026-02-16 | Updated: 2026-03-17
**Author:** guillesd
**Labels:** announcement

We are on the final stretch of duckdb's `v1.5.0` release. It contains various changes and, in particular, many new things landed in the `httpfs` extension. We are eager to share the current state, in the hope that you would like to try it out and report any feedback or bug.

### How to try `v1.5-variegata`

First, note that bug fixes and extension bumps are still landing and that the release has not been packaged yet.

#### CLI

Binaries are available at
- Linux arm64: https://artifacts.duckdb.org/v1.5-variegata/duckdb-binaries-linux-arm64.zip
- Linux amd64: https://artifacts.duckdb.org/v1.5-variegata/duckdb-binaries-linux-amd64.zip
- macOS: https://artifacts.duckdb.org/v1.5-variegata/duckdb-binaries-osx.zip
- Windows: https://artifacts.duckdb.org/v1.5-variegata/duckdb-binaries-windows.zip

```
% ~/Downloads/duckdb-binaries-osx/duckdb
DuckDB v1.5.0-dev7214 (Development Version, dd911088fa)
Enter ".help" for usage hints.
memory D 
```

> [!NOTE]  
> At the moment the last available build is for sha `dd911088fa `.

#### Python

Pre-compiled wheels are installable like so:
```
python3 -m pip install "duckdb>=1.5.0.dev"
```

### How to provide feedback

If you are trying this out, and if you find anything unexpected, in particular connected to the network stack, then early feedback in the form of a bug report would be great to have.

GitHub issue reports are 
- https://github.com/duckdb/duckdb-httpfs/issues for network-related issues
- https://github.com/duckdb/duckdb/issues for core duckdb issues

## Network stack changes overview

> [!IMPORTANT]  
> Here is a list of changes specific to the network stack, with links to relevant PRs:

### CURL library as the default backend

In DuckDB `v1.4+`, `curl` was optional and could been enabled via `SET httpfs_client_implementation = curl;`. Then, it was still experimental, but now it has been bumped to be the default.

PR: https://github.com/duckdb/duckdb-httpfs/pull/96 ... https://github.com/duckdb/duckdb-httpfs/pull/223

DuckDB's `httpfs` extension moved its default backend from `httplib` to `curl`. `openssl` is still the backing SSL library and options such as `http_timeout`, `http_retries`, etc. are still the same, but now there is a different library in the middle.

`httplib` is still the library we use for the initial extension download, and one can opt-in to use the same

CURL project information can be found at https://curl.se/, GitHub project at https://github.com/curl/curl.
`SET httpfs_client_implementation = httplib;` allows to move to `httplib`-implementation.

### Bumping dependencies versions

`httplib` has been moved (in duckdb/duckdb) to 0.27.0, see PR at https://github.com/duckdb/duckdb/pull/20299.
`vcpkg` dependency manager it's now at version 2025.12.12, and consequently this implies using openssl 3.6.0 and curl 8.17.0.

### Glob rework, now lazily expanded

PR: https://github.com/duckdb/duckdb/pull/20619 and https://github.com/duckdb/duckdb-httpfs/pull/216

Some changes landed in duckdb core and then enabled in duckdb-httpfs. Concretely, a new API that allows for lazy glob expansion, so that `FROM 's3:///**; LIMIT 10;` will not require anymore listing all files.

### Hierarchical S3 globs

PR: https://github.com/duckdb/duckdb-httpfs/pull/218

Faster globbing on patterns like `s3:///folder/*/some-specific-subfolder/` thanks to expanding directories hierarchically (`delimiter` S3 modifier) instead of using flat listings.

On the user side this should end up in less roundtrips for most case scenarios, and consequently faster query execution on most queries.
This is enabled by default, since this is significantly better when there are many files per given folder, but might have a constant overhead on smaller example buckets.

`SET s3_allow_recursive_globbing = false` will disable this behavior, using always flat listing.

### Once httpfs is loaded, extensions are bumped to https

PR: https://github.com/duckdb/duckdb/pull/20877

Currently extensions that download from default endpoint always go through HTTP. With this change, when `httpfs` is loaded, subsequent extension installation traffic will go through `https://`, with default endpoint at `https://extensions.duckdb.org`.
This means that if one where to have `httpfs` extension installed out-of-band, say via a local repository, then all subsequent traffic would go via https, that should help in some firewall situations where this has been reported as suspicious.

> Note that extensions signature checks are now performed both on installation AND on load, this do not changes security pose, but should mean easier adoptions in corporare setups.

### Bulk deletes of files from the same bucket

External contributor PRs: https://github.com/duckdb/duckdb/pull/20333 .. https://github.com/duckdb/duckdb-httpfs/pull/181

This adds an API to duckdb and then implements in duckdb-httpfs to perform bulk deletes, that is 1000 files in a single network call.

### Handling for S3 version_id

External contributor PR: https://github.com/duckdb/duckdb-httpfs/pull/243 (commits merged in a different form).

Adds support for querying versioned buckets, via storing `x-amz-version-id` when returned from an S3-like endpoint.

`SET s3_version_id_pinning = false;` will disable this feature.

### Improved S3 region auto-detection

PR: https://github.com/duckdb/duckdb-httpfs/pull/220

In v1.4 DuckDB would fail various queries even HTTP responses would include information about region mismatch. After this change, those are automatically retried. This should improve user experience and allow conflicting credentials to work out of the box.
In particular the problematic case was a default S3 credential combined with reading a public bucket in a region different than the default one. In this case, adding a credential meant the public bucket would not be accessible anymore.
Since this PR, this works automatically.

> [!IMPORTANT]
> In the CLI, a Warning will be shown when such automatic retries are happening, allowing feedback on misconfigured secrets. In non-CLI setup, one must first enable WARN level logging for the warning to show.

## Bugs reports are welcome!

Feel free to report any hiccup you might be facing via the GitHub issue reports (https://github.com/duckdb/duckdb-httpfs/issues for network related issue, https://github.com/duckdb/duckdb/issues for core duckdb issues).

Thanks a lot for helping us make DuckDB v1.5.0 Variegata better!

## Comments

**carlopi:**
Thank you all!

v1.5.0 it's out, I think this can be closed.
