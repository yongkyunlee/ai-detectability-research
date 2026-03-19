# Show HN: Snowflake Emulator – Local Snowflake Development with Go and DuckDB

**HN** | Points: 6 | Comments: 4 | Date: 2026-01-03
**Author:** sr-white
**HN URL:** https://news.ycombinator.com/item?id=46471246
**Link:** https://github.com/nnnkkk7/snowflake-emulator

Hi HN! I built a Snowflake emulator for local development and testing.Testing Snowflake code locally is frustrating – you need a real account (expensive) or mock everything (tedious). I wanted something that just works with the standard [gosnowflake](https:&#x2F;&#x2F;github.com&#x2F;snowflakedb&#x2F;gosnowflake) driver or REST API.snowflake-emulator fixes this by:- Using DuckDB as the storage engine
- Auto-translating Snowflake SQL (IFF→IF, NVL→COALESCE, DATEADD, etc.)
- Supporting gosnowflake driver protocol – no code changes needed
- Providing REST API v2 – use from any language (Python, Node.js, etc.)```go
dsn := "user:pass@localhost:8080&#x2F;TEST_DB&#x2F;PUBLIC?account=test&protocol=http"
db, _ := sql.Open("snowflake", dsn)
db.Query(`SELECT IFF(score >= 90, 'A', 'B') FROM users`)
``````bash
docker run -p 8080:8080 ghcr.io&#x2F;nnnkkk7&#x2F;snowflake-emulator:latest
```GitHub: https:&#x2F;&#x2F;github.com&#x2F;nnnkkk7&#x2F;snowflake-emulatorWould love feedback – especially on SQL functions you'd want supported!

## Top Comments

**toggle-me:**
Nice! I'll give it a try!

**dmarwicke:**
how well does the flatten() translation work in practice? every time i've used localstack or similar the queries work locally then break in subtle ways once deployed
