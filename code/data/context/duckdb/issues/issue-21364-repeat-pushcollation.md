# Repeat PushCollation

**Issue #21364** | State: closed | Created: 2026-03-13 | Updated: 2026-03-17
**Author:** wanghao19920907
**Labels:** reproduced

### What happens?

For SQL with a specified collate, for example: 
```sql
create table test (a varchar);
insert into test values ('a');
insert into test values ('A');
select * from test order by a collate nocase;
```
When executing BindModifiers, the first **PushCollation** is performed. Then, as the Pipeline starts executing and reaches create_sort_key, **PushCollation** is executed again in CreateSortKeyBind. This results in repeated data conversion, which significantly impacts performance. Moreover, the second PushCollation is not handled by statistics propagation, causing functions that should have used ASCII to incorrectly use Unicode instead. This further degrades performance.This does not affect the results, so it may have gone unnoticed.

In the above example, CaseConvertFunction`` has been executed twice.

First  in Binder::BindModifiers
```c++
for (auto &order_node : order.orders) {
	auto &expr = order_node.expression;
	ExpressionBinder::PushCollation(context, order_node.expression, expr->return_type);
}
```
Second in CreateSortKeyBind
```c++
// push collations
for (idx_t i = 0; i return_type);
}
```
### OS:

any

### DuckDB Version:

v1.4-andium

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

wanghao

### Affiliation:

none

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**wanghao19920907:**
When using the ICU extension, the same issue occurs, and the performance impact is even more severe.

**Mytherin:**
Thanks for the investigation! I've pushed a fix in https://github.com/duckdb/duckdb/pull/21412
