# Password leaks when using ATTACH and there's an IOException in the Python client

**Issue #21420** | State: closed | Created: 2026-03-17 | Updated: 2026-03-17
**Author:** brunomurino
**Labels:** under review

### What happens?

The python client exception IOException outputs the entire "ATTACH" arguments used, including the password.

### To Reproduce

Using duckdb 1.5, python 3.12.8, using the mysql extension, and running a local mariadb database on localhost, port 30006, username "root" and password "password", this yields the exception:
```
import duckdb

cnx = duckdb.connect()
cnx.install_extension("mysql")
cnx.load_extension("mysql")
query = f"""ATTACH '
    host=localhost
    user=root
    port=30006
    password=passwor
' AS mydb (TYPE mysql)
;"""
cnx.sql(query)
cnx.sql("select * from mydb.information_schema.tables")
```

### OS:

macOS Tahoe

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Bruno Murino

### Affiliation:

Landbay Partners Ltd

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**staticlibs:**
Hi, thanks for the report! I wonder if you can use the [Secrets Manager](https://duckdb.org/docs/stable/configuration/secrets_manager) in that env to keep only non-sensitive info in the connection string? Related change in MySQL extension - duckdb/duckdb-mysql#172.

**brunomurino:**
I had tried using the Secrets Manager and was getting the same behaviour, but was a few versions ago! Just tried the following and the exception text doesn't leak the password:
```
import duckdb

cnx = duckdb.connect()
cnx.install_extension("mysql")
cnx.load_extension("mysql")
sec = f"""
CREATE SECRET mysql_secret_one (
    TYPE mysql,
    HOST 'localhost',
    PORT 30006,
    USER 'root',
    PASSWORD 'passwor'
);
"""
cnx.sql(sec)
cnx.sql(f"ATTACH '' AS mydb (TYPE mysql,  SECRET mysql_secret_one);")
cnx.sql("select * from mydb.information_schema.tables")
```

Thank you @Mytherin
