# Cannot SELECT FROM JSON column with multiple WHERE clauses

**Issue #20366** | State: open | Created: 2026-01-02 | Updated: 2026-03-11
**Author:** bardware
**Labels:** reproduced

### What happens?

I store complex data in a column of type JSON. One member is an array and I want to SELECT the lines from the table  where one element of the array matches multiple criteria.
I get an error when the WHERE clause is written in a certain order.
The database tries to cast the whole JSON to numeric and I don't understand why.

### To Reproduce

I create a database with one table and insert data:

```sql
CREATE TABLE data (
    data_id INTEGER NOT NULL,
    data_json JSON using compression 'zstd',                
    PRIMARY KEY(data_id)
);
INSERT INTO data (data_id, data_json)
VALUES
    (1, '{"data": [{"id":0,"type":"type1","val":"305.123"},{"id":1,"type":"type2","val":"39.35"}]}'),
    (2, '{"data": [{"id":0,"type":"type1","val":"223.752"},{"id":1,"type":"type2","val":"160.875"}]}');
```

Then I query the data

```sql
SELECT	je.value->>'type' ct, cast(je.value->>'val' AS double ) duration,
		d.data_id
FROM	data d,  json_each(d.data_json, 'data') je
WHERE	cast(je.value->>'val' AS double ) > 300
AND		je.value->>'type' = 'type1';
```

This results in the error

```console
SQL Error: Conversion Error: Failed to cast value to numerical: {"id":0,"type":"type1","val":"223.752"} when casting from source column value

LINE 5: AND		je.value->>'type' = 'type1'
           ^
```

Now comes the fun part: I swap the WHERE clauses

```sql
SELECT	je.value->>'type' ct, cast(je.value->>'val' AS double ) duration,
		d.data_id
FROM	data d,  json_each(d.data_json, 'data') je
WHERE	je.value->>'type' = 'type1'
AND		cast(je.value->>'val' AS double ) > 300;
```

This results in the correct output I expected.

### OS:

Windows

### DuckDB Version:

1.4.3

### DuckDB Client:

DBeaver/JDBC

### Hardware:

_No response_

### Full Name:

Bernhard Döbler

### Affiliation:

private

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Pranav2612000:**
I'm able to reproduce this issue. I'll like to give this a try

**Pranav2612000:**
The reason this query fails is because the brackets are not applied correctly, this is how we try to bind the expression
`(((CAST((je."value" ->> 'val') AS DOUBLE) > 300) AND je."value") ->> 'type')`

This query works with the brackets explicitly added
```
SELECT    je.value->>'type' ct, cast(je.value->>'val' AS double ) duration,
                 d.data_id
         FROM    data d,  json_each(d.data_json, 'data') je
         WHERE    cast(je.value->>'val' AS double ) > 300
       ‣ AND        (je.value->>'type' = 'type1');
```

Is this the expected behaviour? Or should the `->>` have a higher precedence than `AND` ?

**bardware:**
> should the `->>` have a higher precedence than `AND`

That's my opinion. Who can answer this?
