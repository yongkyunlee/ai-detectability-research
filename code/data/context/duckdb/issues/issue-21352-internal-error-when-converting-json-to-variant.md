# Internal error when converting json to variant

**Issue #21352** | State: open | Created: 2026-03-13 | Updated: 2026-03-14
**Author:** mwinters0
**Labels:** reproduced

### What happens?

I tried to test the new variant encoding by doing:
1. Load some parquet which contains json text
2. Convert it to JSON
3. Convert the JSON to Variant

The conversion to Variant crashes.

```
INTERNAL Error:
Field is missing but untyped_value_index is not set
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

Stack Trace

```
duckdb() [0xa7c10b]
duckdb() [0xa7c1c4]
duckdb() [0xa7f231]
duckdb() [0x6cfba1]
duckdb() [0x1b50004]
duckdb() [0x1b510b2]
duckdb() [0xef1a33]
duckdb() [0xef9b49]
duckdb() [0xefa5de]
duckdb() [0xebf354]
duckdb() [0xf1c5d5]
duckdb() [0xf637c2]
duckdb() [0xf63ec5]
duckdb() [0xf64015]
duckdb() [0xf791c0]
duckdb() [0xf792a9]
duckdb() [0xf9efeb]
duckdb() [0xf9fcbd]
duckdb() [0xf9b785]
duckdb() [0xf9bbed]
duckdb() [0xd66475]
duckdb() [0xd66a48]
duckdb() [0xd66fa4]
duckdb() [0xd679b6]
duckdb() [0xd67a56]
duckdb() [0xd6b740]
duckdb() [0xd6c19d]
duckdb() [0x85a4e3]
duckdb() [0x85a7f9]
duckdb() [0x85aacb]
duckdb() [0x86566f]
duckdb() [0x8379e1]
/usr/lib/libc.so.6(+0x27635) [0x7f994b627635]
/usr/lib/libc.so.6(__libc_start_main+0x89) [0x7f994b6276e9]
duckdb() [0x83d8be]
```

I tried to binary search the data by id to find a problem row, but I reached a point where both the upper and lower halves of the range completed successfully.  So the crash seems to be related to the size of the operation rather than the data itself.

### To Reproduce

```shell
duckdb --storage-version 'v1.5.0' test.ddb
```
This test parquet file is 133Mb.  I'll keep it available for at least a few months.
```sql
CREATE TABLE messages AS SELECT * FROM 'https://hatlas.mwinters.net/download/vtest.parquet';
ALTER TABLE messages ADD COLUMN msg_json JSON;
UPDATE messages SET msg_json = msg::JSON;
ALTER TABLE messages DROP COLUMN msg;
ALTER TABLE messages ADD COLUMN msg VARIANT;
UPDATE messages SET msg = msg_json::VARIANT;
```

### OS:

Arch Linux

### DuckDB Version:

v1.5.0

### DuckDB Client:

CLI

### Hardware:

x86 (AMD Ryzen 9 3900X)

### Full Name:

Michael Winters

### Affiliation:

Please Hire Me, I'm Broke Inc.

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@mwinters0, thanks, I could reproduce the issue!

**Tishj:**
While debugging I found a workaround in case you're interested:
```sql
ALTER TABLE messages ALTER msg TYPE USING msg::JSON::VARIANT;
```
or
```sql
ALTER TABLE messages
ALTER msg SET DATA TYPE VARIANT USING msg::JSON;
```

(https://duckdb.org/docs/stable/sql/statements/alter_table#set-data-type)

**mwinters0:**
@Tishj I tried both of these.  The command succeeds, but when I quit I get a different error:

```
Silent exception in AttachedDatabase::Close():  FATAL Error: Failed to create checkpoint because of error: FATAL Error: Failed to create checkpoint: INTERNAL Error: Field is missing but untyped_value_index is not set
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

Stack Trace

```
duckdb() [0xa7c10b]
duckdb() [0xa7c1c4]
duckdb() [0xa7f231]
duckdb() [0x6cfba1]
duckdb() [0x1b50004]
duckdb() [0x1b510b2]
duckdb() [0xef1a33]
duckdb() [0xef9b49]
duckdb() [0xefa5de]
duckdb() [0xebf354]
duckdb() [0xf1c5d5]
duckdb() [0xf1cade]
duckdb() [0xf1d973]
duckdb() [0xf404eb]
duckdb() [0xdac25b]
duckdb() [0xdae392]
duckdb() [0xf2835e]
duckdb() [0xf51e2f]
duckdb() [0xf5cc4f]
duckdb() [0xf81796]
duckdb() [0xf6efe9]
duckdb() [0xd40877]
duckdb() [0xd4139d]
duckdb() [0xd466ac]
duckdb() [0x85561a]
duckdb() [0xd66dd3]
duckdb() [0x85561a]
duckdb() [0x837a80]
/usr/lib/libc.so.6(+0x276c1) [0x7f35391186c1]
/usr/lib/libc.so.6(__libc_start_main+0x89) [0x7f35391187f9]
duckdb() [0x83d8be]
```
