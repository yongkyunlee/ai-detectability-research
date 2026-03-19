# langchain-huggingface==1.2.1 was not released to pypi

**Issue #35483** | State: closed | Created: 2026-02-28 | Updated: 2026-03-02
**Author:** MichaelKarpe
**Labels:** bug, huggingface, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [x] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

#35182 

### Reproduction Steps / Example Code (Python)

```python
pip install langchain-huggingface==1.2.1
```

### Error Message and Stack Trace (if applicable)

```shell
ERROR: Could not find a version that satisfies the requirement langchain-huggingface==1.2.1 (from versions: 0.0.1, 0.0.2, 0.0.3, 0.1.0.dev1, 0.1.0, 0.1.1, 0.1.2, 0.2.0, 0.3.0, 0.3.1, 1.0.0a1, 1.0.0, 1.0.1, 1.1.0, 1.2.0)
ERROR: No matching distribution found for langchain-huggingface==1.2.1
```

### Description

Despite #35182, langchain-huggingface==1.2.1 has not been released to pypi and installing this version with pip does not work

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Mon Feb  2 12:27:57 UTC 2026
> Python Version:  3.12.12 (main, Oct 10 2025, 08:52:57) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 1.2.15
> langchain: 1.2.10
> langsmith: 0.7.6
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> google-adk: 1.25.1
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.9
> opentelemetry-api: 1.38.0
> opentelemetry-exporter-otlp-proto-http: 1.38.0
> opentelemetry-sdk: 1.38.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.3
> pytest: 8.4.2
> pyyaml: 6.0.3
> requests: 2.32.4
> requests-toolbelt: 1.0.0
> rich: 13.9.4
> tenacity: 9.1.4
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> wrapt: 2.1.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**Shivangisharma4:**
Hey @MichaelKarpe ,  I took a look at this, The version bump to 1.2.1 was correctly done in PR #35182 - pyproject.toml and uv.lock are both updated. But it looks like the release workflow (_release.yml) was never triggered after the merge, since there's no langchain-huggingface==1.2.1 git tag in the repo (which gets created automatically when the workflow completes successfully).
