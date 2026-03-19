# CLI `.last` renders incorrectly in v1.5

**Issue #21191** | State: closed | Created: 2026-03-05 | Updated: 2026-03-09
**Author:** teklinp
**Labels:** under review

### What happens?

Query result displays correctly in the CLI, but the `.last` command shows encoding issues both in table borders and inside cell values.

### To Reproduce

```
select 'ü' as u from range(50);
.last
```

**Output:**

```
DuckDB v1.5.0-dev7575 (Development Version, 8a12a2bce1)
Enter ".help" for usage hints.
memory D select 'ü' as u from range(50);
┌────────────┐
│     u      │
│  varchar   │
├────────────┤
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ·          │
│ ·          │
│ ·          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
│ ü          │
└────────────┘
   50 rows
  (40 shown)
memory D .last
-ŽŽŽŽŽŽŽŽŽČ
-    u    -
- varchar -
+ŽŽŽŽŽŽŽŽŽ+
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
- Ř       -
LŽŽŽŽŽŽŽŽŽ-
  50 rows
```

### OS:

windows_amd64

### DuckDB Version:

DuckDB v1.5.0-dev7575 (Development Version, 8a12a2bce1)

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Piotr Tekliński

### Affiliation:

None

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**staticlibs:**
Hi, thanks for the report! This should be fixed in #21202, going to be included into 1.5.1.

Also, even with the fix, the default `C:\Windows\System32\more.com` console pager can show minor glitches. So it is suggested to use `less` pager from WinGit (only works properly with the #21202 fix included) instead:

```sql
.pager '"C:\Program Files\Git\usr\bin\less.exe" -R'
```
