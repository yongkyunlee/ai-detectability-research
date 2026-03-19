# AliSQL: Alibaba's open-source MySQL with vector and DuckDB engines

**HN** | Points: 306 | Comments: 49 | Date: 2026-02-03
**Author:** baotiao
**HN URL:** https://news.ycombinator.com/item?id=46875228
**Link:** https://github.com/alibaba/AliSQL

## Top Comments

**dzonga:**
having an embedded column database for analytics in your traditional db is a massive win for productivity + operations simplicity.at the moment I use PG + Tiger Data - couldn't find a mysql equivalentso this as one.

**linuxhansl:**
Curious how it stacks up to pg_duckdb.
(pg_duckdb seems pretty clean, due to Postres' powerful extension mechanisms)

**Keyframe:**
On a drive-by-glance it looks like if you had a tighter integrated version of PSQL FDW for DuckDB and Vector Storage - meets Vespa. I find it interesting they went with extending MySQL instead of FDW route on PSQL?

**jimmyl02:**
HTAP is here! It seems like these hybrid databases are slowly gaining adoption which is really cool to see.The most interesting part of this is the improvements to transaction handling that it seems they've made in https:&#x2F;&#x2F;github.com&#x2F;alibaba&#x2F;AliSQL&#x2F;blob&#x2F;master&#x2F;wiki&#x2F;duckdb&#x2F;du... (its also a good high level breakdown of MySQL internals too). Ensuring that the sync between the primary tables and the analytical ones are fast and most importantly, transactional, is awesome to see.

**polskibus:**
Does this feed DuckDb continuously data from transactional workloads, akin to what SAP hana does? If so that would be huge - people spend lots of time trying to stitch transactional data to warehouses using Kafka&#x2F;debezium.BTW, Would be great to hear apavlo’s opinion on this.

**enamya:**
the commits history looks a bit weird, 2 commits in 2022, 1 in 2024 and 2025, and 5 in 2026 (one is "First commit, Support DuckDB Engine")

**aussieguy1234:**
I hope the poor devs that built this wernt subjected to the brutal 996 culture (9am-9pm, 6 days per week)

**anentropic:**
How easy will this be to combine with https:&#x2F;&#x2F;github.com&#x2F;mysql&#x2F;mysql-operator for deployment?

**redwood:**
Wonder how DuckDB compares here to what TiDB did using Clickhouse instead

**cies:**
I get the feeling that Oracle is abandonning MySQL.Let's all hope Ali will pick it up :)I'm fully invested on Postgres though.
