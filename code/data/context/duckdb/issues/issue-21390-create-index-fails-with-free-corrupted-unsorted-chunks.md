# CREATE INDEX fails with free(): corrupted unsorted chunks

**Issue #21390** | State: closed | Created: 2026-03-15 | Updated: 2026-03-17
**Author:** ttomasz
**Labels:** reproduced

### What happens?

I tried to create a table with indexed/primary key field.

I'm usually getting error:
```
free(): corrupted unsorted chunks
Aborted (core dumped)
```
Sometimes the error is (when table has PK):
```
corrupted double-linked list
Aborted (core dumped)
```

### To Reproduce

Download data and open a new database:

```bash
wget https://download.openstreetmap.fr/extracts/europe/poland-latest.osm.pbf
duckdb test_size.db
```

Run:
```sql
-- prepare data
install spatial;
load spatial;
set preserve_insertion_order=false;  -- errors with or without this setting
create table node_coords(id int64 not null, lat double not null, lon double not null);
insert into node_coords select id, lat, lon from st_readosm('poland-latest.osm.pbf') where kind = 'node';
-- this is where the problem occurs, tried both unique and non unique as well as primary key
create index idx_node_coords on node_coords(id);
```

### OS:

Linux (x86_64)

### DuckDB Version:

1.5.0 (Variegata)

### DuckDB Client:

CLI

### Hardware:

32GB RAM with more than half free when running test

### Full Name:

Tomasz Taraś

### Affiliation:

Orsted

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @ttomasz, thanks for reporting! I was not yet able to reproduce this on DuckDB v1.5.0 on Ubuntu x86 or arm64. How many threads are you using? Is the error occurring during every run or is it spurious?

**ttomasz:**
Hi @szarnyasg thanks for trying to reproduce. I used default thread count which for my systems is 12 (6 cpu with hyperthreading).

I tried again with 2 threads and 1 thread.

With 1 thread it created the index without crashing, with 2 it crashed.

When trying to create the index with 2 or 12 threads what I'm observing in the CLI is that the reported memory usage is going up and when it reaches around 12-14GB then the time estimate starts going crazy and after a while the progress bar disappears and duckdb crashes with one of the errors mentioned. I think around this memory usage level my system starts to dump stuff to swap.

I'll try again later with nothing else running to have all ram available for duckdb. Maybe it's just running out of memory with an unexpected error.

**szarnyasg:**
Thanks for the info! I have not yet seen `corrupted double-linked list` and `free(): corrupted unsorted chunks` for out-of-memory errors – those tend to be quite clear about the fact that memory exhaustion happened.

**szarnyasg:**
Thanks, I could reproduce this using an  `r7i.2xlarge` AWS instance – 8 vCPU cores, 64 GB RAM, default thread count.

**szarnyasg:**
Hi again @ttomasz – I looked into this deeper and this is already fixed in the nightly build. Now the nightly build (https://duckdb.org/install/preview) currently does not ship the `spatial` extension, so you will not be able to use it for your workload.

However, as a temporary workaround, you can start the data processing with the stable version, then use the nightly version just for creating the index, and then switch back to the stable version to continue the rest of your work with spatial. HTH.

**taniabogatsch:**
Indeed, this should be fixed by https://github.com/duckdb/duckdb/pull/21270, which is going to be shipped in `v1.5.1` together with a newer spatial version.
