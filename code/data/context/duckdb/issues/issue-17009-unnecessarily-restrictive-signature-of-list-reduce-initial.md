# Unnecessarily restrictive signature of `list_reduce(..., initial)`

**Issue #17009** | State: closed | Created: 2025-04-06 | Updated: 2026-03-09
**Author:** soerenwolfers
**Labels:** reproduced

### What happens?

The new `list_reduce(..., initial)` has the signature

```
list_reduce(seq: T[], fun: (T, T) -> T, initial: T)
``` 
instead of the "correct" signature  
```
list_reduce(seq: T[], fun: (S, T) -> S, initial: S)
```
which means it can't do anything that couldn't already be done with 

```
list_reduce([initial] + seq, fun)
```
(the latter even has the advantage that you don't need to guess whether `fun` or `initial` come first).

In particular, the most simple fold, the identity on lists, isn't possible with the current signature constraint:

```sql
select list_reduce([1], (x, y) -> x || [y], [])
``` 
```
Binder Error: Cannot concatenate types INTEGER and INTEGER[] - an explicit cast is required
```

and the unnecessarily inserted casts to enforce an all-Ts-signature produce "obviously wrong" results:

```sql
select
    y1: list_reduce([0], (x, y) -> if(len(x::VARCHAR) - 1, true, false), false), -- should be `true`, is `0`
    y2: list_reduce([2], (x, y) -> ['3.1', '1.4'][y], 1) -- should be `1.4` is `1`
```
```
┌───────┬───────┐
│  y1   │  y2   │
│ int32 │ int32 │
├───────┼───────┤
│     0 │     1 │
└───────┴───────┘
```

Given that the new `list_reduce(..., initial)` is logically just a rewrite of `list_reduce([initial] || ...)` it is not surprising that the latter produces the same results. That's just another reason that the `initial` version _shouldn't_ just be a rewrite though: In the rewritten form you can at least understand what's going on because `[initial] || seq` must obviously be assigned _some_ type and it is excusable that the type inference for that choice doesn't consider the lambda function. With an explicit `initial` argument, on the other hand, one would intuitively expect that the types of `initial` and `seq` need not be in any relation and thus be surprised from resulting errors (or, worse, wrong results). In fact, I believe  

```sql
list_reduce(, , )
```
should have the same type as the "super type" for `` and 
```
([0], )
```

If implementing that isn't as easy as I imagine, I'd argue that one should simply take the type of `` as given, and throw if `([0], )` isn't implicit-castable to that.

In summary, I think the danger of users getting wrong results without noticing (or spending time figuring out what's happening when they do notice) currently outweights the benefit of the 2 characters saved from the new synax in cases where the two-argument function was already sufficient.

Finally, I assume that the unnecessary casts play part in the internal error reported at https://github.com/duckdb/duckdb/issues/17008

### To Reproduce

.

### OS:

Linux

### DuckDB Version:

'1.3.0-dev1976'

### DuckDB Client:

Python

### Hardware:

.

### Full Name:

Soeren Wolfers

### Affiliation:

G-Research

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a nightly build

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have
