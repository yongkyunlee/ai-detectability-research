# floating point exception (core dumped) when reading from table with a list of struct

**Issue #21470** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** maartenbosteels
**Labels:** needs triage

### What happens?

I create a table from a JSON file. When I then do a select from this table I get an floating point exception (core dumped).

The weird thing is: I have two SSH sessions to the same server.
In one session I can reproduce it 100% of the times in the other session 0%.

I compared the env of both sessions and see nothing relevant.
Only diffs are SSH_CONNECTION, SSH_TTY, XDG_SESSION_ID, SSH_CLIENT

### To Reproduce

```
cat > input.json << 'EOF'
{
  "requests": [
    {
      "crawl_started": "2026-03-18 18:16:41.218404",
      "crawl_finished": "2026-03-18 18:16:44.794152",
      "num_of_responses": 0,
      "responses": []
    }
  ],
  "status": null,
  "crawl_started": "2026-03-18 18:16:41.2184",
  "crawl_finished": "2026-03-18 18:16:44.794191",
  "tld": "dk"
}
EOF

cat input.json | jq && duckdb repro.db -c "create or replace table t as from 'output.json'; describe t; from t where tld ='';"
```

### OS:

Ubuntu 22.04.5 LTS, x86_64

### DuckDB Version:

v1.5.0 (Variegata)

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Maarten Bosteels

### Affiliation:

datalabs

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**maartenbosteels:**
```
{
  "requests": [
    {
      "crawl_started": "2026-03-18 18:16:41.218404",
      "crawl_finished": "2026-03-18 18:16:44.794152",
      "num_of_responses": 0,
      "responses": []
    }
  ],
  "status": null,
  "crawl_started": "2026-03-18 18:16:41.2184",
  "crawl_finished": "2026-03-18 18:16:44.794191",
  "tld": "dk"
}
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                           t                                                           │
│                                                                                                                       │
│ requests       struct(crawl_started timestamp, crawl_finished timestamp, num_of_responses bigint, responses json[])[] │
│ status         json                                                                                                   │
│ crawl_started  timestamp                                                                                              │
│ crawl_finished timestamp                                                                                              │
│ tld            varchar                                                                                                │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
Floating point exception (core dumped)
```

**maartenbosteels:**
Possibly same issue as #21429 but I could not reproduce that one.
