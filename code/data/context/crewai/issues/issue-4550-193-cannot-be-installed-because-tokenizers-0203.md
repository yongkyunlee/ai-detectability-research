# 1.9.3 cannot be installed because tokenizers 0.20.3

**Issue #4550** | State: closed | Created: 2026-02-20 | Updated: 2026-03-02
**Author:** z-a-f

`tokenizers~=0.20.3` is missing the version in their `pyproject.toml`, but 1.9.3 depends on it. That means if you try `uv tool install "crewai==1.9.3"`, it would break with the following:

```shell
$ uv tool install crewai
Resolved 128 packages in 369ms
  × Failed to download and build `tokenizers==0.20.3`
  ├─▶ Failed to parse:
  │   `C:\Users\ztahi\AppData\Local\uv\cache\sdists-v9\pypi\tokenizers\0.20.3\FG5MpixO2GrV2GmCLXByU\src\pyproject.toml`
  ╰─▶ TOML parse error at line 1, column 1
        |
      1 | [project]
        | ^^^^^^^^^
      `pyproject.toml` is using the `[project]` table, but the required `project.version` field is neither set nor present in the   
      `project.dynamic` list

  help: `tokenizers` (v0.20.3) was included because `crewai` (v1.9.3) depends on `tokenizers`
```

* Affecting `tokenizers v0.20.3`: https://github.com/huggingface/tokenizers/blob/v0.20.3/bindings/python/pyproject.toml
* Fix was introduced in v0.23: https://github.com/huggingface/tokenizers/commit/3a6504d2740ef3892350ef074beffe4a1ac87a64#diff-bf903f17157a753e10c075d464383a2e36fc657641d17673f054239f8d1a3999R28

## Comments

**whutzefengxie-ops:**
I encountered the same problem and avoided the error by using the following command.
`uv pip install 'tokenizers>=0.21.0' crewai`
