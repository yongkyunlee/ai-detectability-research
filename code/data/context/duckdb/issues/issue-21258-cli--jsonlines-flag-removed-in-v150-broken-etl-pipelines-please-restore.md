# CLI: -jsonlines flag removed in v1.5.0 — broken ETL pipelines, please restore

**Issue #21258** | State: closed | Created: 2026-03-10 | Updated: 2026-03-10
**Author:** aborruso
**Labels:** reproduced

I may be wrong, but it looks like the `-jsonlines` CLI flag was silently removed in v1.5.0.

Testing confirms it:

```
$ duckdb -jsonlines -c "SELECT 1 AS x"
Unknown Option Error: Unrecognized option '-jsonlines'
Did you mean: "-json", "-line"
```

This worked fine up to v1.4.x.

---

### What I think happened

My best guess is that the removal happened as a side effect of the CLI refactoring in [#19544](https://github.com/duckdb/duckdb/pull/19544) ("Refactor command-line parameters into a struct"), which was merged before v1.5.0. The current `shell_command_line_option.cpp` only registers `-json` and `-line` — no `-jsonlines`:

```cpp
{"json", 0, "", nullptr, ToggleOutputMode, "set output mode to 'json'"},
{"line", 0, "", nullptr, ToggleOutputMode, "set output mode to 'line'"},
```

The `ModeJsonRenderer` in `shell_renderer.cpp` still has a `json_array` parameter (suggesting JSONL rendering is still there internally), but it's no longer exposed as a CLI flag.

I could be misreading the code — if there's another way to get JSONL output from the CLI in v1.5.0, I'd love to know.

---

### Why this matters

`-jsonlines` was extremely useful for scripting and ETL pipelines. A typical pattern:

```bash
duckdb -jsonlines -c "SELECT ... FROM read_csv('file.csv')" > output.jsonl
```

The `-json` flag now outputs a JSON **array** — not JSONL — which breaks tools and pipelines that expect newline-delimited JSON. `-line` outputs key=value pairs, which is not JSON at all.

---

### Request

Please restore `-jsonlines` as a first-class CLI flag, or at minimum document the intended replacement in the migration notes. JSONL is a widely used format in data engineering and having it available as a simple flag was one of DuckDB's nicest ergonomic features.

## Comments

**carlopi:**
This looks like a duplicate of https://github.com/duckdb/duckdb/issues/21243, and the same workaround should apply:

```
DUCKDB_NO_HIGHLIGHT=1 ./build/release/duckdb < test.sql
```
or
```
./build/release/duckdb < test.sql | cat
```

First one skip the relevant codepath when ENV variable is present, second skip relevant codepath via a pipe.
I hope either would work for you as a temporary measure.

**aborruso:**
Thanks for the quick reply! Unfortunately neither workaround seems to help with this specific issue.

`DUCKDB_NO_HIGHLIGHT=1` still gives the same error:

```
Unknown Option Error: Unrecognized option '-jsonlines'
```

And piping to `cat` changes nothing about flag parsing — `-jsonlines` is rejected before any output is produced.

I may be misreading things, but looking at the current `tools/shell/shell_command_line_option.cpp`, the registered output modes are:

```cpp
{"json",     0, "", nullptr, ToggleOutputMode, "set output mode to 'json'"},
{"line",     0, "", nullptr, ToggleOutputMode, "set output mode to 'line'"},
```

`-jsonlines` simply isn't in `command_line_options[]` anymore. My guess is it was dropped during the CLI rewrite in #19544, but I couldn't find an explicit removal — am I wrong?

If the flag is intentionally gone, would it be possible to add it back, or at least confirm what the intended replacement is? `-json` now outputs a JSON array, and `-line` outputs key=value pairs — neither is a drop-in replacement for newline-delimited JSON.

**carlopi:**
Oopps, I was a bit too eager, reopened.

I do reproduce, someone will take a look

**aborruso:**
And I think it should be flagged as a bug. 

Thank you

**Mytherin:**
Thanks for reporting - this was removed by accident. As a work-around you can use `duckdb -c ".mode jsonlines"` for now. We'll fix this for the next patch release.

**aborruso:**
Thank you very much @Mytherin
