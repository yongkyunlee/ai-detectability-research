# INTERNAL Error: Failed to bind column reference (inequal types)

**Issue #21372** | State: closed | Created: 2026-03-13 | Updated: 2026-03-17
**Author:** krlmlr
**Labels:** reproduced

### What happens?

Internal error similar to #21340, different query.

### To Reproduce

```sh
( cat , std::__1::allocator> const&) + 48
1        duckdb::Exception::Exception(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 36
2        duckdb::InternalException::InternalException(std::__1::basic_string, std::__1::allocator> const&) + 20
3        duckdb::InternalException::InternalException, std::__1::allocator> const&, unsigned long long&, unsigned long long&, std::__1::basic_string, std::__1::allocator>, std::__1::basic_string, std::__1::allocator>>(std::__1::basic_string, std::__1::allocator> const&, std::__1::basic_string, std::__1::allocator> const&, unsigned long long&, unsigned long long&, std::__1::basic_string, std::__1::allocator>&&, std::__1::basic_string, std::__1::allocator>&&) + 64
4        duckdb::ColumnBindingResolver::VisitReplace(duckdb::BoundColumnRefExpression&, duckdb::unique_ptr, true>*) + 612
5        duckdb::LogicalOperatorVisitor::VisitExpression(duckdb::unique_ptr, true>*) + 476
6        duckdb::LogicalOperatorVisitor::EnumerateExpressions(duckdb::LogicalOperator&, std::__1::function, true>*)> const&) + 940
7        duckdb::LogicalOperatorVisitor::VisitOperatorExpressions(duckdb::LogicalOperator&) + 68
8        duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 1680
9        duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 996
10       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 108
11       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 1668
12       duckdb::LogicalOperatorVisitor::VisitOperatorChildren(duckdb::LogicalOperator&) + 108
13       duckdb::ColumnBindingResolver::VisitOperator(duckdb::LogicalOperator&) + 1668
14       duckdb::PhysicalPlanGenerator::ResolveAndPlan(duckdb::unique_ptr, true>) + 128
15       duckdb::PhysicalPlanGenerator::Plan(duckdb::unique_ptr, true>) + 48
16       duckdb::ClientContext::CreatePreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters) + 1084
17       duckdb::ClientContext::CreatePreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters, duckdb::PreparedStatementMode) + 492
18       duckdb::ClientContext::PendingStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&) + 128
19       duckdb::ClientContext::PendingStatementOrPreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 216
20       duckdb::ClientContext::PendingStatementOrPreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 1324
21       duckdb::ClientContext::PendingQueryInternal(duckdb::ClientContextLock&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&, bool) + 148
22       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, std::__1::unordered_map, std::__1::allocator>, duckdb::BoundParameterData, duckdb::CaseInsensitiveStringHashFunction, duckdb::CaseInsensitiveStringEquality, std::__1::allocator, std::__1::allocator> const, duckdb::BoundParameterData>>>&, duckdb::QueryParameters) + 192
23       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 64
24       duckdb::ClientContext::Query(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 56
25       duckdb::Connection::SendQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 64
26       duckdb_shell::ShellState::ExecuteStatement(duckdb::unique_ptr, true>) + 180
27       duckdb_shell::ShellState::ExecuteSQL(std::__1::basic_string, std::__1::allocator> const&) + 384
28       duckdb_shell::ShellState::RunOneSqlLine(duckdb_shell::InputMode, char*) + 92
29       duckdb_shell::ShellState::ProcessInput(duckdb_shell::InputMode) + 1024
30       main + 1912
31       start + 7184

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### OS:

macOS

### DuckDB Version:

v1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Kirill Müller

### Affiliation:

cynkra GmbH

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**feichai0017:**
I wanna take this

**tlinhart:**
Duplicate of https://github.com/duckdb/duckdb/issues/21340?

**krlmlr:**
Maybe yes, maybe no.
