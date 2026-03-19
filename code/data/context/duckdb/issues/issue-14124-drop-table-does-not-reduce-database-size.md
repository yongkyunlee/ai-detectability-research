# DROP TABLE does not reduce database size

**Issue #14124** | State: open | Created: 2024-09-25 | Updated: 2026-03-03
**Author:** steven-luabase
**Labels:** under review

### What happens?

Is the expected behavior  that after DROP a table that database_size decreases? I've been trying to replicate the test case mentioned in this [PR](https://github.com/duckdb/duckdb/pull/12318) using the Python client on duckdb 1.1.1 and not seeing database size nor file size decrease after dropping.

### To Reproduce

Here is what I'm running:
```
import duckdb
print(duckdb.__version__) # check that duckdb version is latest (1.1.1)

con = duckdb.connect(database='test.duckdb', read_only=False) #create and connect to a database file

insert_sql = '''
CREATE TABLE test (x INT, y AS (x + 100));
insert into test select range FROM range(1000000000);

con.execute(insert_sql)
con.execute("PRAGMA database_size").fetchall()
```
Which returns:
```
[('test', '8.7 MiB', 262144, 35, 35, 0, '0 bytes', '8.7 MiB', '25.5 GiB')]
```
Then I drop the table and check the size again:
```
con.execute("DROP TABLE test")
con.execute("PRAGMA database_size").fetchall()
```
And see that the database size has not changed:
```
[('test', '8.7 MiB', 262144, 35, 35, 0, '64 bytes', '1.5 MiB', '25.5 GiB')]
```
Am I missing something here or is the Python client doing something different?

### OS:

macos

### DuckDB Version:

1.1.1

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Steven Wang

### Affiliation:

definite.app

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have not tested with any build

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

### Did you include all code required to reproduce the issue?

- [ ] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [ ] Yes, I have

## Comments

**szarnyasg:**
Hi @steven-luabase, thanks for opening this issue. A few pointers and questions to help guide the discussion on this:

1) Which operating system are you running in?
2) Please consult the thread for #14087, it seems to be a closely related issue, possibly a duplicate.
3) See the limitations on reclaiming disk space: https://duckdb.org/docs/sql/statements/drop.html#limitations-on-reclaiming-disk-space

**steven-luabase:**
Hi @szarnyasg 
1. MacOS Sonoma
2. Yep it looks similar though I am using a database file instead of an in memory database

Mainly raising this issue because this similar [issue](https://github.com/duckdb/duckdb/issues/12286) was marked as resolved in this [PR](https://github.com/duckdb/duckdb/pull/12318)

**zhaoxin:**
It seems that:
1. VACUUM not implemented
2. DROP TABLE only make new free_blocks, not reduce db file size on disk

So the db file size will keep increasing, no chance to decrease?

**garyLiuxh:**
and more, when truncate a table, the size of DB will be increased.

code:
CREATE TABLE test (x INT, y AS (x + 100));
insert into test select range FROM range(1000000000);
truncate table test;

**mcphatty:**
Sorry to ask, but are there any news on this issue? We are thinking about integrating DuckDB (1.2.0) into our software project and I can reproduce this issue (by adding two large tables, removing the content of the first table via "DELETE FROM table_name;"). Calling "CHECKPOINT" after removing the table contents is not really helping.

If you need a concrete example I can compile one, but its really just creating and filling some tables and removing data from any table which is not the last one as far as I can judge.

We have a recomputation routine which removes table content and refills it with new data at the end of computation. If our database disk size grows significantly after each recompute this would be a real dealbreaker for us, given the fact that we appreciate built-in compression a lot compared to SQLite.

Exporting and re-reading the whole database in mem or on disk is also not an option unfortunately to reclaim space. Some working alternative to VACUUM would be greatly appreciated.

Thanks in advance,
Phil

Linux (Ubuntu 24.04.2 LTS), x86_64, C-API, Version 1.2.0

**garyLiuxh:**
hello, buddy.
&nbsp;&nbsp;&nbsp; have a little advice:
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1&gt; truncate should be drop and reCreate. now it is delete from 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 2&gt; vacuum clear the rows deleted in backgroud.



GaryLiu.晓辉
***@***.***



&nbsp;




------------------&nbsp;原始邮件&nbsp;------------------
发件人:                                                                                                                        "duckdb/duckdb"                                                                                    ***@***.***&gt;;
发送时间:&nbsp;2025年2月18日(星期二) 晚上6:17
***@***.***&gt;;
***@***.******@***.***&gt;;
主题:&nbsp;Re: [duckdb/duckdb] DROP TABLE does not reduce database size (Issue #14124)



   
Sorry to ask, but are there any news on this issue? We are thinking about integrating DuckDB (1.2.0) into our software project and I can reproduce this issue (by adding two large tables, removing the content of the first table via "DELETE FROM table_name;"). Calling "CHECKPOINT" after removing the table contents is not really helping.
 
If you need a concrete example I can compile one, but its really just creating and filling some tables and removing data from any table which is not the last one as far as I can judge.
 
We have a recomputation routine which removes table content and refills it with new data at the end of computation. If our database disk size grows significantly after each recompute this would be a real dealbreaker for us, given the fact that we appreciate built-in compression a lot compared to SQLite.
 
Exporting and re-reading the whole database in mem or on disk is also not an option unfortunately to reclaim space. Some working alternative to VACUUM would be greatly appreciated.
 
Thanks in advance,
 Phil
 
Linux (Ubuntu 24.04.2 LTS), x86_64, C-API, Version 1.2.0

—
Reply to this email directly, view it on GitHub, or unsubscribe.
You are receiving this because you commented.Message ID: ***@***.***&gt;
  mcphatty left a comment (duckdb/duckdb#14124)
 
Sorry to ask, but are there any news on this issue? We are thinking about integrating DuckDB (1.2.0) into our software project and I can reproduce this issue (by adding two large tables, removing the content of the first table via "DELETE FROM table_name;"). Calling "CHECKPOINT" after removing the table contents is not really helping.
 
If you need a concrete example I can compile one, but its really just creating and filling some tables and removing data from any table which is not the last one as far as I can judge.
 
We have a recomputation routine which removes table content and refills it with new data at the end of computation. If our database disk size grows significantly after each recompute this would be a real dealbreaker for us, given the fact that we appreciate built-in compression a lot compared to SQLite.
 
Exporting and re-reading the whole database in mem or on disk is also not an option unfortunately to reclaim space. Some working alternative to VACUUM would be greatly appreciated.
 
Thanks in advance,
 Phil
 
Linux (Ubuntu 24.04.2 LTS), x86_64, C-API, Version 1.2.0
 
—
Reply to this email directly, view it on GitHub, or unsubscribe.
You are receiving this because you commented.Message ID: ***@***.***&gt;

**ml31415:**
> Exporting and re-reading the whole database in mem or on disk is also not an option unfortunately to reclaim space. Some working alternative to VACUUM would be greatly appreciated.

Simply a working VACUUM would be a great start I guess, to make duckdb a viable alternative in any long running process / service.

**andreamoro:**
I experienced this issue and have opened a new report with a concrete reproduction (1.26 GB → 256 MB via `COPY FROM DATABASE` workaround) and a feature request: #21154
