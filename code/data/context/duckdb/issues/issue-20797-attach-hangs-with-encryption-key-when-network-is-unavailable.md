# ATTACH hangs with ENCRYPTION_KEY when network is unavailable

**Issue #20797** | State: closed | Created: 2026-02-03 | Updated: 2026-03-18
**Author:** rkennedy-argus
**Labels:** under review

### What happens?

When using DuckDB to attach an encrypted database via `ATTACH {file} AS {database} (READ_ONLY, ENCRYPTION_KEY {key})` in an environment where there is no network connectivity (but where DNS is functioning), the ATTACH operation will hang.

When there is no network connectivity and DNS is non-functional, the ATTACH will proceed without issue. We hypothesize that the ATTACH is attempting to auto-install the httpfs extension (for better encryption performance). When the DNS lookup fails, the attempt to install the extension fails and DuckDB moves on as the performance optimization is entirely optional. However, when the DNS lookup succeeds, DuckDB moves on to attempt to fetch the extension via HTTP(S), which hangs indefinitely. We believe there is no connect timeout on the HTTP client at this stage.

### To Reproduce

Write a SQL file named `build_database.sql` to generate an encrypted database:

```sql
CREATE TABLE greetings (language VARCHAR, greeting VARCHAR);
INSERT INTO greetings VALUES ('en', 'Hello, World!');

ATTACH 'test_encrypted.db' AS test_enc (ENCRYPTION_KEY 'asdf');

COPY FROM DATABASE memory TO test_enc;
```

Run the SQL to build the database file `test_encrypted.db`:

```shell
duckdb -f build_database.sql
```

Create a Docker image that already has DuckDB installed using a Docker file like this:

```Dockerfile
FROM ubuntu:latest

RUN apt update && apt install -y curl
RUN curl https://install.duckdb.org | sh

ENTRYPOINT ["/bin/bash"]
```

Build the image:

```shell
docker buildx build -t duckdb-encryption-hang:latest .
```

Create a Docker network with functioning DNS but no internet access. e.g.

```shell
docker network create --subnet 172.19.0.0/16 \
    -o com.docker.network.bridge.enable_ip_masquerade=false \
    -o com.docker.network.bridge.name=nointernet \
    nointernet
```

Start a container running in that network. Mount the current working directory so you can access the encrypted database file:

```shell
docker run -it --rm --network nointernet -v $(pwd):/tmp/files duckdb-encryption-hang:latest 
```

Inside the running container, run DuckDB, attempting to attach the encrypted database:

```shell
/root/.duckdb/cli/1.4.4/duckdb -cmd "ATTACH '/tmp/files/test_encrypted.db' (READ_ONLY, ENCRYPTION_KEY 'asdf')"
```

At this point, DuckDB will hang (forever?). This is the failure mode we are encountering in our production network, where the application runs in an AWS VPC with private networking only (but where DNS works).

We can demonstrate what happens when DNS is also non-functional, by creating a fully air-gapped Docker network:

```shell
docker network create --internal airgap
```

Now start the container again, but use the `airgap` network this time:

```shell
docker run -it --rm --network airgap -v $(pwd):/tmp/files duckdb-encryption-hang:latest 
```

and attempt to open the database using the DuckDB CLI:

```shell
/root/.duckdb/cli/1.4.4/duckdb -cmd "ATTACH '/tmp/files/test_encrypted.db' (READ_ONLY, ENCRYPTION_KEY 'asdf')"
```

It takes a couple of seconds, but the database opens successfully:

```console
root@9a522024a1eb:/# /root/.duckdb/cli/1.4.4/duckdb -cmd "ATTACH '/tmp/files/test_encrypted.db' (READ_ONLY, ENCRYPTION_KEY 'asdf')"
100% ▕██████████████████████████████████████▏ (00:00:02.58 elapsed)
DuckDB v1.4.4 (Andium) 6ddac802ff
Enter ".help" for usage hints.
```

### OS:

linux/arm64

### DuckDB Version:

1.4.4

### DuckDB Client:

Python and CLI

### Hardware:

_No response_

### Full Name:

Ryan Kennedy

### Affiliation:

Group Argus

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**rkennedy-argus:**
You can also see this behavior if you're just installing extensions…

No DNS and no internet (the `airgap` network from the initial explanation)…

```console
% docker run -it --rm --network airgap -v $(pwd):/tmp/files duckdb-encryption-hang:latest
root@14ac8286db20:/# timeout -v 30s /root/.duckdb/cli/1.4.4/duckdb -c "INSTALL fts"
IO Error:
Failed to download extension "fts" at URL "http://extensions.duckdb.org/v1.4.4/linux_arm64/fts.duckdb_extension.gz"
Extension "fts" is an existing extension.

For more info, visit https://duckdb.org/docs/stable/extensions/troubleshooting?version=v1.4.4&platform=linux_arm64&extension=fts (ERROR Could not establish connection)
```

No internet, but working DNS (the `nointernet` network from the initial explanation…

```console
% docker run -it --rm --network nointernet -v $(pwd):/tmp/files duckdb-encryption-hang:latest
root@1ce70abba606:/# timeout -v 30s /root/.duckdb/cli/1.4.4/duckdb -c "INSTALL fts"
timeout: sending signal TERM to command '/root/.duckdb/cli/1.4.4/duckdb'
```

**samansmink:**
Hey @rkennedy-argus thanks for reporting.

This is likely happening due to DuckDB's autoloading mechanism combined with the high default timeouts + the retry mechanism. To work around this I think you can either:
- Make sure `httpfs` extension is preinstalled
- disable autoinstallation `SET autoinstall_known_extensions = false;`
- shorten the timeout + retries `SET http_timeout=4;SET http_retries=1` (2 tries with 4sec timeout)

**rkennedy-argus:**
> Hey [@rkennedy-argus](https://github.com/rkennedy-argus) thanks for reporting.
> 
> This is likely happening due to DuckDB's autoloading mechanism combined with the high default timeouts + the retry mechanism. To work around this I think you can either:
> 
> * Make sure `httpfs` extension is preinstalled

That's ultimately what we'll end up doing, if for no other reason than we want the hardware accelerated encryption benefit.

> * disable autoinstallation `SET autoinstall_known_extensions = false;`

This does work without triggering a 30 second timeout imposed via /usr/bin/timeout:

```console
root@603e921e1a1d:/# timeout -v 30s /root/.duckdb/cli/1.4.4/duckdb -c "SET autoinstall_known_extensions = false; ATTACH '/tmp/duckdb/test_encrypted.db' AS test_enc (READ_ONLY, ENCRYPTION_KEY 'asdf'); from test_enc.greetings;"
┌──────────┬───────────────┐
│ language │   greeting    │
│ varchar  │    varchar    │
├──────────┼───────────────┤
│ en       │ Hello, World! │
└──────────┴───────────────┘
```

> * shorten the timeout + retries `SET http_timeout=4;SET http_retries=1` (2 tries with 4sec timeout)

This gets timed out at 30 seconds:

```console
root@603e921e1a1d:/# timeout -v 30s /root/.duckdb/cli/1.4.4/duckdb -c "SET http_timeout=4; SET http_retries=1; ATTACH '/tmp/duckdb/test_encrypted.db' AS test_enc (READ_ONLY, ENCRYPTION_KEY 'asdf'); from test_enc.greetings;"
timeout: sending signal TERM to command '/root/.duckdb/cli/1.4.4/duckdb'
```

If I run it without `timeout`, it runs for 6 minutes before complaining that it can't download the extension:

```console
root@603e921e1a1d:/# time /root/.duckdb/cli/1.4.4/duckdb -c "SET http_timeout=4; SET http_retries=1; ATTACH '/tmp/duckdb/test_encrypted.db' AS test_enc (READ_ONLY, ENCRYPTION_KEY 'asdf'); from test_enc.greetings;"
Extension Autoloading Error:
An error occurred while trying to automatically install the required extension 'httpfs':
Failed to download extension "httpfs" at URL "http://extensions.duckdb.org/v1.4.4/linux_arm64/httpfs.duckdb_extension.gz"
Extension "httpfs" is an existing extension.

For more info, visit https://duckdb.org/docs/stable/extensions/troubleshooting?version=v1.4.4&platform=linux_arm64&extension=httpfs (ERROR Connection timed out)

real    6m0.989s
user    0m0.012s
sys     0m0.029s
```

Are `http_timeout` and `http_retries` used solely by the httpfs extension itself, rather than by the extension loading mechanism? I don't believe those configurations control the extension loading codepaths.

**samansmink:**
> Are http_timeout and http_retries used solely by the httpfs extension itself, rather than by the extension loading mechanism? I don't believe those configurations control the extension loading codepaths.

Ah you're right! This could indeed be the case, we'll take a look into fixing this

**carlopi:**
I think part of the issue have been solved in v1.5.0: attaching a READ_ONLY encrypted database will not trigger installation of `httpfs` anymore.

Behaviour should now be for READ_ONLY:
* if `httpfs` is available locally, attempt LOAD (might fail for signature), but always succeed
* if `httpfs` is NOT available locally, use base mbedtls
In neither case install is triggered.

Behaviour for write path will still require `httpfs`, so that's LOADed, or INSTALLed + LOADed, but if neither are successful then an error is thrown.

On the sub-issue of `http_timeout` not being used, that I don't think it's completely correct: issue is that issuing `SET http_timeout = 1` will on its own trigger INSTALL of httpfs. Once httpfs is loaded, then it will respect the settings, but to get that you still get default timeouts.

Solution here is lifting `http_timeout` and `http_retries` from duckdb-httpfs to duckdb, so they can be always used.

**carlopi:**
I think, strictly speaking, issue is solved already in v1.5.0, and the suggested solution for network restricted setup is to disable extensions auto-installing, since that's bound to fail (but will take a while to do so), or provide a custom (and reachable) extension endpoint.

I will branch the subissue of lifting `http_timeout` and `http_retries`, that I think it's a good UX.

**rkennedy-argus:**
> On the sub-issue of `http_timeout` not being used, that I don't think it's completely correct: issue is that issuing `SET http_timeout = 1` will on its own trigger INSTALL of httpfs. Once httpfs is loaded, then it will respect the settings, but to get that you still get default timeouts.

Oh, interesting. I hadn't even considered that the configuration value was itself tied to the extension and that utilizing it would trigger extension auto install.

I'm happy to hear about the change in 1.5.0 regarding READ_ONLY encrypted debases and I appreciate the opening of #21452. I think lifting the `http_[timeout|retries]` configurations is a good plan.

Thank you for helping to keeps all our ducks in a row.
