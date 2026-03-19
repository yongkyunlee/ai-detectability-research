# Invalid unicode with Chinese characters when use 'duckdb -c' command

**Issue #21445** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** yangyadonghcl
**Labels:** needs triage, needs reproducible example

### What happens?
 duckdb -c " from 'F:/账单数据/数据备份/汇总/总包裹.parquet' ", this command works in v1.4.4,but fails in v1.5

### To Reproduce

duckdb -c " from '总包裹.parquet'"

### OS:

Windows 11 

### DuckDB Version:

1.5.0

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

yangyadong

### Affiliation:

null

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [ ] Yes, I have

### Did you include all code required to reproduce the issue?

- [ ] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**staticlibs:**
Hi, thanks for the report! It seems that I cannot easily reproduce this:

```sql
> duckdb_150.exe
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D SELECT count(*) FROM 'c:\tmp\账单数据数据备份汇总总包裹.parquet';
┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│          150 │
└──────────────┘
```

This is with the default code page in Windows Terminal:

```cmd
> chcp
Active code page: 437
```

I wonder if there is something specific about your environment (if the problem is in the file name)? Or can the problem be in the file contents processing?

**staticlibs:**
> It seems that I cannot easily reproduce this

Sorry, misinterpreted the second screenshot, it is not stdin, but startup command processing. I will follow up.

**duckdblabs-bot:**
Thanks for opening this issue in the DuckDB issue tracker! To resolve this issue, our team needs a reproducible example. This includes:

* A source code snippet which reproduces the issue.
* The snippet should be self-contained, i.e., it should contain all imports and should use relative paths instead of hard coded paths (please avoid `/Users/JohnDoe/...`).
* A lot of issues can be reproduced with plain SQL code executed in the [DuckDB command line client](https://duckdb.org/docs/api/cli/overview). If you can provide such an example, it greatly simplifies the reproduction process and likely results in a faster fix.
* If the script needs additional data, please share the data as a CSV, JSON, or Parquet file. Unfortunately, we cannot fix issues that can only be reproduced with a confidential data set. [Support contracts](https://duckdblabs.com/#support) allow sharing confidential data with the core DuckDB team under NDA.

For more detailed guidelines on how to create reproducible examples, please visit Stack Overflow's [“Minimal, Reproducible Example”](https://stackoverflow.com/help/minimal-reproducible-example) page.

**yangyadonghcl:**
> > It seems that I cannot easily reproduce this
> 
> Sorry, misinterpreted the second screenshot, it is not stdin, but startup command processing. I will follow up.

Yes, the point is that the **startup command processing** can't parse Chinese characters correctly.
You can try  

`duckdb -c "select 1+1 as '鸭子'";`

**blakethornton651-art:**
I'm trying to reproduce this on my side

On Wed, Mar 18, 2026, 9:18 AM yangyadonghcl ***@***.***>
wrote:

> *yangyadonghcl* left a comment (duckdb/duckdb#21445)
> 
>
> It seems that I cannot easily reproduce this
>
> Sorry, misinterpreted the second screenshot, it is not stdin, but startup
> command processing. I will follow up.
>
> image.png (view on web)
> 
>
> Yes,the point is command interface can't parse chinese character correctly.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

**staticlibs:**
@yangyadonghcl

Thanks for raising this issue, there were multiple fixes to Unicode handling in Windows shell recently, but the command line arguments were overlooked. This should be fixed now by #21472.

With it the following Unicode input works on Windows (in default Windows Terminal):

In `cmd.exe` shell:

```cmd
cmd> duckdb.exe -c "SELECT '🦆'"

cmd> duckdb.exe  "C:\Program Files\Git\usr\bin\echo.exe" "SELECT '🦆'" | duckdb.exe
```

These examples above don't depend on the console code page ([1](https://learn.microsoft.com/en-us/windows/console/console-code-pages), [2](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/chcp))

The following example, with piping Unicode from the in-built `echo` works only when the console is set to UTF-8:

```cmd
cmd> chcp 65001 && echo SELECT '🦆' | duckdb.exe
```

In PowerShell command-line arguments work correctly:

```powershell
PS> .\duckdb.exe -c "SELECT '🦆'"
```

But piping Unicode through a PowerShell pipe does NOT work:

```powershell
# does NOT work
PS> & "C:\Program Files\Git\usr\bin\echo.exe" "SELECT '🦆'" | .\duckdb.exe
```

It is not clear whether some PowerShell setting can help with fixing it. Just right now we do not want to support multiple modes/flags for reading from stdin (we just removed `.utf8` mode that was mostly broken). So it is suggested to use a workaround with calling `cmd.exe` from PowerShell instead, the following examples work correctly:

```powershell
PS> cmd /c "duckdb.exe  cmd /c """C:\Program Files\Git\usr\bin\echo.exe"" ""SELECT '🦆'"" | duckdb.exe"

PS> cmd /c "chcp 65001 && echo SELECT '🦆' | duckdb.exe"
```

For output Unicode data, in-general it works always, but the custom pager is highly recommended, see a warning on the [Output Formats](https://duckdb.org/docs/current/clients/cli/output_formats) doc page.
