# Docs: langchain-huggingface README missing [full] extra — HuggingFaceEmbeddings silently fails without sentence-transformers>=5.2.0

**Issue #35712** | State: closed | Created: 2026-03-10 | Updated: 2026-03-10
**Author:** anix-lynch
**Labels:** external

## Summary

The `langchain-huggingface` README only shows:

```bash
pip install langchain-huggingface
```

But `sentence-transformers` is an **optional dependency** (under `[full]` extra, requiring `>=5.2.0`). Users who follow the README and try to use `HuggingFaceEmbeddings` hit an `ImportError` at runtime with no guidance on how to fix it.

## The Problem

From `libs/partners/huggingface/pyproject.toml`:

```toml
[project.optional-dependencies]
full = [
    "transformers>=5.0.0,=5.2.0,=2.2.0
from langchain_community.embeddings import HuggingFaceEmbeddings

# New (langchain-huggingface) — requires sentence-transformers>=5.2.0
from langchain_huggingface import HuggingFaceEmbeddings
```

Many projects have `sentence-transformers>=2.2.0` pinned in `requirements.txt` from older tutorials. After migrating to `langchain-huggingface`, they get an ImportError even though sentence-transformers IS installed — because their version (2.x or 3.x) is below the 5.2.0 minimum.

## Minimal Reproduction

```bash
pip install langchain-huggingface sentence-transformers==2.7.0  # common older pin
python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings()"
# ImportError or unexpected behavior
```

## Expected Fix

README should show:

```bash
# Base install
pip install langchain-huggingface

# For HuggingFaceEmbeddings (local inference with sentence-transformers)
pip install langchain-huggingface[full]
# or explicitly:
pip install langchain-huggingface "sentence-transformers>=5.2.0"
```

With a migration note that `langchain-community` accepted `sentence-transformers>=2.2.0` but `langchain-huggingface[full]` requires `>=5.2.0`.

## Environment

- langchain-huggingface: 1.x
- sentence-transformers: 2.2.0 (pinned from older project, common in ML pipelines)
- Hit during migration from `langchain_community.embeddings.HuggingFaceEmbeddings` to `langchain_huggingface`
- Discovered while migrating a resume embedding pipeline that used local HuggingFace models to avoid API costs

## Comments

**agarwalkirti:**
Hi, I’d like to work on this documentation improvement.

My plan is to update the README under the installation section to:
- mention the optional [full] extra
- show the command `pip install langchain-huggingface[full]`
- add guidance for installing `sentence-transformers>=5.2.0`
- include a migration note for users coming from langchain-community

Let me know if this approach looks good and I can submit a PR.
