# Excessive memory consumption when using Appender API in C#

**Issue #21142** | State: open | Created: 2026-03-02 | Updated: 2026-03-13
**Author:** varunrains
**Labels:** under review

### What happens?

Hi Team,

We are using Duck DB for storing some FHIR data for offline usage as we are ingesting around 9K msgs/seconds we used Appender API for the bulk insert but as soon we use it in few minutes of time we are hitting the memory out of exception as the memory keeps increasing and it is not getting stablalized at all.
Is there any open bug for this ? Or is there any improvements planned for the C# packages.
We were able to pinpoint this issue with the memory dumps that we got during the issue.
Code Used:

```csharp
using (var appender = _connection!.CreateAppender("main", "FailedMsgs"))
{
    foreach (var encryptedMessage in encryptedMessages)
    {
        var row = appender.CreateRow();
        row.AppendValue(encryptedMessage); // Message column
        row.AppendValue(DateTime.UtcNow);
        row.EndRow();
    }
}
```

Please let us know if you have any insights into this.

### To Reproduce

This is the code that we are using to insert the records in bulk

```csharp
using (var appender = _connection!.CreateAppender("main", "FailedMessages"))
{
    foreach (var encryptedMessage in encryptedMessages)
    {
        var row = appender.CreateRow();
        row.AppendValue(encryptedMessage); // Message column
        row.AppendValue(DateTime.UtcNow);
        row.EndRow();
    }
}
```

### OS:

Windows

### DuckDB Version:

1.4.4

### DuckDB Client:

1.4.4

### Hardware:

_No response_

### Full Name:

Varun

### Affiliation:

NA

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
cc @Giorgi

**Giorgi:**
@varunrains Did you use either a memory profiler or did you look in the dump to see whether it's native memory (belonging to duckdb itself) or managed memory from the .NET library?

**varunrains:**
Hi @Giorgi  Thanks for the reply. It was indeed the duckdb itself and it was not from the managed memory. (This was analyzed from teh memory dump that we took when analyzing the memory spikes)
We even tried to replace Duck DB from SQL Lite with the same code that we have and we are not seeing any memory issues with SQL Lite for the same code. From this we concluded that the Appender API is the culprit.

**Giorgi:**
@varunrains There are memory usage improvements in the 1.5.0 version of the .Net library: https://www.giorgi.dev/database/duckdb-net-1-5-performance/

**varunrains:**
Hi @Giorgi , Thanks will check this
