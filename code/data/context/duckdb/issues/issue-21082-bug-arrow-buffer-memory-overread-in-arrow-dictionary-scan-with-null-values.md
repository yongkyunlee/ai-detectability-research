# bug: [Arrow] Buffer memory overread in Arrow dictionary scan with NULL values

**Issue #21082** | State: closed | Created: 2026-02-25 | Updated: 2026-03-09
**Author:** rustyconover
**Labels:** under review

### What happens?

Hi DuckDB Team,

There's a bug dealing with Arrow dictionaries that contain null values.  @pdet this is likely in your area, it is a simple fix.  The allocation is just off by one value for nulls in the dictionary.  This happens in 1.4 and 1.5.

`ColumnArrowToDuckDBDictionary` in `src/function/table/arrow_conversion.cpp` allocates the dictionary vector with exactly `dictionary->length` entries. When NULL values are present in the dictionary-encoded column, `SetMaskedSelectionVectorLoop` sets the selection index for NULL rows to `last_element_pos`, which equals `dictionary->length` — one past the end of the allocated buffer. This is an out-of-bounds read on the dictionary vector.

The read lands in uninitialized or adjacent memory. Depending on allocation layout, this can surface as garbage values, incorrect NULL handling, or a crash (e.g. under AddressSanitizer).

### Root cause

In `SetMaskedSelectionVectorLoop`, NULL rows are pointed at `last_element_pos` as a sentinel:

```cpp
// line 1283
} else {
    //! Need to point out to last element
    sel.set_index(row, last_element_pos);  // last_element_pos == dictionary->length
}
```

But the dictionary vector is only allocated with `dictionary->length` entries (valid indices `0` through `length - 1`):

```cpp
auto base_vector = make_uniq(vector.GetType(),
    NumericCast(array.dictionary->length));  // no room for sentinel
```

So every NULL row reads one element past the end of the buffer.

### Fix

Allocate one extra entry beyond the dictionary length for the NULL sentinel, and mark it invalid:

```cpp
auto dict_length = NumericCast(array.dictionary->length);
auto base_vector = make_uniq(vector.GetType(), dict_length + 1);
ArrowToDuckDBConversion::SetValidityMask(*base_vector, *array.dictionary, chunk_offset,
                                         dict_length, 0, 0, has_nulls);
FlatVector::Validity(*base_vector).SetInvalid(dict_length);
```

This ensures the sentinel index `dictionary->length` points to a valid (but NULL-marked) entry in the buffer, rather than reading past the end.

A PR to address this issue will be posted in just a moment.

### Environment

- DuckDB v1.4.4 and 1.5
- Affects all platforms

### To Reproduce

This bug is triggered when DuckDB scans a dictionary-encoded Arrow array containing NULLs via the C Data Interface (i.e. through `arrow_scan` / the Arrow scan infrastructure).

**This cannot currently be reproduced using pure SQL.** The `nanoarrow` community extension provides `read_arrow()` / `scan_arrow_ipc()` for reading Arrow IPC files, but it does not support dictionary-encoded columns:

```
IO Error: ArrowIpcDecoderDecodeSchema(...) failed with errno 45:
  Schema message field with DictionaryEncoding not supported
```

However, any extension or application that passes dictionary-encoded Arrow data through the C Data Interface (e.g. via `arrow_scan`, or any custom extension using `ArrowToDuckDB`) will hit this bug if the data contains NULLs. A minimal PyArrow example that produces such data:

```python
"""
Reproducer: buffer overread in Arrow dictionary conversion with NULLs.

DuckDB's ColumnArrowToDuckDBDictionary allocates the dictionary vector with
dictionary->length entries, but NULL indices point to dictionary->length
(one past the end). This script triggers that code path via the Python API.

The bug is a 1-element overread. With a small dictionary (1 entry), the
sentinel index reads position 1 in a 1-element buffer. We use multiple
batches and verify the NULL values come back correctly.
"""
import pyarrow as pa
import duckdb

print(f"duckdb version: {duckdb.__version__}")
print(f"pyarrow version: {pa.__version__}")

# Strategy: use a single-entry dictionary so the sentinel reads index 1
# in a buffer of size 1. Write many batches to increase chance of
# observable corruption.
dictionary = pa.array(["only_value"])

# Many NULLs to maximize reads of the sentinel position
indices = pa.array([0, None] * 5000, type=pa.int8())
dict_array = pa.DictionaryArray.from_arrays(indices, dictionary)
arrow_table = pa.table({"val": dict_array})

print(f"Rows: {len(arrow_table)}, Dictionary size: 1")
print(f"Querying via DuckDB arrow_scan...")

result = duckdb.sql("SELECT val, count(*) as cnt FROM arrow_table GROUP BY val ORDER BY val").fetchall()
print(f"\nGrouped result: {result}")

# Verify correctness: should be exactly 5000 'only_value' and 5000 NULL
for val, cnt in result:
    if val is None:
        assert cnt == 5000, f"Expected 5000 NULLs, got {cnt}"
    elif val == "only_value":
        assert cnt == 5000, f"Expected 5000 'only_value', got {cnt}"
    else:
        print(f"UNEXPECTED VALUE: {val!r} (count={cnt}) -- likely corruption from overread!")

print("\nNote: The overread reads 1 element past the dictionary buffer.")
print("Under ASan this would be detected. Without ASan, the read may")
print("silently return whatever is in adjacent memory.")
```

### OS:

macOS

### DuckDB Version:

1.4 and 1.5

### DuckDB Client:

CLI

### Hardware:

Macbook Air

### Full Name:

Rusty Conover

### Affiliation:

Query.Farm

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes
