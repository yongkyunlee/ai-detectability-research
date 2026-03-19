# Sorting and ART indices should be supported on Big-endian platforms

**Issue #9714** | State: closed | Created: 2023-11-17 | Updated: 2026-03-10
**Author:** barracuda156
**Labels:** under review

### What happens?

Sorting and ART indices are broken in `duckdp` for Big-endian platforms. The codebase has the following:

https://github.com/search?q=repo%3Aduckdb%2Fduckdb+Radix%3A%3AIsLittleEndian%28%29&type=code

P. S. This issue is not specific to any OS. So while I tested it on macOS, it affects any Unix-like OS just as well.

### To Reproduce

The issue was discovered when running tests for `duckplyr` in `R`, but the cause of the problem is `duckdb` itself.

### OS:

macOS / PowerPC

### DuckDB Version:

0.9.1

### DuckDB Client:

R

### Full Name:

Sergey Fedorov

### Affiliation:

Soochow University

### Have you tried this on the latest `main` branch?

I have tested with a main build

### Have you tried the steps to reproduce? Do they include all relevant data and configuration? Does the issue you report still appear there?

- [X] Yes, I have

## Comments

**szarnyasg:**
Hello @barracuda156 unfortunately we do not support big-endian architectures (see our [support policy](https://duckdblabs.com/news/2023/10/02/support-policy.html)). Of course, contributions are welcome.

**szarnyasg:**
Hi @barracuda156, we discussed this internally and concluded that we do not have the capacity to support Big-endian platforms. This is not necessarily a matter of implementation efforts, rather the related infrastructure and testing which would require a substantial effort.

Patches are welcome but we are unable to commit to supporting Big-endian platforms in the long run.

**barracuda156:**
@szarnyasg If it is a matter of running a test-suite (or/and some alternative more specific tests) and submitting results to verify nothing got broken, I could commit to doing that regularly as required.

Perhaps an explicit warning can be displayed to a user that the upstream does not guarantee full support for Big-endian platforms (or even that tickets are not accepted).

(I am replying in a context of discussing the issue, there is no implication that anyone *should* do this.)

**barracuda156:**
@Mytherin @DNikolaevAtRocket Oh, I did not see that PR. Thank you for addressing the issue!

**Mytherin:**
The PR was submitted by @DNikolaevAtRocket - see https://github.com/duckdb/duckdb/pull/19748 - I just merged it
