# Combined count distinct in qualify fail to filter

**Issue #21198** | State: closed | Created: 2026-03-05 | Updated: 2026-03-05
**Author:** memeplex
**Labels:** expected behavior

### What happens?

Combined count distinct conditions in qualify clause fail to apply correctly.

### To Reproduce

```python
rel = duckdb.query("""
select count(distinct price) as uniq
from (
  select * from 'data.csv'
  qualify
    count(distinct price) over (partition by item_id) >= 5
    and count(distinct price) over (partition by product_id) >= 5
)
group by item_id
""")

rel.aggregate("min(uniq)")

=> 4
```

[data.csv](https://github.com/user-attachments/files/25769593/data.csv)

### OS:

Linux cate-cp--fda2-ai-price 5.15.0-1075-aws #82~20.04.1-Ubuntu SMP Thu Dec 19 05:24:09 UTC 2024 x86_64 GNU/Linux

### DuckDB Version:

1.4.4

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Carlos

### Affiliation:

Mutt

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**hawkfish:**
Hi @memeplex thanks for the report! It looks like this is failing in 1.5.

**hawkfish:**
OK I've had a chance to dig into this a bit more and the result is correct. What is confusing is that the windowed `count distinct`s are both computed _before_ the `qualify` predicate is applied. So the intersection of those predicates may reduce the number of distinct prices for the `item_id`s that pass _both_ filters.

The `item_id`s that have `uniq = 5
             and count(distinct price) over (partition by product_id) >= 5
         )
         group by item_id
         having uniq < 5
         order by 1;
```

|  item_id   | uniq |
|-----------:|-----:|
| 610548446  | 4    |
| 611532167  | 4    |
| 2943107170 | 4    |
| 2949514888 | 4    |

If we look at the windowing output for these `item_id`s, we see:

```sql
from (
    select *,
        count(distinct price) over (partition by item_id) as pi,
        count(distinct price) over (partition by product_id) as pp,
    from fnord
)
where item_id in (2943107170, 610548446, 611532167, 2949514888)
order by item_id, price;
```

| column0 |  price   |  item_id   | product_id | pi | pp |
|--------:|---------:|-----------:|-----------:|---:|---:|
| 1370624 | 27776.0  | 610548446  | 18956616   | 5  | 1  |
| 1400537 | 30990.0  | 610548446  | 19123630   | 5  | 8  |
| 2393761 | 32186.0  | 610548446  | 19123630   | 5  | 8  |
| 1405082 | 32190.0  | 610548446  | 19123630   | 5  | 8  |
| 1307264 | 34019.0  | 610548446  | 19123630   | 5  | 8  |
| 1772506 | 73961.0  | 611532167  | 18622254   | 6  | 6  |
| 262080  | 82609.0  | 611532167  | 18622254   | 6  | 6  |
| 878611  | 82627.0  | 611532167  | 17426250   | 6  | 2  |
| 293150  | 82627.0  | 611532167  | 17426250   | 6  | 2  |
| 853605  | 82638.0  | 611532167  | 17426250   | 6  | 2  |
| 1811503 | 84990.0  | 611532167  | 18622254   | 6  | 6  |
| 1868516 | 89990.0  | 611532167  | 18622254   | 6  | 6  |
| 2500081 | 3371.0   | 2943107170 | 21362417   | 5  | 8  |
| 2748680 | 3543.0   | 2943107170 | 21362417   | 5  | 8  |
| 960772  | 3543.0   | 2943107170 | 21362417   | 5  | 8  |
| 1022995 | 3552.0   | 2943107170 | 21362417   | 5  | 8  |
| 1085530 | 4405.0   | 2943107170 | 21362415   | 5  | 1  |
| 2129591 | 4625.0   | 2943107170 | 21362417   | 5  | 8  |
| 1411733 | 80590.0  | 2949514888 | 34706441   | 5  | 5  |
| 2732986 | 89170.0  | 2949514888 | 34706441   | 5  | 5  |
| 2235979 | 101064.0 | 2949514888 | 34706441   | 5  | 5  |
| 1496816 | 101108.0 | 2949514888 | 2949514888 | 5  | 1  |
| 172227  | 119990.0 | 2949514888 | 34706441   | 5  | 5  |

In each `item_no` group, one or more of the rows will be removed by the `qualify` filter, resulting in a total count for that group of `< 5`.
