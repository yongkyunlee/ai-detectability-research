# DuckDB doesn't preserve UTC offset when adding a day to timestamptz column

**Issue #20845** | State: open | Created: 2026-02-06 | Updated: 2026-03-15
**Author:** MarcoGorelli
**Labels:** Needs Documentation, expected behavior

### What happens?

If I start with `'2025-03-29 02:30:00+01'` in `'Europe/Amsterdam'` and try to add one calendar day, I would end up on `'2025-03-30 02:30:00+01'`

However, due to DST, `'2025-03-30 02:30:00+01'` does not exist in time zone `'Europe/Amsterdam'`

DuckDB shifts the result forwards to `'2025-03-30 03:30:00+02'`

I was looking at the [whenever](https://whenever.readthedocs.io/en/latest/overview.html#ambiguity-in-timezones) library, which claims to follow RFC-5545, and here it preserves the UTC offset of the original datetime. In this case, they shift forwards to `'2025-03-30 01:30:00+01'`

Looking at https://duckdb.org/docs/stable/sql/functions/timestamptz#icu-timestamp-with-time-zone-operators, I don't see any mention of what rule exactly DuckDB follows.

I'd like to suggest one of the following:
- DuckDB follows RFC-5545
- Or, DuckDB explicitly documents what it does

### To Reproduce

Here's the sql to reproduce:

```sql
SET timezone = 'Europe/Amsterdam';
select a,
       a + '1 day'::INTERVAL as c,
from values (CAST('2025-3-29 02:30' AS TIMESTAMPTZ),)  df(a)
```

```
┌──────────────────────────┬──────────────────────────┐
│            a             │            c             │
│ timestamp with time zone │ timestamp with time zone │
├──────────────────────────┼──────────────────────────┤
│ 2025-03-29 02:30:00+01   │ 2025-03-30 03:30:00+02   │
└──────────────────────────┴──────────────────────────┘
```

### OS:

x86_64

### DuckDB Version:

1.4.4

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Marco Edward Gorelli

### Affiliation:

Quansight Labs

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**hawkfish:**
Hi @MarcoGorelli  -

We use [ICU](https://unicode-org.github.io/icu/userguide/datetime/) for our temporal operations and our behaviour matches Postgres:

```sql
hawkfish=# set timezone='Europe/Amsterdam';
SET
hawkfish=# create temporary table df(a TIMESTAMPTZ);
CREATE TABLE
hawkfish=# insert into df values('2025-3-29 02:30');
INSERT 0 1
hawkfish=# select a, a + '1 day'::interval as c from df;
           a            |           c            
------------------------+------------------------
 2025-03-29 02:30:00+01 | 2025-03-30 03:30:00+02
```

The offset that is displayed is determined by the current time zone setting (this is part of the SQL standard). But your concern appears to be that ICU day field arithmetic on DST boundaries is not "compatible"? In particular that adding 1 day is the same as adding 24 hours?

**hawkfish:**
After looking at your bio, I see that you work on the Polars time code? We are committed to Postgres compatibility, so this behaviour is not going to change (especially since it has been in place for about 5 years now!) but you can always create an extension similar to our ICU that uses the whenever code base.

**MarcoGorelli:**
thanks for your reply!

I find it absolutely expected that adding one day is not necessarily the same as adding 24 hours 👍 For example, `'2025-03-29 05:30:00+01'` plus 1 day equals `'2025-03-30 05:30:00+02'`, which is 23 hours, and I find that completely expected ✅ 

My question is solely about what happens when the result is on an ambiguous or a non-existent datetime. In this example, the "add 1 calendar day" result is `'2025-03-30 02:30:00+02'`, which is non-existent due to a DST transition. It seems like different tools do different things:
- `whenever` / RFC-5545: preserves the UTC offset, i.e. here it would go to `'2025-03-30 01:30:00+01'`
- Polars currently raises (you need to specify `ambiguous='earliest'` / `ambiguous='latest'`, in places where that keyword is present)
- It looks like DuckDB always rounds up to the next valid datetime, i.e. here `'2025-03-30 03:30:00+02'`

>  We are committed to Postgres compatibility, so this behaviour is not going to change (especially since it has been in place for about 5 years now!)

Absolutely fine to not change behaviour 🙏 In which case, formalising / documenting the actual behaviour in the timezones page might be useful to users?

**hawkfish:**
Thanks for bringing it up - I've tagged it with a documentation request.

**rohitmannur007:**
Hi @hawkfish ,

I’d like to help with the documentation update related to DST behavior when adding intervals to `TIMESTAMPTZ`.

My plan is to add a section explaining how DuckDB handles non-existent timestamps during DST transitions (for example when adding `INTERVAL '1 day'` across DST boundaries), and clarify that the behavior follows PostgreSQL and moves to the next valid timestamp.

Please let me know if this should be added under the `timestamptz` functions documentation or the timezone documentation page.

Happy to submit a PR once I confirm the correct location.

**hawkfish:**
Hi @rohitmannur007 - Thanks for the offer! I think the best place is to put it in with [the explanation of temporal binning](https://duckdb.org/docs/stable/sql/data_types/timestamp#time-zone-support).

But please don't refer to "non-existent timestamps" - there is no such thing! What you are seeing is how ICU handles interval arithmetic on _temporal bin sets_. In the original example, adding a day to `2025-03-29 02:30:00+02` produces the instant `2025-03-29 02:30:00+02` (using offset notation). This is a valid instant, but the bin set from this offset notation (ymdHMSo) does not exist in the current time zone. The options for the bin arithmetic are then either to choose a valid bin representation of the instant (which is what ICU does in both DuckDB and Postgres) or to choose one of the boundary instants around the missing bin interval. ICU chooses to maintain the instant in this situation (i.e., `latest` in Polars).

For the other transition, adding 1 day to `2025-10-25 03:30:00+02` produces the instant `2025-10-26 03:30:00+02`, but again this bin set does not exist in the current time zone. The valid bin set for this instant is `2025-10-26 04:30:00+01`, but this case, ICU chooses to maintain the hour bin and maps to the bin set for the instant `2025-10-26 03:30:00+01` (i.e., `earliest` in Polars).

**rohitmannur007:**
Hi @hawkfish 
Thanks for the clarification! That makes sense — I’ll update the section to describe this in terms of temporal binning and remove the reference to “non-existent timestamps.” I’ll adjust the wording to explain that the instant exists but the local bin representation may not, and document how ICU resolves the mapping during DST transitions
