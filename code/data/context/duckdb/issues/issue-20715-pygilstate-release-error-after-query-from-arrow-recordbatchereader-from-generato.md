# PyGILState_Release error after query from Arrow RecordBatcheReader from generator

**Issue #20715** | State: open | Created: 2026-01-28 | Updated: 2026-03-12
**Author:** Jerry-GK
**Labels:** reproduced

### What happens?

I'm trying to query from arrow RecordBatchReader, following https://duckdb.org/docs/stable/guides/python/sql_on_arrow#apache-arrow-recordbatchreaders
I' trying to query from arrow which is dynamically generated in batch to avoid OOM.

But when the program exits, I encountered:

Fatal python error: PyGILState_Release thread ... must be current when releasing.
Python runtime state: finalizing (tstate = ...)

Thread ... (most recent call first)

Aborted

### To Reproduce

```python
import duckdb
import pandas as pd
import numpy as np
import pyarrow as pa

batch_num = 1000
batch_size = 100000

def my_batch_generator(n):
    for i in range(n):
        print(f"Generate batch {i}...")
        df = pd.DataFrame({
            'id': range(0, batch_size),
            'value': np.random.rand(batch_size),
        } )
        schema = pa.Schema.from_pandas(df)
        yield pa.RecordBatch.from_pandas(df, schema=schema)

def get_arrow_reader_from_df(n):
    sample_df = pd.DataFrame({'id': [0], 'value': [0.0]})
    schema = pa.Schema.from_pandas(sample_df)
    return pa.RecordBatchReader.from_batches(schema, my_batch_generator(n))

if __name__ =="__main__":
    data_stream = get_arrow_reader_from_df(n=batch_num)
    res_df = duckdb.sql("""
    SELECT
    id,
    value
    FROM data_stream
    LIMIT 10
    """).df()
    print(res_df)
```

Note:
1. Error does not occur if no `LIMIT 10`
2. Error does not occur if sleep(1) before exit the program.
3. Some batches(but not all remaining batches)  are still yielding after the query is done (the result set from loaded batches has reached the query LIMIT rows number).

So I guess it's because DuckDB tries to access/release the GIL lock after the python program exits. But I'm not sure it's a bug of DuckDB or my misuse.

### OS:

linux x86_64

### DuckDB Version:

1.4.3

### DuckDB Client:

Python (python3.9)

### Hardware:

_No response_

### Full Name:

Jerry G

### Affiliation:

Zhejiang University

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
This produced a hang for me, so I could reproduce a different problem... but still a problem! Forwarding it to the team.

**Jerry-GK:**
> This produced a hang for me, so I could reproduce a different problem... but still a problem! Forwarding it to the team.

Does the team have any leads on this problem?

**zhongchun:**
I've also encountered this problem. Could the community please resolve it as soon as possible?

**evertlammerts:**
This seems to happen because pyarrow's `Scanner` uses a threadpool to prefetch batches (which makes sense, especially for remote datasets), **and** the scanner wraps a Python generator. When the ArrowArrayStreamWrapper is destroyed and the C stream released, the threads are still alive in pyarrow's threadpool. They only get cleaned up when the interpreter shuts down. Since they wrap Python objects they need the GIL to do so. This is where things seem to go wrong.

This is an MRE that uses pyarrow alone:
```py
import pyarrow as pa
import pyarrow.dataset as ds

schema = pa.schema([("x", pa.int64())])

def gen():
    for i in range(1000):
        yield pa.record_batch(
            [pa.array(range(i * 100_000, (i + 1) * 100_000))],
            schema=schema,
        )

reader = pa.RecordBatchReader.from_batches(schema, gen())
scanner = ds.Scanner.from_batches(reader, use_threads=True)
output_reader = scanner.to_reader()

batch = output_reader.read_next_batch()
print(f"Read {batch.num_rows} rows, exiting...")
# hangs on exit
```

Note that this also hangs with `ds.Scanner.from_batches(reader, use_threads=False)`. `to_reader()` also creates a thread, which does not get cleaned up correctly if not every batch was read. DuckDB seems to clean it up correctly, without hanging, which is interesting in itself.

Some ideas to explore...
* One way to work around this is by disabling the prefetch threads (ds.scanner.). It would be nice if we can do that only if they are backed by Python (and not when they are e.g. reading remote parquet files).
* If we can find a way to allow pyarrow to acquire the GIL when we clean up the c stream, then pyarrow should be able to correctly shut down the threads. This might be hard to control though, since duckdb does this internally and it's not clear to me how we can ensure this is done without the GIL being held some other place.

**zhongchun:**
> This seems to happen because pyarrow's `Scanner` uses a threadpool to prefetch batches (which makes sense, especially for remote datasets), **and** the scanner wraps a Python generator. When the ArrowArrayStreamWrapper is destroyed and the C stream released, the threads are still alive in pyarrow's threadpool. They only get cleaned up when the interpreter shuts down. Since they wrap Python objects they need the GIL to do so. This is where things seem to go wrong.
> 
> This is an MRE that uses pyarrow alone:
> 
> import pyarrow as pa
> import pyarrow.dataset as ds
> 
> schema = pa.schema([("x", pa.int64())])
> 
> def gen():
>     for i in range(1000):
>         yield pa.record_batch(
>             [pa.array(range(i * 100_000, (i + 1) * 100_000))],
>             schema=schema,
>         )
> 
> reader = pa.RecordBatchReader.from_batches(schema, gen())
> scanner = ds.Scanner.from_batches(reader, use_threads=True)
> output_reader = scanner.to_reader()
> 
> batch = output_reader.read_next_batch()
> print(f"Read {batch.num_rows} rows, exiting...")
> # hangs on exit
> Note that this also hangs with `ds.Scanner.from_batches(reader, use_threads=False)`. `to_reader()` also creates a thread, which does not get cleaned up correctly if not every batch was read. DuckDB seems to clean it up correctly, without hanging, which is interesting in itself.
> 
> Some ideas to explore...
> 
> * One way to work around this is by disabling the prefetch threads (ds.scanner.). It would be nice if we can do that only if they are backed by Python (and not when they are e.g. reading remote parquet files).
> * If we can find a way to allow pyarrow to acquire the GIL when we clean up the c stream, then pyarrow should be able to correctly shut down the threads. This might be hard to control though, since duckdb does this internally and it's not clear to me how we can ensure this is done without the GIL being held some other place.

Thanks for your replay, it has been resolved as you suggested.
