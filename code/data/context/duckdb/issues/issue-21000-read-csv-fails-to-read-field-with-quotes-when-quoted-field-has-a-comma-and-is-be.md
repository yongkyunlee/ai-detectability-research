# read_csv fails to read field with quotes when quoted field has a comma and is beyond sample_size rows

**Issue #21000** | State: open | Created: 2026-02-18 | Updated: 2026-03-08
**Author:** omerfyalcin
**Labels:** reproduced

### What happens?

I have a CSV file where one column has character values. None of them are quoted, except for one row that has "Beth, Bens. Co." — quoted (with double quotes) because of the comma inside it. read_csv() fails in its default settings. It treats the comma as a delimiter and gets confused by the extra column. 

I'm pretty sure the sniffer looks at the first 20480 rows, sees no quotes anywhere, and decides the file doesn't use quoting. Then when it hits the quoted field later, it doesn't handle it correctly. This is the error I get from an example file with only two columns (file attached below):

```
Invalid Input Error:
CSV Error on Line: 20502
Original Line: Bob,"Beth, Bens. Co."
Expected Number of Columns: 2 Found: 3
Possible fixes:
* Disable the parser's strict mode (strict_mode=false) to allow reading rows that do not comply with the CSV standard.
* Enable null padding (null_padding=true) to replace missing values with NULL
* Enable ignore errors (ignore_errors=true) to skip this row

  file = test.csv
  delimiter = , (Auto-Detected)
  quote = (empty) (Auto-Detected)
  escape = (empty) (Auto-Detected)
  new_line = \n (Auto-Detected)
  header = true (Auto-Detected)
  skip_rows = 0 (Auto-Detected)
  comment = (empty) (Auto-Detected)
  strict_mode = true (Auto-Detected)
  date_format =  (Auto-Detected)
  timestamp_format =  (Auto-Detected)
  null_padding = 0
  sample_size = 20480
  ignore_errors = false
  all_varchar = 0
```

This can be fixed with either explicitly passing `quote = '"'` as an argument to read_csv() or increasing the sample_size until it covers the quoted field. I should also note that this only fails when the field has a comma in it: when everything else is the same but comma is removed, it does not fail.

Lastly, I also tested this with csv readers of pandas, polars, data.table, readr, and base R, using their default settings in each case. They all read it correctly by default, leading me to think that this should also work by default in duckdb without specifying additional arguments.

Here's the test file this was generated from:
[test.csv](https://github.com/user-attachments/files/25381084/test.csv)

The test file (test.csv) can I also be reproduced with the following Python script:

```
with open("test.csv", "w") as f:
    f.write("name,company\n")
    for i in range(20500):
        f.write(f"Alice,Acme Corp\n")
    f.write('Bob,"Beth, Bens. Co."\n')
```

Thank you for your amazing work on this wonderful tool!

### To Reproduce

To reproduce, on the duckdb CLI, run:

```
FROM read_csv('test.csv');
```

### OS:

Kubuntu 24.04,  x86_64

### DuckDB Version:

v1.4.4 (Andium) 6ddac802ff

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Omer F. Yalcin

### Affiliation:

University of Massachusetts Amherst

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hello @omerfyalcin, thanks for reporting. I could reproduce the issue and we'll take a look.

In the meantime, a possible workaround for such files is to pass `sample_size = -1`, so DuckDB is forced to scan the whole file when trying to detect the CSV's dialect.

```sql
FROM read_csv('test.csv', sample_size = -1);
```

**kchasialis:**
Hello,

I have submitted a PR for this issue.
https://github.com/duckdb/duckdb/pull/21228

Please let me know if it works!
