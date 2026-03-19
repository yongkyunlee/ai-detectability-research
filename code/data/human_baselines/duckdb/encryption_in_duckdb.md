---
source_url: https://duckdb.org/2025/11/19/encryption-in-duckdb
author: Lotte Felius, Hannes Mühleisen
platform: DuckDB official blog
scope_notes: "Full engineering blog post on data-at-rest encryption in DuckDB v1.4"
---

# Data-at-Rest Encryption in DuckDB

**Authors:** Lotte Felius, Hannes Mühleisen
**Date:** 2025-11-19

## TL;DR

Starting with DuckDB v1.4, transparent data-at-rest encryption using industry-standard AES encryption is now available. The implementation supports both AES-GCM-256 (authenticated) and AES-CTR-256 (faster but unauthenticated) ciphers with minimal performance overhead.

## Historical Context

The authors reference Simon Singh's "The Code Book," noting that even Mary, Queen of Scots used encryption (Caesar cipher) for sensitive correspondence—though it was eventually broken. Today, cryptography is widespread across CPUs and operating systems, yet many prominent databases offer limited encryption options. PostgreSQL has very limited choices, and SQLite requires a "$2000 add-on" for encryption.

## Encryption Fundamentals

**Advanced Encryption Standard (AES)** is the industry standard symmetric cipher. DuckDB implements:

- **AES-GCM-256**: Authenticates data via a calculated tag, preventing tampering
- **AES-CTR-256**: Faster but lacks authentication

Both require plaintext input, an initialization vector (IV), and an encryption key. The nonce (12 bytes) plus counter (4 bytes) create the IV, ensuring identical plaintexts encrypt differently. "IV reuse is problematic, since an attacker could XOR the two ciphertexts and extract" both messages.

## DuckDB Implementation Details

### Database Header Structure

The main database header remains plaintext (containing no sensitive data). When encryption is enabled, the first flag bit is set, followed by:

1. **Database identifier**: 16 random bytes functioning as a salt
2. **Metadata**: 8 bytes specifying key derivation function, authentication data usage, cipher type, and key length
3. **Encrypted canary**: Validates correct key input

### Encryption Key Management

Users provide any plaintext or base64-encoded string, but 32-byte base64 keys are recommended. Rather than using keys directly, DuckDB derives secure keys via key derivation functions (KDF), reducing them to 32-byte keys. Derived keys are cached in a secure, memory-locked cache that prevents disk swapping. Original plaintext keys are immediately wiped from memory after derivation.

### Block Structure

After the main header, two 4KB database headers contain configuration details. Remaining headers and blocks are encrypted when enabled.

**Plaintext blocks** contain an 8-byte block header with a checksum.

**Encrypted blocks** contain a 40-byte header with:
- 16-byte nonce/IV
- Optional 16-byte tag (depending on cipher)
- Encrypted checksum

### Write-Ahead Log (WAL) Encryption

The WAL ensures durability by logging changes before writing to the main database. For encrypted databases, WAL entries are encrypted per-value, with:

1. Length (plaintext)
2. Nonce
3. Encrypted checksum
4. Encrypted entry
5. 16-byte authentication tag

### Temporary File Encryption

Intermediate data from sorting, joins, and window functions is automatically encrypted when using encrypted databases or when setting `temp_file_encryption = true`. DuckDB generates temporary encryption keys for these files, which are lost on crash—making temporary files undecryptable garbage in failure scenarios.

## Usage Examples

### Creating an Encrypted Database

```sql
INSTALL tpch;
LOAD tpch;
ATTACH 'encrypted.duckdb' AS encrypted (ENCRYPTION_KEY 'asdf');
ATTACH 'unencrypted.duckdb' AS unencrypted;
USE unencrypted;
CALL dbgen(sf = 1);
COPY FROM DATABASE unencrypted TO encrypted;
```

### Decrypting a Database

```sql
ATTACH 'encrypted.duckdb' AS encrypted (ENCRYPTION_KEY 'asdf');
ATTACH 'new_unencrypted.duckdb' AS unencrypted;
COPY FROM DATABASE encrypted TO unencrypted;
```

### Re-encrypting with a New Key

```sql
ATTACH 'encrypted.duckdb' AS encrypted (ENCRYPTION_KEY 'asdf');
ATTACH 'new_encrypted.duckdb' AS new_encrypted (ENCRYPTION_KEY 'xxxx');
COPY FROM DATABASE encrypted TO new_encrypted;
```

### Using AES-CTR Instead of Default GCM

```sql
ATTACH 'encrypted.duckdb' AS encrypted (
    ENCRYPTION_KEY 'asdf',
    ENCRYPTION_CIPHER 'CTR'
);
```

### Querying Encryption Status

```sql
FROM duckdb_databases();
```

This returns database names, paths, and encryption status.

### Forcing Temporary File Creation

```sql
SET memory_limit = '1GB';
ATTACH 'tpch_encrypted.db' AS enc (
    ENCRYPTION_KEY 'asdf',
    ENCRYPTION_CIPHER 'cipher'
);
USE enc;
CALL dbgen(sf = 1);
```

## Implementation and Performance

DuckDB implemented encryption twice for flexibility without external dependencies:

1. **Mbed TLS**: Embedded within DuckDB, but lacks hardware acceleration
2. **OpenSSL**: Available via the `httpfs` extension, with hardware-accelerated AES operations

Due to random number generator vulnerabilities discovered in Mbed TLS mode post-release, DuckDB disabled writes to databases using Mbed TLS in v1.4.1. Version 1.4.2+ automatically installs and loads `httpfs` (enabling OpenSSL) when writes are attempted.

### Performance Results

**SUMMARIZE Query (5.4 seconds unencrypted TPC-H data, scale factor 10)**:
- Mbed TLS: ~6.2 seconds
- OpenSSL: ~5.4 seconds (hardware acceleration eliminates overhead)

**TPC-H Power Test (scale factor 100, 16GB memory)**:
- **Without encryption**: Power@Size: 624,296; Throughput@Size: 450,409
- **With encryption**: Essentially unchanged

**TPC-H Power Test (scale factor 100, 8GB memory)**:
- **Without encryption**: Power@Size: 591,841; Throughput@Size: 153,690
- **With encryption**: Power@Size: 571,985; Throughput@Size: 145,353

The performance difference with disk stress is minimal and "likely not relevant in real operational scenarios."

## Limitations and Future Work

DuckDB's encryption "does not yet meet the official NIST requirements." The implementation tracks progress toward NIST compliance via GitHub issue #20162 ("Store and verify tag for canary encryption").

## Conclusion

The encryption feature enables new deployment models: encrypted DuckDB files can be distributed via CDNs with read-only access using decryption keys. Threat modeling simplifies on cloud providers since "access to DuckDB storage would have been enough to leak data" previously. With OpenSSL, "there is almost no performance overhead to using encryption in DuckDB," especially considering hardware acceleration.
