# INTERNAL Error: Failed to bind column reference "id"

**Issue #21419** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** RaczeQ
**Labels:** reproduced

### What happens?

After updating the DuckDB version to 1.5.0, the query that previously worked (up to the newest 1.4 versions) stopped working. Requires `spatial` extension to run.

Two files used in the query: [duckdb_bug_reproduce.zip](https://github.com/user-attachments/files/26047707/duckdb_bug_reproduce.zip)

Full stacktrace:
```
Traceback (most recent call last):
  File "", line 1, in 
  File "/Users/raczeq/Library/Application Support/Code/User/workspaceStorage/d66ab285dad476612fb0ce6c42f42139/ms-python.python/pythonrc.py", line 24, in my_displayhook
    self.original_displayhook(value)
_duckdb.InternalException: INTERNAL Error: Failed to bind column reference "id" [1.0] (bindings: {#[0.0], #[0.1], #[0.2], #[1.1]})

Stack Trace:

0        duckdb_adbc_init + 3548796
1        duckdb_adbc_init + 3444796
2        duckdb_adbc_init + 6619064
3        duckdb_adbc_init + 6618092
4        PyInit__duckdb + 12757784
5        PyInit__duckdb + 12758412
6        PyInit__duckdb + 12758188
7        PyInit__duckdb + 12756744
8        PyInit__duckdb + 12753060
9        duckdb_adbc_init + 6616956
10       PyInit__duckdb + 12752648
11       duckdb_adbc_init + 6616944
12       PyInit__duckdb + 12752648
13       duckdb_adbc_init + 6616944
14       PyInit__duckdb + 12752648
15       duckdb_adbc_init + 6616944
16       PyInit__duckdb + 12752648
17       duckdb_adbc_init + 6616944
18       PyInit__duckdb + 12752648
19       duckdb_adbc_init + 6616944
20       PyInit__duckdb + 12752648
21       duckdb_adbc_init + 6616944
22       duckdb_adbc_init + 6690316
23       duckdb_adbc_init + 6690064
24       duckdb_adbc_init + 7418972
25       duckdb_adbc_init + 7422120
26       duckdb_adbc_init + 7438948
27       duckdb_adbc_init + 7445700
28       duckdb_adbc_init + 7437192
29       duckdb_adbc_init + 7440960
30       duckdb_adbc_init + 7456932
31       duckdb_adbc_init + 7458180
32       PyInit__duckdb + 735352
33       PyInit__duckdb + 783716
34       PyInit__duckdb + 784564
35       PyInit__duckdb + 1502336
36       PyInit__duckdb + 1502176
37       _duckdb.cpython-312-darwin.so + 41780
38       cfunction_vectorcall_FASTCALL_KEYWORDS + 92
39       method_vectorcall + 368
40       slot_tp_repr + 240
41       PyObject_Repr + 180
42       PyFile_WriteObject + 236
43       sys_displayhook + 296
44       _PyEval_EvalFrameDefault + 49688
45       method_vectorcall + 304
46       PyObject_CallOneArg + 128
47       _PyEval_EvalFrameDefault + 10300
48       PyEval_EvalCode + 304
49       run_mod + 176
50       PyRun_InteractiveOneObjectEx + 632
51       _PyRun_InteractiveLoopObject + 156
52       _PyRun_AnyFileObject + 200
53       PyRun_AnyFileExFlags + 68
54       pymain_run_stdin + 164
55       Py_RunMain + 1396
56       pymain_main + 500
57       Py_BytesMain + 40
58       start + 7184

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### To Reproduce

```python
import duckdb
duckdb.load_extension('spatial')

duckdb.sql(
    """
    SELECT
        og.id,
        og.geometry_id,
        st_difference(
            any_value(og.geometry),
            st_union_agg(ig.geometry)
        ) AS geometry
    FROM
        read_parquet('relation_outer_parts.parquet') AS og
        INNER JOIN read_parquet('relation_inner_parts.parquet') AS ig
        ON og.id = ig.id
        AND st_within(ig.geometry, og.geometry)
    GROUP BY
        og.id,
        og.geometry_id
    """
)
```

### OS:

macOS Tahoe 26.3 ARM64 (M3 Pro)

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Kamil Raczycki

### Affiliation:

Open Source Contributor

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Thanks @RaczeQ, I could reproduce the issue! We'll take a look.
