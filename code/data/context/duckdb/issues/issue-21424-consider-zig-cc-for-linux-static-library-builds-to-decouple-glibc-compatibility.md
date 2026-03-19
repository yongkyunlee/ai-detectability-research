# Consider zig cc for Linux static library builds to decouple glibc compatibility from compiler version

**Issue #21424** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** samjewell
**Labels:** under review

## Context

The tension between compiler toolchain version and glibc compatibility for prebuilt Linux static libraries has come up multiple times:

- #17632 — GCC 14 in `manylinux_2_28` produced binaries requiring glibc 2.38, breaking Debian 12 and the official Go Docker images
- #17776 — Fixed by downgrading to GCC 12
- #17963 — Proposed reverting the downgrade, noting it diverges from the standardised manylinux toolchain and creates inconsistency with extension builds

The core problem is that **GCC's libstdc++ version and the target glibc version are coupled** — using a newer GCC can silently pull in newer glibc/libstdc++ symbols, even when building on a `manylinux_2_28` image designed to target glibc 2.28. This creates a recurring dilemma: use a modern compiler and risk breaking downstream consumers, or downgrade the compiler and diverge from the standardised toolchain.

## Proposal

[`zig cc`](https://andrewkelley.me/post/zig-cc-powerful-drop-in-replacement-gcc-clang.html) is a drop-in C/C++ compiler (backed by Clang/LLVM) that **explicitly decouples the compiler version from the target glibc version**:

```bash
zig cc -target x86_64-linux-gnu.2.28 -o libduckdb.a ...
```

This would address the recurring tension by:

1. **Decoupling compiler version from glibc floor.** Use the latest Clang/LLVM optimisations while guaranteeing only glibc 2.28 (or lower) symbols are referenced. No more "which GCC version do we use" debate.
2. **Making the glibc target explicit and auditable.** The version is a build flag, not an implicit consequence of which distro image or compiler you build with.
3. **Maintaining a single consistent toolchain.** The same zig version can build both the core libraries and extensions, avoiding the toolchain inconsistency concern raised in #17963.
4. **Potentially enabling musl targets.** `zig cc -target x86_64-linux-musl` would produce fully statically-linked libraries with zero glibc runtime dependency, which could unblock Alpine/musl environments for downstream consumers (see companion issue: [duckdb/duckdb-go-bindings#72](https://github.com/duckdb/duckdb-go-bindings/issues/72)).
5. **Simplifying cross-compilation.** A single zig installation can target linux-amd64, linux-arm64, etc. without separate toolchains or emulation.

## Scope

This would be a change to the Linux build workflows (e.g., `LinuxRelease.yml`, `BuildStaticBundle.yml`) — replacing or supplementing `gcc`/`g++` with `zig cc`/`zig c++`. Zig is distributed as a single ~45 MB tarball with no system dependencies, so CI integration is straightforward.

I'm not suggesting this needs to happen immediately — just raising it as a potentially cleaner long-term solution to the glibc compatibility problem that keeps resurfacing. Happy to help test if there's interest.

## Related

- #17632 — Prebuilt static libs incompatible with Debian 12
- #17776 — GCC downgrade fix
- #17963 — Discussion about reverting the downgrade
- [zig cc blog post](https://andrewkelley.me/post/zig-cc-powerful-drop-in-replacement-gcc-clang.html)
- Companion issue for Go consumer impact: [duckdb/duckdb-go-bindings#72](https://github.com/duckdb/duckdb-go-bindings/issues/72)
