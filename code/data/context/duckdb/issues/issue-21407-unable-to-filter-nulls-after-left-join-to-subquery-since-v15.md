# Unable to filter NULLs after left join to subquery since v1.5

**Issue #21407** | State: closed | Created: 2026-03-16 | Updated: 2026-03-17
**Author:** glenjamin
**Labels:** reproduced

### What happens?

I'm not sure if there's more of this query that could be stripped away, but this is what I've managed to reduce it to

When left joining a table onto a subquery, in v1.4.4 I'm able to add a WHERE clause which filters out the null rows eg (IS NOT NULL) or (= 'x').

### To Reproduce

Data setup
```sql
create or replace table c(id int, u_id int);
insert into c values (1, 1), (2,2), (3,3), (4, null);

create or replace table t(id int, name text, u_ids int[]);
insert into t values (1, 'one', [1]), (2, 'two', [1, 2]), (3, 'three', null);
```

Query
```sql
select c.id, ts.names
from c LEFT JOIN (
  select array_agg(t.name)
  from t where c.u_id = any(t.u_ids)
) as ts(names) on true
where ts.names IS NOT NULL;
```

Actual result
| id    | names          |
|-------|----------------|
| 1     | ['one', 'two'] |
| 2     | ['two']        |
| 3     | NULL           |
| 4     | NULL           |

Expected result (and the result in v1.4.4)
| id    | names          |
|-------|----------------|
| 1     | ['one', 'two'] |
| 2     | ['two']        |

### OS:

macOS

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Glen Mailer

### Affiliation:

Geckoboard

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@glenjamin thanks for reporting this. This indeed a regression. We'll take a look and fix it in one of the upcoming 1.5.x releases.
