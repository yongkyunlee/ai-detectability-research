# INTERNAL: Error when selecting data loaded from huggingface dataset using a limit clause

**Issue #21289** | State: closed | Created: 2026-03-10 | Updated: 2026-03-17
**Author:** maurice1408
**Labels:** reproduced

### What happens?

Loaded the training dataset from

https://huggingface.co/datasets/e1879/threads-english-tech-news-sft

by downloading the [`train-00000-of-00001.parquet`](https://huggingface.co/datasets/e1879/threads-english-tech-news-sft/blob/main/data/train-00000-of-00001.parquet) file and loading into DuckDB v1.5.0 (Variegata).

Using the cli...

On Debian Bulseye...

when issuing

```sql
select "instruction" from 'train-00000-of-00001.parquet' limit 10;
```

It produces:
```
INTERNAL Error: Misaligned render width provided for string "Write a short Threads post for an English tech-news account about the US government officially designating AI company Anthropic a “supply chain risk.” Start with a punchy hook and include the 🇺🇸 flag emoji. Clearly state the designation and explain why it’s notable: the label is typically r"
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors

Stack Trace:

duckdb() [0xa7c10b]
duckdb() [0xa7c1c4]
duckdb() [0xa7f231]
duckdb() [0x87b797]
duckdb() [0x492965]
duckdb() [0xabe274]
duckdb() [0xac08c3]
duckdb() [0xac13bf]
duckdb() [0x88106a]
duckdb() [0x884766]
duckdb() [0x85a49a]
duckdb() [0x85a7f9]
duckdb() [0x85aacb]
duckdb() [0x86566f]
duckdb() [0x8379e1]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0xea) [0x7fc258bcdd7a]
duckdb() [0x83d8be]
```

### OS:

MacOS Tohoe 26.3 and Debian Bullseye

### DuckDB Version:

1.5

### DuckDB Client:

cli

### Hardware:

Macbook Pro M3

### Full Name:

Maurice Hickey

### Affiliation:

Nisos

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
Thanks @maurice1408, I could reproduce the issue.

**Mytherin:**
Thanks for filing - fixed in https://github.com/duckdb/duckdb/pull/21409
