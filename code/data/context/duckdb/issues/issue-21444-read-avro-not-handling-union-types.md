# read_avro not handling union types

**Issue #21444** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** mixedveges
**Labels:** needs triage

### What happens?

`read_avro` appears to misread union types at `VECTOR_SIZE` multiple row indices
```
{
  "type": "record",
  "name": "SSTable",
Show less
  "fields": [
    {
      "type": "long",
      "name": "id"
    },
    {
      "type": [
        "null",
        "string"
      ],
      "name": "value"
    }
]
}
```
In the attached file, it is reading out every `VECTOR_SIZE` multiple row index value field as `NULL` instead of the string.

### To Reproduce

[out.avro.zip](https://github.com/user-attachments/files/26071980/out.avro.zip)

### OS:

mac aarch64

### DuckDB Version:

1.4.4

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Bevan Chan

### Affiliation:

Phocas Software

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @mixedveges, thanks for opening this issue. In DuckDB 1.5, the Avro reader returns the following schema:

```
describe (from read_avro('out.avro'));
```
```
┌───────────────┐
│   Describe    │
│               │
│ id    bigint  │
│ value varchar │
└───────────────┘
```

What would be the expected schema?

**Tishj:**
The schema is not the problem, they're saying if `STANDARD_VECTOR_SIZE` was 2, their output would look like:
```
string
NULL
string
NULL
```
