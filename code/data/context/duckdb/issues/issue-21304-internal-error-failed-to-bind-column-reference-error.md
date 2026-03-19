# INTERNAL Error: Failed to bind column reference error

**Issue #21304** | State: closed | Created: 2026-03-11 | Updated: 2026-03-17
**Author:** gishor
**Labels:** reproduced

### What happens?

In duckdb 1.5.0 (latest on v1.5 branch) we get the error:

```
INTERNAL Error:
Failed to bind column reference "b" [10.1] (bindings: {#[10.0]})
```

I didn't see anybody reporting it yet.

### To Reproduce

query:
```sql
WITH t(a,b) AS (VALUES(1,2))
         SELECT * FROM (SELECT * FROM t UNION ALL SELECT * FROM t), (SELECT a FROM t) r;
```

output:
```
INTERNAL Error:
Failed to bind column reference "b" [10.1] (bindings: {#[10.0]})

Stack Trace:

0        duckdb::Exception::ToJSON(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 420
1        duckdb::Exception::Exception(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 468
2        duckdb::InternalException::InternalException(std::__1::basic_string, std::__1::allocator> const&) + 220
3        duckdb::InternalException::InternalException(std::__1::basic_string, std::__1::allocator> const&) + 84
4        duckdb::InternalException::InternalException, std::__1::allocator> const&, unsigned long long&, unsigned long long&, std::__1::basic_string, std::__1::allocator>>(std::__1::basic_string, std::__1::allocator> const&, std::__1::basic_string, std::__1::allocator> const&, unsigned long long&, unsigned long long&, std::__1::basic_string, std::__1::allocator>&&) + 700
5        duckdb::ColumnBindingResolver::VisitReplace(duckdb::BoundColumnRefExpression&, duckdb::unique_ptr, true>*) + 6976
6        duckdb::LogicalOperatorVisitor::VisitExpression(duckdb::unique_ptr, true>*) + 3840
7        duckdb::LogicalOperatorVisitor::VisitOperatorExpressions(duckdb::LogicalOperator&)::$_0::operator()(duckdb::unique_ptr, true>*) const + 368
8        decltype(std::declval()(std::declval, true>*>())) std::__1::__invoke[abi:ne190102], true>*>(duckdb::LogicalOperatorVisitor::VisitOperatorExpressions(duckdb::LogicalOperator&)::$_0&, duckdb::unique_ptr, true>*&&) + 148
9        void std::__1::__invoke_void_return_wrapper::__call[abi:ne190102], true>*>(duckdb::LogicalOperatorVisitor::VisitOperatorExpressions(duckdb::LogicalOperator&)::$_0&, duckdb::unique_ptr, true>*&&) + 136
10       std::__1::__function::__alloc_func, void (duckdb::unique_ptr, true>*)>::operator()[abi:ne190102](duckdb::unique_ptr, true>*&&) + 240
11       std::__1::__function::__func, void (duckdb::unique_ptr, true>*)>::operator()(duckdb::unique_ptr, true>*&&) + 316
12       std::__1::__function::__value_func, true>*)>::operator()[abi:ne190102](duckdb::unique_ptr, true>*&&) const + 588
13       std::__1::function, true>*)>::operator()(duckdb::unique_ptr, true>*) const + 392
14       duckdb::LogicalOperatorVisitor::EnumerateExpressions(duckdb::LogicalOperator&, std::__1::function, true>*)> const&) + 14892
15       duckdb::LogicalOperatorVisitor::VisitOperatorExpressions(duckdb::LogicalOperator&) + 460
16       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 28620
17       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 1552
18       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 28432
19       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 1552
20       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 28432
21       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 1552
22       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 28432
23       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 1552
24       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 28432
25       duckdb::ColumnBindingResolver::Verify(duckdb::LogicalOperator&) + 712
26       duckdb::Optimizer::Verify(duckdb::LogicalOperator&) + 132
27       duckdb::Optimizer::RunOptimizer(duckdb::OptimizerType, std::__1::function const&) + 932
28       duckdb::Optimizer::RunBuiltInOptimizers() + 3012
29       duckdb::Optimizer::Optimize(duckdb::unique_ptr, true>) + 1604
30       duckdb::ClientContext::CreatePreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters) + 6324
31       duckdb::ClientContext::CreatePreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters, duckdb::PreparedStatementMode) + 5856
32       duckdb::ClientContext::PendingStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&) + 1316
33       duckdb::ClientContext::PendingStatementOrPreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 2852
34       duckdb::ClientContext::PendingStatementOrPreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 6252
35       duckdb::ClientContext::PendingQueryInternal(duckdb::ClientContextLock&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&, bool) + 1076
36       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, std::__1::unordered_map, std::__1::allocator>, duckdb::BoundParameterData, duckdb::CaseInsensitiveStringHashFunction, duckdb::CaseInsensitiveStringEquality, std::__1::allocator, std::__1::allocator> const, duckdb::BoundParameterData>>>&, duckdb::QueryParameters) + 1284
37       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 564
38       duckdb::ClientContext::Query(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 624
39       duckdb::Connection::SendQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 588
40       duckdb_shell::ShellState::ExecuteStatement(duckdb::unique_ptr, true>) + 1860
41       duckdb_shell::ShellState::ExecuteSQL(std::__1::basic_string, std::__1::allocator> const&) + 3628
42       duckdb_shell::ShellState::RunOneSqlLine(duckdb_shell::InputMode, char*) + 836
43       duckdb_shell::ShellState::ProcessInput(duckdb_shell::InputMode) + 6504
44       main + 12536
45       start + 6076

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### OS:

mac arm

### DuckDB Version:

DuckDB v1.6.0-dev84 (Development Version, 8a897b5ef8)

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

Gishor Sivanrupan

### Affiliation:

Exaforce

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
@gishor Thanks for the report, I could reproduce this on the nightly v1.6 build.

**kryonix:**
Thanks! This will be fixed with PR https://github.com/duckdb/duckdb/pull/21275

**gishor:**
Oh nice, thanks for the update 🙌
