# Show HN: HitKeep – Web Analytics in a Single Go Binary (Embedded DuckDB and NSQ)

**HN** | Points: 2 | Comments: 1 | Date: 2026-02-25
**Author:** examo
**HN URL:** https://news.ycombinator.com/item?id=47153832
**Link:** https://github.com/pascalebeier/hitkeep

## Top Comments

**examo:**
Hi, I'm Pascale. I built HitKeep, an open-source, privacy-first web analytics platform that runs as a single static Go binary.To be honest, I thought web analytics cant be that hard to maintain and it can't be impossible to just get all of my data, be it instance-wide, user-wide, site-wide, or filtered. The existing open-source alternatives are fantastic, but have a massive footprint and are not designed for data sovereignty first.HitKeep brings a takeout-first approach where you can export everything to EXCEL, CSV, PARQUET, JSON, or NDJSON, even filtered data.architeture:To achieve "ClickHouse-like" analytics performance, I built HitKeep using:Embedded DuckDB: Used for columnar OLAP storage. It handles aggregations and time-bucketing beautifully, and the entire database is just one (tm) hitkeep.db file.Embedded NSQ: Writing to a columnar DB synchronously per HTTP request creates lock contention. HitKeep embeds an in-process NSQ broker. The HTTP handler enqueues the hit in microseconds, and a background consumer batches writes to DuckDB.Clustering: If you want High Availability, it uses gossip protocol for leader election (Leader holds the DB write lock, followers proxy ingest requests).Embedded UI & Tracker: The Angular SPA and the 2KB tracking script (hk.js) are compiled into the binary via embed.FS.
It idles at around 50MB of RAM and easily runs on a $4 VPS or a Raspberry Pi.Features:Cookie-less by default.
Automatically (optionally) respects Do Not Track headers.
Goals, Multi-step Funnels, Custom Events, and UTM attribution.
Passkeys (WebAuthn) and TOTP built-in for account security.And what always bothers me you can actually log in with just your Passkey or use it as a second factor.Much more to come, but currently I focus on ironing out the uiyou can find the full docs on https:&#x2F;&#x2F;hitkeep.com
