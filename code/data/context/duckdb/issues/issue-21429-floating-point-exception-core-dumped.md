# Floating point exception (core dumped)

**Issue #21429** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** DerZc
**Labels:** needs triage

### What happens?

The following test case triggers a core dump

```sql
CREATE TABLE t1(c0 BOOL);
SELECT (((((CASE t1.rowid WHEN 0.8275004431515318 THEN t1.c0 ELSE '0.2377015493079887' END ))))) FROM t1;
```

### OS:

ubuntu 24.04

### DuckDB Version:

 v1.6.0-dev1462

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Chi Zhang

### Affiliation:

Tsinghua University

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**DerZc:**
[hs_err_pid895301.log](https://github.com/user-attachments/files/26059676/hs_err_pid895301.log)

Hope this log is helpful.

**szarnyasg:**
Hi @DerZc, thanks for opening this issue. I have not yet been able to reproduce it on macOS and Ubuntu x86/arm64. I tried different builds (stable/relassert/debug).

Could you please provide more information?
* Are you running on x86_64 or arm64?
* Is it a debug build?
* Did you try the build on the latest commit hash, currently ff4f70eeee83cfd3dae6577fc9b2b448d5fbdb35?

**DerZc:**
Hi @szarnyasg I am running on a x86_64 server, it is a release build. 

There are some information:
```
processor	: 127
vendor_id	: AuthenticAMD
cpu family	: 15
model		: 107
model name	: QEMU Virtual CPU version 2.5+
stepping	: 1
microcode	: 0x1000065
cpu MHz		: 2449.998
cache size	: 512 KB
physical id	: 0
siblings	: 128
core id		: 127
cpu cores	: 128
apicid		: 127
initial apicid	: 127
fpu		: yes
fpu_exception	: yes
cpuid level	: 13
wp		: yes
flags		: fpu de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx lm rep_good nopl cpuid extd_apicid tsc_known_freq pni ssse3 cx16 sse4_1 sse4_2 x2apic popcnt aes hypervisor lahf_lm cmp_legacy 3dnowprefetch vmmcall
bugs		: fxsave_leak sysret_ss_attrs null_seg swapgs_fence amd_e400 spectre_v1 spectre_v2
bogomips	: 4899.99
TLB size	: 1024 4K pages
clflush size	: 64
cache_alignment	: 64
address sizes	: 40 bits physical, 48 bits virtual
power management:
```

This is a screen record

https://github.com/user-attachments/assets/eea8534c-f174-4db3-8c1a-19cc8c37d063
