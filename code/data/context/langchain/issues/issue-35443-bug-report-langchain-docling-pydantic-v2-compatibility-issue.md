# # Bug Report: langchain-docling Pydantic v2 Compatibility Issue

**Issue #35443** | State: open | Created: 2026-02-25 | Updated: 2026-03-09
**Author:** ajithpaugustine
**Labels:** bug, external

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
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
from langchain_docling import DoclingLoader

def main():
    FILE_PATH = ["https://arxiv.org/pdf/2408.09869"]  # Docling Technical Report
    
    loader = DoclingLoader(file_path=FILE_PATH)
    docs = loader.load()

    print(f"Loaded {len(docs)} documents")
    print(docs[0].page_content[:500])  # Print first 500 characters

if __name__ == "__main__":
    main()
```

### Error Message and Stack Trace (if applicable)

```shell
File "d:\arvix_benchmark\venv\lib\site-packages\docling_core\types\__init__.py", line 3, in 
    from docling_core.types.doc.document import DoclingDocument
  File "d:\arvix_benchmark\venv\lib\site-packages\docling_core\types\doc\__init__.py", line 4, in 
    from .document import (
  File "d:\arvix_benchmark\venv\lib\site-packages\docling_core\types\doc\document.py", line 49, in 
    from docling_core.search.package import VERSION_PATTERN
  File "d:\arvix_benchmark\venv\lib\site-packages\docling_core\search\package.py", line 17, in 
    class Package(BaseModel, extra="forbid"):
  File "d:\arvix_benchmark\venv\lib\site-packages\docling_core\search\package.py", line 24, in Package
    version: Annotated[str, StringConstraints(strict=True, pattern=VERSION_PATTERN)] = importlib.metadata.version(
TypeError: StringConstraints() takes no arguments
```

### Description

# Bug Report: langchain-docling Pydantic v2 Compatibility Issue

## Summary
`langchain-docling` fails to import with a `TypeError: StringConstraints() takes no arguments` when using current versions of `docling-core` and Pydantic v2.

## Environment
- **Python**: 3.9.7
- **langchain-docling**: 1.1.0
- **docling**: 2.69.1
- **docling-core**: 2.60.1
- **pydantic**: 2.12.5
- **OS**: Windows 10

## Error Trace
```
Traceback (most recent call last):
  File "D:\arvix_benchmark\load.py", line 1, in 
    from langchain_docling import DoclingLoader
  File "D:\arvix_benchmark\venv\lib\site-packages\langchain_docling\__init__.py", line 7, in 
    from langchain_docling.loader import DoclingLoader
  File "D:\arvix_benchmark\venv\lib\site-packages\langchain_docling\loader.py", line 12, in 
    from docling.chunking import BaseChunk, BaseChunker, HybridChunker
  ...
  File "D:\arvix_benchmark\venv\lib\site-packages\docling_core\search\package.py", line 17, in 
    class Package(BaseModel, extra="forbid"):
  File "D:\arvix_benchmark\venv\lib\site-packages\docling_core\search\package.py", line 24, in Package
    version: Annotated[str, StringConstraints(strict=True, pattern=VERSION_PATTERN)] = ...
TypeError: StringConstraints() takes no arguments
```

## Root Cause
In `docling_core/search/package.py` line 24, the code calls:
```python
StringConstraints(strict=True, pattern=VERSION_PATTERN)
```

However, in **Pydantic v2.12.5**, `StringConstraints()` does not accept positional/keyword arguments in this way. The correct syntax for Pydantic v2 is:
```python
StringConstraints(min_length=1, pattern=VERSION_PATTERN)
# or use Field with constraints
```

## Steps to Reproduce
1. Create a Python 3.9+ environment
2. Install: `pip install langchain-docling pydantic>=2.0`
3. Try to import: `from langchain_docling import DoclingLoader`
4. Error occurs

## Expected Behavior
`langchain-docling` should import successfully and be usable with Pydantic v2.x

## Actual Behavior
Import fails with `TypeError: StringConstraints() takes no arguments`

## Suggested Fix
Update `docling-core` to use Pydantic v2 syntax for `StringConstraints`, or pin `pydantic` to a compatible version in `setup.py`/`pyproject.toml`.

## Workaround (if available)
- Downgrade to older versions: `pip install docling-core==2.48.0 docling==2.18.0`
- Or use an alternative document loader

---

**Report this to:**
- https://github.com/langchain-ai/langchain-docling (or relevant repo)

### System Info

   
System Information
------------------
> OS:  Windows
> OS Version:  10.0.22631
> Python Version:  3.9.7 (default, Sep 16 2021, 16:59:28) [MSC v.1916 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 0.3.83
> langchain: 0.3.27
> langsmith: 0.4.37
> langchain_docling: 1.1.0
> langchain_text_splitters: 0.3.11

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> async-timeout=4.0.0;: Installed. No version info available.
> claude-agent-sdk>=0.1.0;: Installed. No version info available.
> docling~=2.18: Installed. No version info available.
> httpx=0.23.0: Installed. No version info available.
> jsonpatch=1.33.0: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.72: Installed. No version info available.
> langchain-core=0.3.75: Installed. No version info available.
> langchain-core~=0.3.19: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=0.3.9: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langsmith-pyo3>=0.1.0rc2;: Installed. No version info available.
> langsmith=0.3.45: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> openai-agents>=0.0.3;: Installed. No version info available.
> opentelemetry-api>=1.30.0;: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http>=1.30.0;: Installed. No version info available.
> opentelemetry-sdk>=1.30.0;: Installed. No version info available.
> orjson>=3.9.14;: Installed. No version info available.
> packaging=23.2.0: Installed. No version info available.
> packaging>=23.2: Installed. No version info available.
> pydantic=1: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pytest>=7.0.0;: Installed. No version info available.
> PyYAML=5.3.0: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> requests-toolbelt>=1.0.0: Installed. No version info available.
> requests=2: Installed. No version info available.
> requests>=2.0.0: Installed. No version info available.
> rich>=13.9.4;: Installed. No version info available.
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> typing-extensions=4.7.0: Installed. No version info available.
> uuid-utils=0.12.0: Installed. No version info available.
> vcrpy>=7.0.0;: Installed. No version info available.
> zstandard>=0.23.0: Installed. No version info available.

## Comments

**xXMrNidaXx:**
## Root Cause Analysis

This is a Pydantic v1 vs v2 compatibility issue in `docling-core`, not directly in `langchain-docling`.

The error occurs because `StringConstraints` in Pydantic v2 is a class that accepts keyword arguments, but the code is being called with Pydantic v1 semantics where `StringConstraints()` takes no arguments.

**Two scenarios cause this:**

1. **Mixed Pydantic versions:** `docling-core` was written for Pydantic v2, but you have v1 installed (possibly pinned by another dependency)

2. **Version mismatch:** Older `docling-core` expects Pydantic v1, but you have v2

## Workarounds

**Option 1: Force Pydantic v2**
```bash
pip install "pydantic>=2.0,=2.0,=2.0,<3.0"
```

This would fail-fast during install rather than at runtime.

---
*Corey Nida | [RevolutionAI](https://revolutionai.io) — We help teams ship AI products without the infrastructure headaches.*

**keenborder786:**
@ajithpaugustine Feel like an appropriate place to open the issue is at the following repo: https://github.com/docling-project/docling-langchain

**ajithpaugustine:**
thanks @xXMrNidaXx  for the reply. I tried those but the issue i am facing was in importing in the library itself. i tried forcing pydantic v2 but still the issue persists.

As @keenborder786  has pointed it out let me open an issue with docling repo rather than langchain.

Thank you guys!

**keenborder786:**
@ajithpaugustine can you close the issue here?
