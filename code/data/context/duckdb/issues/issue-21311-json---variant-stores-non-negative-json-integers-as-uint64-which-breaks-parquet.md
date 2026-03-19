# `JSON -> VARIANT` stores non-negative JSON integers as `UINT64`, which breaks Parquet `VARIANT` export

**Issue #21311** | State: closed | Created: 2026-03-11 | Updated: 2026-03-15
**Author:** ryanworl
**Labels:** reproduced

### What happens?

**Summary**

DuckDB currently preserves yyjson’s unsigned integer tag when casting JSON to `VARIANT`, so ordinary JSON integers like `42` become `VariantLogicalType::UINT64` instead of `INT64`. The Parquet `VARIANT` writer rejects `UINT64`, so `COPY ... TO PARQUET` fails for normal JSON-originated data that would fit comfortably in `INT64`.

**Source references**

```cpp
581:584:duckdb-src/third_party/yyjson/include/yyjson.hpp

/** Unsigned integer subtype: `uint64_t`. */
#define YYJSON_SUBTYPE_UINT     ((uint8_t)(0 (result, result_index, values_offset_data, blob_offset_data[result_index],
                                     nullptr, 0, VariantLogicalType::UINT64);
    if (WRITE_DATA) {
        auto value = unsafe_yyjson_get_uint(val);
        memcpy(blob_data + blob_offset_data[result_index], const_data_ptr_cast(&value), sizeof(uint64_t));
    }
    blob_offset_data[result_index] += sizeof(uint64_t);
    break;
}
case YYJSON_TYPE_NUM | YYJSON_SUBTYPE_SINT: {
    WriteVariantMetadata(result, result_index, values_offset_data, blob_offset_data[result_index],
                                     nullptr, 0, VariantLogicalType::INT64);
```

```cpp
523:533:duckdb-src/extension/parquet/writer/variant/convert_variant.cpp

case VariantLogicalType::TIMESTAMP_SEC:
case VariantLogicalType::TIME_MICROS_TZ:
case VariantLogicalType::TIME_NANOS:
case VariantLogicalType::UINT8:
case VariantLogicalType::UINT16:
case VariantLogicalType::UINT32:
case VariantLogicalType::UINT64:
case VariantLogicalType::UINT128:
case VariantLogicalType::INT128:
default:
    throw InvalidInputException("Can't convert VARIANT of type '%s' to Parquet VARIANT",
```

### To Reproduce

```sql
COPY (
  SELECT '1'::JSON::VARIANT AS v
) TO 'repro.parquet' (FORMAT PARQUET);
```

```
Invalid Input Error:
Can't convert VARIANT of type 'UINT64' to Parquet VARIANT
```

### OS:

macOS

### DuckDB Version:

1.5

### DuckDB Client:

CLI

### Hardware:

MacBook Air

### Full Name:

Ryan Worl

### Affiliation:

Confluent

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**ryanworl:**
Tagging @Tishj since you're probably the right person for this.

**Tishj:**
Also mentioned here https://github.com/duckdb/duckdb/pull/21024

**Mytherin:**
Thanks for reporting - this should now be fixed in https://github.com/duckdb/duckdb/pull/21357
