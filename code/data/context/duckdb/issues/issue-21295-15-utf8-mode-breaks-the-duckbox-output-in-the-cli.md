# [1.5] .utf8 mode breaks the duckbox output in the CLI

**Issue #21295** | State: closed | Created: 2026-03-11 | Updated: 2026-03-12
**Author:** d-mercier
**Labels:** reproduced

### What happens?

Enabling .utf8 mode inside the DuckDB Windows CLI 1.5.0 makes duckbox formatted output full of characters like `ΓöîΓöÇ`. I'm using the Windows 11 Terminal application to run the CLI in a Command Prompt.

### To Reproduce

Perform a select or a describe with .utf8 previously enabled.

```
load spatial;
.utf8
select id, bbox, theme from read_parquet('s3://overturemaps-us-west-2/release/2026-01-21.0/theme=buildings/type=building/part-00000-47160ab1-2f19-4475-89f8-cc1348df69a6-c000.zstd.parquet')  limit 1;
```

or 
```
load spatial;
.utf8
describe select id, bbox, theme from read_parquet('s3://overturemaps-us-west-2/release/2026-01-21.0/theme=buildings/type=building/part-00000-47160ab1-2f19-4475-89f8-cc1348df69a6-c000.zstd.parquet')  limit 1;
```

### OS:

Windows 11

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

David Mercier

### Affiliation:

Aechelon Technology

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**staticlibs:**
@d-mercier 

Hi, thanks for the report! `.utf8` mode requires the terminal code page to be set to UTF-8:

```cmd
chcp 65001
```

Just is there any reason to use `.utf8` with 1.5.0? This option is experimental and [undocumented](https://duckdb.org/docs/current/clients/cli/dot_commands). Perhaps we can just remove it.

See also #21191.

**d-mercier:**
Up until version 1.5 I enabled .utf8 when I launched duckdb in the terminal with -cmd .utf8 (in the terminal profile). There wasn't a downside as far as I could tell, but it made the rendering of UTF8 characters work without the chcp step. Enabling chcp 65001 does help with the duckbox rendering but it doesn't entirely resolve the UTF8 character rendering (especially when using ".mode lines" which I commonly use). Here's an example feature that has UTF8 characters in the name.primary field.

`select names.primary from read_parquet('s3://overturemaps-us-west-2/release/2026-01-21.0/theme=buildings/type=building/part-00169-47160ab1-2f19-4475-89f8-cc1348df69a6-c000.zstd.parquet') where id='fb100188-e319-4500-bccf-ba89ee800852';`

This shows what happens with the default terminal 437 code page:

This shows what happens with the code page set to 65001:

**d-mercier:**
Also the .utf8 command is still in the .help so that's where I first found it.

**staticlibs:**
@d-mercier 

> especially when using ".mode lines" which I commonly use

Thanks for the clarification! The `.mode lines` appeared to be broken on Windows in 1.5.0 (prints duplicate values, we will look into this), but I cannot reproduce any Unicode problems with it:

```cmd
> chcp
Active code page: 437
```
```sql
> duckdb_150.exe
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D .mode lines
memory D select 'おはようございます1' as col1 from range(1);
 col1 = おはようございます1
memory D select 'おはようございます2' as col1 from range(2);
 col1 = おはようございます2おはようございます2

 col1 = おはようございます2
memory D select 'おはようございます3' as col1 from range(3);
 col1 = おはようございます3おはようございます3おはようございます3

 col1 = おはようございます3おはようございます3

 col1 = おはようございます3
```

> Also the .utf8 command is still in the .help so that's where I first found it.

We currently assume that `.utf8` is no longer applicable to 1.5.0 and would like to remove it. If there are known cases when the Unicode is rendered correctly only with `.utf8` (like it was with `.last` in #21191) - please let us know!

**d-mercier:**
My second screen shot shows a case where the .utf8 makes the .mode lines output render correctly.

**staticlibs:**
@d-mercier 

I cannot reproduce the problem on the second screenshot:

```sql
> chcp
Active code page: 65001

> duckdb_150.exe
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D select 'おはようございます2' as col1 from range(2);
┌─────────────────────┐
│        col1         │
│       varchar       │
├─────────────────────┤
│ おはようございます2 │
│ おはようございます2 │
└─────────────────────┘
memory D .mode lines
memory D select 'おはようございます1' as col1 from range(1);
 col1 = おはようございます1
memory D select 'おはようございます2' as col1 from range(2);
 col1 = おはようございます2おはようございます2

 col1 = おはようございます2
```

Any idea what I am doing differently from your example on the screenshot?

**staticlibs:**
@d-mercier 

Sorry, sent this too soon, I think the Unicode handling on your screenshot is correct, it is just the raw memory garbage (not a broken Unicode) is printed at the end of the line, while in my case it prints the duplicated value - likely also a raw memory. So I can indeed reproduce it, and it surely is supposed to work without `.utf8`.

**Mytherin:**
Should be fixed by https://github.com/duckdb/duckdb/pull/21319
