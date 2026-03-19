# timestamp conversion failed when using sql where clause but it is correct under select clause

**Issue #20708** | State: open | Created: 2026-01-28 | Updated: 2026-03-16
**Author:** weipeng1999
**Labels:** reproduced

### What happens?

timestamp conversion failed when using sql where clause but it is correct under select clause 

### To Reproduce

something strange when i just using "where" clause

```sql
select * from datas where Datetime == '2023-04-02 16:00:00'::timestamp;
```
```
Conversion Error:
invalid timestamp field format: "2023-04-02 16:00:00", expected format is (YYYY-MM-DD HH:MM:SS[.US][±HH[:MM[:SS]]| ZONE])

LINE 1: select * from datas where Datetime == '2023-04-02 16:00:00'::timestamp;                                                                   ^
```
but this is correct format under select clause

```sql
select '2023-04-02 16:00:00'::timestamp;
```
```
┌──────────────────────────────────────────┐
│ CAST('2023-04-02 16:00:00' AS TIMESTAMP) │
│                timestamp                 │
├──────────────────────────────────────────┤
│ 2023-04-02 16:00:00                      │
└──────────────────────────────────────────┘
```
so it was a really confusion 

### OS:

x86_64

### DuckDB Version:

1.4.3

### DuckDB Client:

duckdb-cli

### Hardware:

_No response_

### Full Name:

peng wei

### Affiliation:

FJQXJ

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
Hi @weipeng1999, upon further inspection, I was unable to reproduce the error. Can you please

- provide a full reproducer script
- let me know the operating system that you are using?

**weipeng1999:**
> Hi [@weipeng1999](https://github.com/weipeng1999), upon further inspection, I was unable to reproduce the error. Can you please
> 
> * provide a full reproducer script
> * let me know the operating system that you are using?

sure,  today i test more and think seems due to this strange [parquet file](https://github.com/weipeng1999/some_error_parquet)
with following duckdb sql running in conda environment
``` bash
>>> conda run -n duckdb --live-stream duckdb
DuckDB v1.4.3 (Andium) d1dc88f950
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
D create or replace view datas as from 'example.parquet';
D from datas where Station_Id_c == 'F5481' and '2023-04-02 16:00:00'::timestamp >> fastfetch
                  -`                     weipeng@archlinux-weipeng                                                                                                            
                 .o+`                    -------------------------                                                                                                            
                `ooo/                    OS: Arch Linux x86_64                                                                                                                
               `+oooo:                   Host: HP ZHANX 14 G1a AI (SBKPFV3)                                                                                                   
              `+oooooo:                  Kernel: Linux 6.18.6-zen1-1-zen                                                                                                      
              -+oooooo+:                 Uptime: 45 mins                                                                                                                      
            `/:-:++oooo+:                Packages: 3069 (pacman)                                                                                                              
           `/++++/+++++++:               Shell: zsh 5.9                                                                                                                       
          `/++++++++++++++:              Display (LGD07B5): 1920x1080 in 14", 60 Hz [Built-in]                                                                                
         `/+++ooooooooooooo/`            DE: KDE Plasma 6.5.5                                                                                                                 
        ./ooosssso++osssssso+`           WM: KWin (Wayland)                                                                                                                   
       .oossssso-````/ossssss+`          WM Theme: plastik                                                                                                                    
      -osssssso.      :ssssssso.         Theme: Breeze (Light) [Qt], Breeze [GTK2/3/4]                                                                                        
     :osssssss/        osssso+++.        Icons: breeze [Qt], breeze [GTK2/3/4]                                                                                                
    /ossssssss/        +ssssooo/-        Font: Noto Sans (10pt) [Qt], Noto Sans (10pt) [GTK2/3/4]                                                                             
  `/ossssso+/:-        -:/+osssso+-      Cursor: breeze (36px)
 `+sso+:-`                 `.-/+oso:     Terminal: tmux 3.6a
`++:.                           `-/+/    CPU: AMD Ryzen AI 7 350 (16) @ 5.09 GHz
.`                                 `/    GPU: AMD Radeon 860M Graphics [Integrated]
                                         Memory: 10.82 GiB / 54.69 GiB (20%)
                                         Swap: 283.62 MiB / 4.00 GiB (7%)
                                         Disk (/): 311.93 GiB / 512.00 GiB (61%) - btrfs
                                         Disk (/mnt/data): 108.11 GiB / 1024.00 GiB (11%) - fuseblk
                                         Disk (/mnt/windows): 75.32 GiB / 511.22 GiB (15%) - fuseblk [Read-only]
                                         Local IP (wlan0): 192.168.0.112/24
                                         Battery (Primary): 41% [Discharging]
                                         Locale: zh_CN.UTF-8
archlinux:~ >>> conda env export -n duckdb
name: duckdb
channels:
  - conda-forge
  - pkgs/main
dependencies:
  - _libgcc_mutex=0.1=main
  - _openmp_mutex=5.1=1_gnu
  - ca-certificates=2025.12.2=h06a4308_0
  - duckdb-cli=1.4.3=hecca717_1
  - icu=78.1=h33c6efd_0
  - libduckdb=1.4.3=h77cc3ed_1
  - libgcc=15.2.0=h69a1729_7
  - libgomp=15.2.0=h4751f2c_7
  - libstdcxx=15.2.0=h39759b7_7
  - openssl=3.6.0=h26f9b46_0

prefix: "/conda/envs/duckdb"
```

**rohitmannur007:**
hi @weipeng1999 

I attempted to reproduce the issue using a minimal SQL example.

Reproducer script:

CREATE TABLE datas (
    Station_Id_c VARCHAR,
    Datetime TIMESTAMP
);

INSERT INTO datas VALUES
('F5481','2023-04-02 16:00:00'),
('F5481','2023-04-02 18:00:00');

SELECT *
FROM datas
WHERE '2023-04-02 16:00:00'::timestamp <= Datetime
AND Datetime <= '2023-04-02 20:00:00'::timestamp;

In this case the query executes correctly.

This suggests the problem may be related to how timestamps are parsed when reading the Parquet file rather than the SQL predicate itself.

**rohitmannur007:**
I tried to reproduce the issue on the latest DuckDB development build
(v1.6.0-dev).

Minimal example:

CREATE TABLE datas (
    Station_Id_c VARCHAR,
    Datetime TIMESTAMP
);

INSERT INTO datas VALUES
('F5481','2023-04-02 16:00:00'),
('F5481','2023-04-02 18:00:00');

SELECT *
FROM datas
WHERE '2023-04-02 16:00:00'::timestamp <= Datetime
AND Datetime <= '2023-04-02 20:00:00'::timestamp;

Result:

The query executes correctly and returns the expected rows.

This suggests the problem may be related to how timestamps are read from
the Parquet file rather than the SQL predicate itself.
