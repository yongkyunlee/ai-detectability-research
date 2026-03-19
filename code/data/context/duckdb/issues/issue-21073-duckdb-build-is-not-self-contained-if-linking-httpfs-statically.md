# Duckdb build is not self-contained if linking httpfs statically

**Issue #21073** | State: closed | Created: 2026-02-25 | Updated: 2026-03-03
**Author:** myrrc
**Labels:** under review

### What happens?

I'm opening this as an issue and not as a PR as I don't have a good solution myself.
DuckDB's httpfs, if built from duckdb-httpfs, uses vcpkg to bootstrap curl dependency. However, if we build duckdb from duckdb repo with `BUILD_EXTENSIONS=httpfs`, the build fails unless you have `libcurl-openssl-dev` installed.

In duckdb's CI it's installed along with cmake and ninja-build. My main argument is that curl is not a build system like cmake or ninja and therefore can be bootstrapped in duckdb's cmake files directly. 

However, duckdb doesn't use vcpkg to manage its own dependencies, so I can't think of a good way of installing it as part of build. You can work around with `EXTENSION_CONFIG_BUILD` but then you need to use vcpkg.

### To Reproduce

Try to build duckdb with `BUILD_EXTENSIONS=httpfs` on a machine without curl dev headers installed

### OS:

Debian trixie 13 aarch64

### DuckDB Version:

stable

### DuckDB Client:

None

### Hardware:

_No response_

### Full Name:

Mikhail Kot

### Affiliation:

Vortex

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**carlopi:**
Thanks for raising, there are extensions (`httpfs` included) that have a build time dependency on `vcpkg`.

My proposed solution would be adding to duckdb own Makefile a way to setup vcpkg (see https://github.com/duckdb/duckdb/pull/21123), so that the path will become:
1. make setup-vcpkg
2. pass correct env variable, and build extensions

You could for now consider manually (or anyhow, outside of duckdb) performing the steps outlined in the PR, that are at https://github.com/duckdb/duckdb/pull/21123/changes#diff-76ed074a9305c04054cdebb9e9aad2d818052b07091de1f20cad0bbac34ffb52R567-R568

**carlopi:**
Linked PR it's merged, this is solved I believe (for v1.5-variegata onward, otherwise via manual steps)
