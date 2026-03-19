# .multiline dot command throws errors

**Issue #21308** | State: closed | Created: 2026-03-11 | Updated: 2026-03-13
**Author:** jaywgraves
**Labels:** reproduced

### What happens?

I have a `~/.duckdbrc` file on MacOS with just the single command of `.multiline`

after upgrading to 1.5.0 I get this error on startup
```shell
➜ duckdb
-- Loading resources from /Users/g274496/.duckdbrc
Invalid Command Error:
Invalid usage of command '.multiline'

Usage: '.multiline '
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D
```

If I comment it out, everything works file.

If I try the `.multiline` command I get the same error.
```shell
❯ duckdb
-- Loading resources from /Users/jay/.duckdbrc
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
memory D .multiline
Invalid Command Error:
Invalid usage of command '.multiline'

Usage: '.multiline '
memory D
```

using `.singleline` in the CLI gives a similar error.

Both `.multiline` and `.singleline` are listed in `.help` and on the 1.5 documentation page.
https://duckdb.org/docs/current/clients/cli/dot_commands#list-of-dot-commands

I'm sure this has something to do with the new CLI and I'm guessing I don't need `.multiline` in my `.duckdbrc` any longer. 

### To Reproduce

start a duckdb CLI session and enter the command
`.multiline` 
or
`.singleline`

### OS:

MacOS 14.8.4 (23J319)

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Jay Graves

### Affiliation:

self/personal

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**jaywgraves:**
@Mytherin I have a fix for this locally.  should my PR target `main` or `v1.5-variegata`

**Mytherin:**
Cool - it should target `v1.5-variegata` since this is a regression from v1.4

**jaywgraves:**
Since that MR landed (thank you!) do you want this closed or do you wait until it's released, presumably 1.5.1?

**Mytherin:**
It can be closed now - thanks
