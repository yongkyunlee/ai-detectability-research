# BaseRequest(endpoint, path) constructor is flawed

**Issue #21116** | State: closed | Created: 2026-02-27 | Updated: 2026-03-09
**Author:** myrrc
**Labels:** reproduced

### What happens?

For specific issue see https://github.com/duckdb/duckdb-httpfs/pull/265.

In `http_util.hpp`,

```
BaseRequest::BaseRequest(RequestType type, const string &endpoint_p, const string &path_p, const HTTPHeaders &headers,
	            HTTPParams &params)
	    : type(type), url(path), path(path_p), proto_host_port(endpoint_p), headers(headers), params(params) {
	}
```

constructor is incorrect.
url binds only to path and not to endpoint_p + path_p as it should, thus if someone wants to use url, this may not be correct.

Above is incorrect example of this usage in httpfs's curl backend.

This may be a trivial fix but `url` is a `const string&` thus I'm not sure changing semantics for BaseRequest->url is the best scenario.

### To Reproduce

See above

### OS:

Not applicable

### DuckDB Version:

1.4.3, but reproduces in  main as well

### DuckDB Client:

Not applicable

### Hardware:

_No response_

### Full Name:

Mikhail Kot

### Affiliation:

SpiralDB

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**carlopi:**
Thanks for the report, I do agree, and I am looking to removing this extra constructor entirely in duckdb/duckdb (that will land post v1.5.0).

**carlopi:**
Thanks for raising, since https://github.com/duckdb/duckdb/pull/21151 (now merged in 1.5-variegata), the misleading constructor it's not available anymore.
