# DuckDB CLI: highlight/autocomplete not working on Windows.

**Issue #10302** | State: closed | Created: 2024-01-22 | Updated: 2026-03-14
**Author:** adrivn
**Labels:** under review

### What happens?

When running the CLI version of DuckDB, under Windows, neither the *highlight* or the *autocomplete* features work as expected.

### To Reproduce

Tested on DuckDB v0.9.2 under Windows 10 Version 10.0.19044 Build 19044 + Windows Terminal 1.18.3181.0.

Basically, the highlight options cannot be activated. Help says:

    .highlight [on|off] Toggle syntax highlighting in the shell on/off

But upon entering .highlight on it results in an error

    D .highlight on
    Error: unknown command or invalid arguments: "highlight". Enter ".help" for help

Same goes for the [autocomplete extension for the CLI ](https://duckdb.org/docs/extensions/autocomplete.html), when ran on Linux it behaves as expected, whereas under Windows it does NOT:

    Use ".open FILENAME" to reopen on a persistent database.
    D SELE
    D SELE__<cursor shifts to this position instead of suggesting full SELECT command

If you need me to run any additional tests or to provide more information about the system, please let me know.

### OS:

Windows 10 Version 10.0.19044 Build 19044 

### DuckDB Version:

v0.9.2

### DuckDB Client:

CLI

### Full Name:

Adrian Emege

### Affiliation:

No affiliation

### Have you tried this on the latest `main` branch?

I have tested with a main build

### Have you tried the steps to reproduce? Do they include all relevant data and configuration? Does the issue you report still appear there?

- [X] Yes, I have

## Comments

**szarnyasg:**
@adrivn I don't have a Windows machine at hand but one piece of information: the DuckDB on the `main` branch has a new CLI shell which allows multiline editing. Can you please give it a go to see whether it fixes the highlight issue?
You can find a nightly build here: https://artifacts.duckdb.org/latest/duckdb-binaries-windows.zip

**adrivn:**
@szarnyasg I just ran the latest nightly build for the DuckDB Windows CLI (`duckdb_cli-windows-amd64.zip`) but it's the same as with the v0.9.2: no autocomplete, no syntax highlight. 

I can confirm that both v0.9.2 and nightly builds work as intended under Linux x64, not so in Windows.

**szarnyasg:**
I can also confirm that this is currently not working. It is not planned to be fixed in the v0.10 release.

**kwando:**
It seems kinda broken in MacOS too to be honest. Tab autocompletes something random most of the time.
```
❯ duckdb --version
v0.9.2 3c695d7ba9
❯ neofetch
                    'c.          kwando@_ 
                 ,xNMM.          --------                                                                                                                                                                                                                                                               
               .OMMMMo           OS: macOS 14.2.1 23C71 x86_64                                                                                                                                                                                                                                          
               OMMM0,            Host: MacBookPro18,4                                                                                                                                                                                                                                                   
     .;loddo:' loolloddol;.      Kernel: 23.2.0                                                                                                                                                                                                                                                         
   cKMMMMMMMMMMNWMMMMMMMMMM0:    Uptime: 5 days, 7 hours, 7 mins                                                                                                                                                                                                                                        
 .KMMMMMMMMMMMMMMMMMMMMMMMWd.    Packages: 325 (brew)                                                                                                                                                                                                                                                   
 XMMMMMMMMMMMMMMMMMMMMMMMX.      Shell: zsh 5.9                                                                                                                                                                                                                                                         
;MMMMMMMMMMMMMMMMMMMMMMMM:       Resolution: 3440x1440, 1512x982                                                                                                                                                                                                                                        
:MMMMMMMMMMMMMMMMMMMMMMMM:       DE: Aqua                                                                                                                                                                                                                                                               
.MMMMMMMMMMMMMMMMMMMMMMMMX.      WM: Quartz Compositor                                                                                                                                                                                                                                                  
 kMMMMMMMMMMMMMMMMMMMMMMMMWd.    WM Theme: Blue (Dark)                                                                                                                                                                                                                                                  
 .XMMMMMMMMMMMMMMMMMMMMMMMMMMk   Terminal: /dev/ttys007                                                                                                                                                                                                                                             
  .XMMMMMMMMMMMMMMMMMMMMMMMMK.   CPU: Apple M1 Max                                                                                                                                                                                                                                                      
    kMMMMMMMMMMMMMMMMMMMMMMd     GPU: Apple M1 Max                                                                                                                                                                                                                                                      
     ;KMMMMMMMWXXWMMMMMMMk.      Memory: 5897MiB / 65536MiB                                                                                                                                                                                                                                             
       .cooc,.    .,coo:.                                                                                                                                                                                                                                                                               
                                                         
                                                         
```

**github-actions[bot]:**
This issue is stale because it has been open 90 days with no activity. Remove stale label or comment or this will be closed in 30 days.

**adrivn:**
Any news on this?

**abubelinha:**
I am testing `duckdb v1.0.0 1f98600c2c` on Windows 7 Home Premium SP1 64 bits

I can confirm autocomplete does not work here either.
(I wouldn't expect `.highlight` to work since [docs](https://duckdb.org/docs/api/cli/syntax_highlighting) say it is only available for Linux/Mac)

**gregorywaynepower:**
Any luck on getting autocomplete working on Windows machines? Or will autocomplete only be supported on Mac/Linux machines?

Currently using [Harlequin](https://harlequin.sh/) as a workaround, which works--I just miss at least having autocomplete when I'm on Windows.

Can confirm that autocomplete works in [DBeaver](https://dbeaver.io/) as well.

**mandarinamdar:**
D .version
DuckDB v1.2.0 5f5512b827
msvc-1929

I am using above version on Windows 11, 24H2 (OS Build 26100.3194)

Autocomplete does not work. Keeps on adding tabs but no autocomplete

**ededovic:**
Same here as well, auto complete does not work on windows nor git for windows. It works on linux. 
D .version
DuckDB v1.3.2 (Ossivalis) 0b83e5d2f6
msvc-1944
