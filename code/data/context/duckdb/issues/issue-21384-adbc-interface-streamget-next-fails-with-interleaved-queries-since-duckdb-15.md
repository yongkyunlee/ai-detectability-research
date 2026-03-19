# ADBC interface: stream.get_next() fails with interleaved queries since DuckDB 1.5

**Issue #21384** | State: open | Created: 2026-03-15 | Updated: 2026-03-16
**Author:** rouault
**Labels:** under review

### What happens?

When using the ADBC interface and doing (StatementExecuteQuery, &stmt, &stream), then  (StatementExecuteQuery, &stmt2, &stream2) and then stream.get_next(&stream, &array), the later fails

### To Reproduce

Given  test_adbc.cpp 
```
#include 
#include 

#define ADBC_CALL(func, ...) driver.func(__VA_ARGS__)

int main()
{
    AdbcDriver driver;
    AdbcError error = ADBC_ERROR_INIT;
    assert(AdbcLoadDriver("duckdb", "duckdb_adbc_init", ADBC_VERSION_1_1_0, &driver,
                              &error) == ADBC_STATUS_OK);
    AdbcDatabase database;
    assert(ADBC_CALL(DatabaseNew, &database, &error) == ADBC_STATUS_OK);

    assert(ADBC_CALL(DatabaseSetOption, &database, "path", ":memory:", &error) == ADBC_STATUS_OK);

    assert(ADBC_CALL(DatabaseInit, &database, &error) == ADBC_STATUS_OK);

    AdbcConnection conn;
    assert(ADBC_CALL(ConnectionNew, &conn, &error) == ADBC_STATUS_OK);

    assert(ADBC_CALL(ConnectionInit, &conn, &database, &error) == ADBC_STATUS_OK);

    {
        AdbcStatement stmt;
        assert(ADBC_CALL(StatementNew, &conn, &stmt, &error) == ADBC_STATUS_OK);

        assert(ADBC_CALL(StatementSetSqlQuery, &stmt, "SELECT 1", &error) == ADBC_STATUS_OK);

        struct ArrowArrayStream stream;
        int64_t rows_affected = -1;
        assert(ADBC_CALL(StatementExecuteQuery, &stmt, &stream, &rows_affected, &error) == ADBC_STATUS_OK);

        {
            AdbcStatement stmt2;
            assert(ADBC_CALL(StatementNew, &conn, &stmt2, &error) == ADBC_STATUS_OK);

            assert(ADBC_CALL(StatementSetSqlQuery, &stmt2, "SELECT 2", &error) == ADBC_STATUS_OK);

            struct ArrowArrayStream stream2;
            assert(ADBC_CALL(StatementExecuteQuery, &stmt, &stream2, &rows_affected, &error) == ADBC_STATUS_OK);
        }

        struct ArrowArray array;

        // Crashes HERE with libduckdb 1.5
        assert(stream.get_next(&stream, &array) == 0);

        if (array.release)
            array.release(&array);
        stream.release(&stream);

        assert(ADBC_CALL(StatementRelease, &stmt, &error) == ADBC_STATUS_OK);
    }

    return 0;
}
```

```
$ g++ -g test_adbc.cpp -I/home/even/miniconda3/envs/adbc/include -L/home/even/miniconda3/envs/adbc/lib -ladbc_driver_manager -o mytest && ./mytest 
mytest: test_adbc.cpp:46: int main(): Assertion `stream.get_next(&stream, &array) == 0' failed.
Abandon (core dumped)
```

This works with DuckDB 1.4.4. I've bisected this failure to commit eb859e74a0b3555dcbfc7382c18f3fab9f0abe10 (CC @eitsupi)

### OS:

Ubuntu 24.04

### DuckDB Version:

1.5.0

### DuckDB Client:

C

### Hardware:

_No response_

### Full Name:

Even Rouault

### Affiliation:

Spatialys

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**eitsupi:**
My understanding is that this is not a bug but follows the ADBC specification.
Note that in the reproducer, the second `StatementExecuteQuery` uses `stmt` (not `stmt2`), so this is a case of re-executing the same statement while a prior result set is still active.

The ADBC spec explicitly states that this must invalidate prior result sets:
https://github.com/apache/arrow-adbc/blob/da58c591ed89b29c9096e4ebc0fe99d369e2bc88/c/include/arrow-adbc/adbc.h#L2001-L2019

The concurrency documentation also discusses this exact scenario:
https://github.com/apache/arrow-adbc/blob/da58c591ed89b29c9096e4ebc0fe99d369e2bc88/docs/source/cpp/concurrency.rst

In DuckDB 1.4, `duckdb_execute_prepared` (non-streaming) was used, so results were materialized in memory and happened to remain valid.
In 1.5, `duckdb_execute_prepared_streaming` is used, and the prior stream is properly invalidated per the spec.
The `get_next()` call returns a non-zero error code.

@lidavidm
Any thoughts?

**rouault:**
> Note that in the reproducer, the second `StatementExecuteQuery` uses `stmt` (not `stmt2`), so this is a case of re-executing the same statement while a prior result set is still active.

ok, that was a typo of my various back&forth putting together the reproducer. Even when changing the second StatementExecuteQuery to use stmt2, I get the issue. But I understand this is indeed the scenario of concurrency.rst...

**lidavidm:**
A crash is not ideal (though it seems it's not a crash per se, just an error result?), but yes, a driver doesn't _necessarily_ support concurrent statements. I agree that it would be useful, and it feels like it should be possible for DuckDB, but I'm not familiar enough with the internals.

**rouault:**
> A crash is not ideal (though it seems it's not a crash per se, just an error result?)

it's not a crash indeed. The assert() in the reproducer are just to illustrate the point of failure

**eitsupi:**
I'll take a look at if it can be able to support multiple executions.
