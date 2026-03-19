# [regression] INTERNAL Error: invalid code point detected in Utf8Proc::UTF8ToCodepoint, likely due to invalid UTF-8

**Issue #21061** | State: closed | Created: 2026-02-24 | Updated: 2026-03-02
**Author:** gijshendriksen
**Labels:** under review

### What happens?

For some of our Parquet data, DuckDB (built from `main`) recently started producing internal errors, claiming the data may be invalid UTF-8:
```
INTERNAL Error: invalid code point detected in Utf8Proc::UTF8ToCodepoint, likely due to invalid UTF-8
```
However, DuckDB 1.4.4 can handle the data without a problem.

The data in question is created from Spark, with Parquet V2 encodings and ZSTD compression.

### To Reproduce

I unfortunately couldn't reproduce the issue in a standalone example, but the data for which this happens is in a public S3 instance. The error can be reproduced with the following queries:
```
CREATE SECRET (
    TYPE s3,
    ENDPOINT 'a3s.fi',
    URL_STYLE 'path',
    SCOPE 's3://2006391-owi-remote-index'
);

SELECT docid, url
FROM 's3://2006391-owi-remote-index/year=2026/month=2/day=1/collection=b0ea55f4-01fd-11f1-89ba-02a47ca5d9fd/documents/language=nld/metadata_0.parquet'
WHERE docid=451995;
```

In DuckDB 1.4.4, this correctly produces:
```
┌────────┬─────────────────────────────────────────────┐
│ docid  │                     url                     │
│ int32  │                   varchar                   │
├────────┼─────────────────────────────────────────────┤
│ 451995 │ https://nl.wikipedia.org/wiki/Orthorombisch │
└────────┴─────────────────────────────────────────────┘
```
On `main`, this throws the following error:
```
INTERNAL Error: invalid code point detected in Utf8Proc::UTF8ToCodepoint, likely due to invalid UTF-8
```

### OS:

Linux x86_64

### DuckDB Version:

v1.5.0-dev8048 (491c2a84fd)

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Gijs Hendriksen

### Affiliation:

Radboud University

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**arjenpdevries:**
Maybe one more bit of information to help debug the problem:

```
ows_remote_index D SELECT docid, url
                   FROM 's3://2006391-owi-remote-index/year=2026/month=2/day=1/collection=b0ea55f4-01fd-11f1-89ba-02a47ca5d9fd/documents/language=nld/metadata_0.parquet'
                   WHERE docid<10243 and not(starts_with(url, 'http'))
                   ORDER BY docid ASC
                   LIMIT 10;
┌───────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ docid │                                                      url                                                       │
│ int32 │                                                    varchar                                                     │
├───────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 10240 │ y-gate/accept-tcf2?redirectUri%3D%252Farnhem%252Fvertrekkend-wethouder-heeft-nieuwe-baan-mulder-gaat-strijd-aa │
│ 10241 │ t-kansenongelijkheid-in-onderwijs~a6e06a13%252F                                                                │
│ 10242 │ oggedIn=falseU\0\0\0https://vanberkelbeelden.pictures/beeldhouwers/j-r                                         │
└───────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

However, ...

```
SELECT docid, url FROM 's3://2006391-owi-remote-index/year=2026/month=2/day=1/collection=b0ea55f4-01fd-11f1-89ba-02a47ca5d9fd/documents/language=nld/metadata_0.parquet'WHERE docid=10243;
```

gives the INTERNAL ERROR again.

So I suspect that string processing goes wrong somewhere in a block of data, because every string in the table __should__ start with `http`, and a location where to look is the block that has the records 10240-10242.

**arjenpdevries:**
Ah, and attached a little parquet file that illustrates the problem, created from the above using
```
copy (SELECT docid, url FROM 's3://2006391-owi-remote-index/year=2026/month=2/day=1/collection=b0ea55f4-01fd-11f1-89ba-02a47ca5d9fd/documents/language=nld/metadata_0.parquet'WHERE docid>10230 and docid < 10243) TO 't.parquet';
```

You can download it here: [`t.parquet`](https://www.cs.ru.nl/~arjen/tmp/t.parquet).

For completeness, I also created the file for one more entry in the table. You can download it here: [`t-fails.parquet`](https://www.cs.ru.nl/~arjen/tmp/t-fails.parquet).

This triggers the error when doing `select * from 't-fails.parquet'`.

The interesting and puzzling thing is that while duckdb 1.4.4. can read the original data correctly, the written parquet files I collected here for debugging do cause the same errors when read from disk as a table. However, when I create the same parquet file from the S3 source, this works correctly in duckdb 1.4.4, and the parquet file written can be read correctly in duckdb v1.5-variegata.

So... I assume that the byte sequence read from the pqt on s3 in 1.5 must differ from what 1.4.4 reads.

**arjenpdevries:**
Here a more concise version to share what I learned from the [previous comment](https://github.com/duckdb/duckdb/issues/21061#issuecomment-3967551234), just in case, and to take the S3 parameter out the equation. Unfortunately, still not completely reproducible on a small example, but with one downloaded parquet file, you can reproduce the bug with only DuckDB itself.

Download the [parquet file](https://www.cs.ru.nl/~arjen/metadata_0.parquet).

Try the following query in `duckdb 1.4.4` and in a fresh compiled `duckdb v1.5-variegata`:

```
select url from metadata_0.parquet where docid = 10243;
```

The error message:

```
INTERNAL Error: invalid code point detected in Utf8Proc::UTF8ToCodepoint, likely due to invalid UTF-8
```

If you write the query result to parquet in one of the duckdb versions and read it in the other, you always get the error/no error depending on which one writes out the parquet file. If I make a small parquet file with just that record, both duckdb clients report the error. So the problem is only reproducible with the large parquet file I shared above. 

My hypothesis is that the handling of strings when reading from parquet files in v1.5 must have introduced the regression.
Hope this helps!

**ccfelius:**
@arjenpdevries thanks for all the comments! I saw it a bit too late, but I (think) I have the fix for this here: https://github.com/duckdb/duckdb/pull/21110

**arjenpdevries:**
I can confirm that this is fixed by @ccfelius in https://github.com/duckdb/duckdb/pull/21110 🚀 🐎
