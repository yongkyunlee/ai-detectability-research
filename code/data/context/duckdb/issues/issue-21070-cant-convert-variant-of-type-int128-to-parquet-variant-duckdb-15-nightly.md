# Can't convert VARIANT of type 'INT128' to Parquet VARIANT (DuckDB 1.5 nightly)

**Issue #21070** | State: closed | Created: 2026-02-24 | Updated: 2026-03-02
**Author:** ryanworl
**Labels:** reproduced

### What happens?

```
Invalid Input Error:
Can't convert VARIANT of type 'INT128' to Parquet VARIANT
```

### To Reproduce

On DuckDB 1.5 nightly downloaded today:
```sql
copy (select actor::variant as actor, repo::variant as repo, payload::variant as payload, org::variant as org
from 'https://data.gharchive.org/2015-01-01-1.json.gz') to 'foo.parquet' (FORMAT Parquet);
```

Error:
```
Invalid Input Error:
Can't convert VARIANT of type 'INT128' to Parquet VARIANT
```

Interestingly, it doesn't happen if I `set threads = 1;` before executing. That file is publicly available, so hopefully this will be easy to reproduce. It doesn't appear to be 100% deterministic, though.

### OS:

macOS ARM

### DuckDB Version:

v1.5.0-dev7422 (Development Version, d66b932e8e)

### DuckDB Client:

CLI

### Hardware:

Macbook Pro, Apple M3 Pro chip, 18 GB memory

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

**Tishj:**
The only thing I can think of is that your JSON contains unsigned types and signed types for the same field, and that gets upcast to HUGEINT when constructing the duckdb schema for it:
```c++
static LogicalTypeId MaxNumericType(const LogicalTypeId &a, const LogicalTypeId &b) {
    D_ASSERT(a != b);
    if (a == LogicalTypeId::DOUBLE || b == LogicalTypeId::DOUBLE) {
        return LogicalTypeId::DOUBLE;
    }
    if (a == LogicalTypeId::HUGEINT || b == LogicalTypeId::HUGEINT) {
        return LogicalTypeId::HUGEINT;
    }
    // One is BIGINT and the other is UBIGINT - need HUGEINT to represent both ranges
    if ((a == LogicalTypeId::BIGINT && b == LogicalTypeId::UBIGINT) ||
        (a == LogicalTypeId::UBIGINT && b == LogicalTypeId::BIGINT)) {
        return LogicalTypeId::HUGEINT;
    }
    return LogicalTypeId::BIGINT;
}
```

this could in the future be adjusted to output VARIANT I think
so we can preserve both types without having to upgrade to a type that includes both

**ryanworl:**
Is this small enough to include in the 1.5 release? I didn't pick this dataset at random. It is GitHub's event stream, which I think makes for a very good demo of VARIANT.

**ryanworl:**
I just checked the data in the file with a coding agent in a variety of ways and I don't see how this isn't a bug. There aren't any numbers bigger than `INT64`.

**szarnyasg:**
@ryanworl Thanks, I could reproduce it from ~3 runs!

**szarnyasg:**
Hi @ryanworl, this has been fixed by https://github.com/duckdb/duckdb/pull/21024

If you pick the v1.5-dev nightly build from [here](https://duckdb.org/install/preview#command-line-interface-cli-c-and-c-clients), this should already have the fix!

**ryanworl:**
I'm not so sure about this yet. I built from source from latest commit of `v1.5-variegata` and have reproduced the issue.

**ryanworl:**
Another important note: I _cannot_ reproduce the issue when I download the file and run the query against the file locally. It only reproduces when I do it against the remote file.

**ryanworl:**
After 17 million input tokens and 225k output tokens in GPT 5.3 Codex in Cursor, I have this diff to fix:

```
diff --git a/extension/json/json_functions/json_structure.cpp b/extension/json/json_functions/json_structure.cpp
index 8d0633a522..429cdeb746 100644
--- a/extension/json/json_functions/json_structure.cpp
+++ b/extension/json/json_functions/json_structure.cpp
@@ -437,8 +437,9 @@ static void ExtractStructureObject(yyjson_val *obj, JSONStructureNode &node, con
 
 static void ExtractStructureVal(yyjson_val *val, JSONStructureNode &node) {
 	D_ASSERT(!yyjson_is_arr(val) && !yyjson_is_obj(val));
-	auto &desc = node.GetOrCreateDescription(JSONCommon::ValTypeToLogicalTypeId(val));
-	if (desc.type == LogicalTypeId::UBIGINT &&
+	const auto val_type = JSONCommon::ValTypeToLogicalTypeId(val);
+	auto &desc = node.GetOrCreateDescription(val_type);
+	if (val_type == LogicalTypeId::UBIGINT &&
 	    unsafe_yyjson_get_uint(val) > static_cast(NumericLimits::Maximum())) {
 		desc.has_large_ubigint = true;
 	}
```

I'm not going to pretend I know enough about DuckDB's json extension to say if this fix is valid, but it gave me this description of the fix:

> Root cause was in JSON schema extraction: UBIGINT handling was gated on accumulated node description (desc.type) rather than the current value type, so unsafe_yyjson_get_uint(val) could run for non-UBIGINT values (notably NULL), causing spurious large-UBIGINT detection. Fix is to gate on val_type == UBIGINT for the current yyjson_val.

And I can confirm that I can no longer reproduce the issue with this fix applied.

I hope this helps!

**Tishj:**
I think that's correct
As Claude pointed out, in the method to get the description, there's this block:
```c++
	if (type == LogicalTypeId::SQLNULL) {
		// 'descriptions' is non-empty, so let's not add NULL
		return descriptions.back();
	}
```
Meaning if we input SQLNULL, we could get back a non-null type on the description, and then we treat a JSON "null" value as if it was a UBIGINT, reading garbage from it
