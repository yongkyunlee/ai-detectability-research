# Duckdb debug build fails with multiple definitions for filesystem flags

**Issue #21108** | State: open | Created: 2026-02-27 | Updated: 2026-03-10
**Author:** myrrc
**Labels:** under review

### What happens?

A duckdb debug build sometimes triggers a link issue. As a sidenote,
for mold it additionally crashes the linker https://github.com/rui314/mold/issues/1538.

My guess as why it happens:

In `file_open_flags.cpp` there are definitions of constexpr variables

```cpp
class FileFlags {
public:
	//! Open file with read access
	static constexpr FileOpenFlags FILE_FLAGS_READ = FileOpenFlags(FileOpenFlags::FILE_FLAGS_READ);
```

These variables are not `static inline` (weirdly that matters for constexpr) and thus they need to be defined elsewhere, otherwise build fails with "undefined reference".

```
mold: error: undefined symbol: duckdb::FileFlags::FILE_FLAGS_MULTI_CLIENT_ACCESS
>>> referenced by ub_duckdb_storage.cpp
(duckdb::WriteAheadLog::Initialize())
>>> referenced 5 more times
mold: error: undefined symbol: duckdb::FileFlags::FILE_FLAGS_FILE_CREATE_NEW
>>> referenced by extension_install.cpp
>>>               src/libduckdb_static.a(extension_install.cpp.o):(duckdb::WriteExtensionFileToDisk(duckdb::FileSystem&, std::__cxx11::basic_string, std::allocator > const&, void*, unsigned long))

```

So, they are additionally defined in `file_system.cpp` (the error above is result of removing such definitions):

```cpp
namespace duckdb {

constexpr FileOpenFlags FileFlags::FILE_FLAGS_READ;
```

However, duckdb and extensions using duckdb utilise a unity build, which produces the following error:

```
mold: error: duplicate symbol: extension/vortex/libvortex_duckdb.a(5811b530fb0dbdaf-file_system.o): src/libduckdb_static.a(ub_duckdb_common.cpp.o): duckdb::FileFlags::FILE_FLAGS_READ
mold: error: duplicate symbol: extension/vortex/libvortex_duckdb.a(5811b530fb0dbdaf-file_system.o): src/libduckdb_static.a(ub_duckdb_common.cpp.o): duckdb::FileFlags::FILE_FLAGS_PARALLEL_ACCESS

/usr/bin/ld: extension/vortex/libvortex_duckdb.a(5811b530fb0dbdaf-file_system.o):(.rodata._ZN6duckdb9FileFlags15FILE_FLAGS_READE[_ZN6duckdb9FileFlags15FILE_FLAGS_READE]+0x0): multiple definition of `duckdb::FileFlags::FILE_FLAGS_READ'; src/libduckdb_static.a(ub_duckdb_common.cpp.o):(.rodata+0x2db40): first defined here
/usr/bin/ld: extension/vortex/libvortex_duckdb.a(5811b530fb0dbdaf-file_system.o):(.rodata._ZN6duckdb9FileFlags26FILE_FLAGS_PARALLEL_ACCESSE[_ZN6duckdb9FileFlags26FILE_FLAGS_PARALLEL_ACCESSE]+0x0): multiple definition of `duckdb::FileFlags::FILE_FLAGS_PARALLEL_ACCESS'; src/libduckdb_static.a(ub_duckdb_common.cpp.o):(.rodata+0x2dd40): first defined here
```

Above is an example of building our extension with duckdb, but this reproduces with official extensions as well.

Setting variables to `static constexpr inline` solves this issue if you remove definitions from `file_system.cpp`. Otherwise there is a following (rightful) error:

```
In file included from /home/myrrc/duckdb-vortex/build/debug/src/common/ub_duckdb_common.cpp:19:
/home/myrrc/duckdb-vortex/duckdb/src/common/file_system.cpp:53:25: error: redefinition of ‘constexpr const duckdb::FileOpenFlags duckdb::FileFlags::FILE_FLAGS_READ’
   53 | constexpr FileOpenFlags FileFlags::FILE_FLAGS_READ;
      |                         ^~~~~~~~~
/home/myrrc/duckdb-vortex/duckdb/src/include/duckdb/common/file_open_flags.hpp:131:47: note: ‘constexpr const duckdb::FileOpenFlags duckdb::FileFlags::FILE_FLAGS_READ’ previously defined here
  131 |         static constexpr inline FileOpenFlags FILE_FLAGS_READ = FileOpenFlags(FileOpenFlags::FILE_FLAGS_READ);
```

### To Reproduce

Create a duckdb (extension) debug build `make debug -j`. Tested with duckdb-httpfs, our extension vortex-duckdb, and standalone duckdb at 1.4.3.
The issue does reproduce on debug and reldebug builds, but not in release.

### OS:

Debian 13 Trixie aarch64

### DuckDB Version:

d1dc88f950d456d72493df452dabdcd13aa413dd (1.4.3)

### DuckDB Client:

Not applicable

### Hardware:

_No response_

### Full Name:

Mikhail Kot

### Affiliation:

SpiralDB

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**dentiny:**
> These variables are not static inline (weirdly that matters for constexpr) and thus they need to be defined elsewhere

I guess it's because `constexpr` declaration implies `inline` starts from C++17 (ref: https://en.cppreference.com/w/cpp/language/inline.html) and DuckDB's now on C++11

**dentiny:**
I temporarily worked around by allowing duplicate symbols.
```sh
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_link_libraries(test_distributed_flight -Wl,--allow-multiple-definition)
endif()
```

**Maxxen:**
Hello!

I've haven't really been able to reproduce this but I've pushed a PR here https://github.com/duckdb/duckdb/pull/21286 that changes the file flag constant to no longer use constexpr and instead only be defined once in the `.cpp` file, which should resolve any duplicate symbol issues.
