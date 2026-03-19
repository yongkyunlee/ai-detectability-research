# Why DuckDB is my first choice for data processing

**HN** | Points: 310 | Comments: 119 | Date: 2026-01-16
**Author:** tosh
**HN URL:** https://news.ycombinator.com/item?id=46645176
**Link:** https://www.robinlinacre.com/recommend_duckdb/

## Top Comments

**DangitBobby:**
Being able to use SQL on CSV and json&#x2F;jsonl files is pretty sweet. Of course it does much more than that, but that's what I do most often with it. Love duckdb.

**oulu2006:**
That's really interesting, I love the idea of being able to use columnar support directly within postgresql.I was thinking of using Citus for this, but possibly using duckdb is a better way to do. Citus comes with a lot more out of the box but duckdb could be a good stepping stone.

**clumsysmurf:**
DuckDB has experimental builds for Android ... I'm wondering how much work it would take to implement a Java API for it similar to sqlite (Cursor, etc).

**smithclay:**
Agree with the author, will  add: duckdb is an extremely compelling choice if you’re a developer and want to embed analytics in your app (which can also run in a web browser with wasm!)Think this opens up a lot of interesting possibilities like more powerful analytics notebooks like marimo (https:&#x2F;&#x2F;marimo.io&#x2F;) … and that’s just one example of many.

**tjchear:**
I’ve not used duckdb before nor do I do much data analysis so I am curious about this one aspect of processing medium sized json&#x2F;csv with it: the data are not indexed, so any non-trivial query would require a full scan. Is duckdb so fast that this is never really a problem for most folks?

**biophysboy:**
I think my favorite part of duckdb is its flexibility. Its such a handly little swiss army knife for doing analytical processing in scientific environments (messy data w&#x2F; many formats).

**s-a-p:**
"making DuckDB potentially a suitable replacement for lakehouse formats such as Iceberg or Delta lake for medium scale data" > I'm a Data Engineering noob, but DuckDB alone doesn't do metadata & catalog management, which is why they've also introduce DuckLake.Related question, curious as to your experience with DuckLake if you've used it. I'm currently setting up s3 + Iceberg + duckDB for my company (startup) and was wondering what to pick between Iceberg and DuckLake.

**noo_u:**
I'd say the author's thoughts are valid for basic data processing. Outside of that, most of claims in this article, such as:"We're moving towards a simpler world where most tabular data can be processed on a single large machine1 and the era of clusters is coming to an end for all but the largest datasets."become very debatable. Depending on how you want to pivot&#x2F; scale&#x2F;augment your data, even datasets that seemingly "fit" on large boxes will quickly OOM you.The author also has another article where they claim that:"SQL should be the first option considered for new data engineering work. It’s robust, fast, future-proof and testable. With a bit of care, it’s clear and readable." (over polars&#x2F;pandas etc)This does not map to my experience at all, outside of the realm of nicely parsed datasets that don't require too much complicated analysis or augmentation.

**mrtimo:**
What I love about duckdb:-- Support for .parquet, .json, .csv (note: Spotify listening history comes in a multiple .json files, something fun to play with).-- Support for glob reading, like: select * from 'tsa20*.csv' - so you can read hundreds of files (any type of file!) as if they were one file.-- if the files don't have the same schema, union_by_name is amazing.-- The .csv parser is amazing. Auto assigns types well.-- It's small! The Web Assembly version is 2mb! The CLI is 16mb.-- Because it is small you can add duckdb directly to your product, like Malloy has done: https:&#x2F;&#x2F;www.malloydata.dev&#x2F; - I think of Malloy as a technical persons alternative to PowerBI and Tableau, but it uses a semantic model that helps AI write amazing queries on your data. Edit: Malloy makes SQL 10x easier to write because of its semantic nature. Malloy transpiles to SQL, like Typescript transpiles to Javascript.

**majkinetor:**
Anybody with experience in using duckdb to quickly select page of filtered transactions from the single table having a couple of billions of records and let's say 30 columns where each can be filtered using simple WHERE clausule? Lets say 10 years of payment order data. I am wondering since this is not analytical scenario.Doing that in postgres takes some time, and even simple count(*) takes a lot of time (with all columns indexed)
