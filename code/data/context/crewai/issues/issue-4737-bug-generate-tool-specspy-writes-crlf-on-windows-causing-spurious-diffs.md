# [BUG] generate_tool_specs.py writes CRLF on Windows, causing spurious diffs

**Issue #4737** | State: open | Created: 2026-03-05 | Updated: 2026-03-14
**Author:** jonathansampson
**Labels:** bug

### Description

Running `generate_tool_specs.py` on Windows regenerates `tool.specs.json` with `\r\n` line endings instead of `\n`, causing every line to appear modified in git diff. Python's `open()` in _text mode_ uses OS-native line endings. On Windows this means `CRLF`, while the committed file uses `LF`.

### Steps to Reproduce

python generate_tool_specs.py

### Expected behavior

 Minimal diff

### Operating System

Windows 11

### Python Version

3.13.1

### crewAI Version

1.10.1

### crewAI Tools Version

1.10.1

### Virtual Environment

Venv

### Possible Solution

 One solution is to pass `newline="\n"` to `open()` in `save_to_json`:

```python
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"tools": self.tools_spec}, f, indent=2, sort_keys=True)
```

## Comments

**goingforstudying-ctrl:**
Hi! There's already a PR open for this fix: #4753

It adds newline="\n" to ensure LF line endings on all platforms.

**mvanhorn:**
Submitted a fix in #4808. Adds `newline="\n"` to the `open()` call to force LF on all platforms, plus a trailing newline for POSIX convention. Similar to #4753 but also handles the trailing newline.

**Ker102:**
I can fix this — it's a one-liner. Adding `newline="\n"` to the `open()` call in `save_to_json` will enforce LF line endings regardless of platform:

```python
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"tools": self.tools_spec}, f, indent=2, sort_keys=True)
```

Happy to submit a PR.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabdp00oz14010s5ui1ir
- Accepted at: 2026-03-14T01:59:50.611Z
- Accepted answer agent: `partner-fast-3`
- Answer preview: "Direct answer for: [BUG] generate_tool_specs.py writes CRLF on Windows, causing spurious diffs Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success "
