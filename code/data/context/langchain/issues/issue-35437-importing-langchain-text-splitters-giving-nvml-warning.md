# importing langchain_text_splitters giving NVML warning

**Issue #35437** | State: open | Created: 2026-02-25 | Updated: 2026-03-18
**Author:** caravin
**Labels:** bug, text-splitters, external

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
- [x] langchain-text-splitters
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
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
import langchain_text_splitters
```

### Error Message and Stack Trace (if applicable)

```shell
/usr/local/python/python-3.11/std/lib64/python3.11/site-packages/torch/cuda/__init__.py:611: UserWarning: Can't initialize NVML
  warnings.warn("Can't initialize NVML")
```

### Description

Just trying to import the package is resulting in the above warning. Although it isn't harmful, we have a couple of workflows where we raise flags if the process raise any warnings. And this warning is creating issues for us. 

I am not 100% sure that it is only because of langchain_text_splitters and not related to my setup but for me just importing this package is causing the issue

### System Info

langchain==1.x stack

## Comments

**keenborder786:**
@caravin 
Your machine either lacks an NVIDIA GPU, lacks NVIDIA drivers, or is running in a container/environment without GPU passthrough.

Why don't you just do the following? 

```python
import warnings
warnings.filterwarnings("ignore", message="Can't initialize NVML")
import langchain_text_splitters
```

This will just specifically filter the given warning and other warnings would still raise the flag.

**xXMrNidaXx:**
This is likely coming from a transitive dependency (probably `sentence-transformers` or `torch`) that langchain-text-splitters pulls in for certain semantic chunking features.

**Quick workarounds:**

1. **Filter the specific warning before imports:**
```python
import warnings
warnings.filterwarnings("ignore", message="Can't initialize NVML")

import langchain_text_splitters  # Now silent
```

2. **Set CUDA_VISIBLE_DEVICES to empty (if you don't need GPU):**
```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import langchain_text_splitters
```

3. **For CI/production workflows with zero-tolerance warnings:**
```python
import warnings
import sys

# Capture warnings as errors only for your code
warnings.filterwarnings("error")  # Treat warnings as errors
warnings.filterwarnings("ignore", module="torch.*")  # But allow torch's
warnings.filterwarnings("ignore", message=".*NVML.*")

import langchain_text_splitters
```

4. **Environment variable approach:**
```bash
PYTHONWARNINGS="ignore::UserWarning:torch.cuda" python your_script.py
```

**Root cause:** The warning originates from PyTorch's CUDA initialization when torch is imported (either directly or via sentence-transformers). If NVML (NVIDIA Management Library) isn't available (common in CPU-only environments, containers, or non-NVIDIA systems), torch logs this warning.

The cleanest fix would be for the affected upstream package to filter this internally, but since it's a UserWarning from torch's initialization path, filtering on import is the pragmatic solution.

For your CI/CD pipelines, I'd suggest option 1 or 4 - they're the most targeted and won't mask other legitimate warnings.

**caravin:**
thx @xXMrNidaXx / @keenborder786 for the suggestions.

To add some background, the standard machines on which we run our production jobs don't have GPUs installed in them. So we are seeing this warning. We have a bunch of teams/processes who are using `langchain-text-splitters` and it is kind of hard to ask every one of them to add the filter-warnings code in the launcher scripts.

I did some debugging as to why we weren't observing this earlier and why it started coming after the 1.x upgrade. I found that it is because of dependency packages like spacy, ntlk being imported globally -- earlier they were being imported lazily. This changed as part of 1.0.0 version in this PR -- https://github.com/langchain-ai/langchain/pull/32325
cc'ing @cbornet / @mdrxy as they are the authors/reviewers of this PR. Is there any reason why you guys decided to make the import global instead of lazy?

Additionally, I also started seeing spikes in memory usage post 1.x upgrade and that also links to this change. Because of importing these packages, globally, combinedly, they are adding an additional ~700MB memory usage (earlier, with 0.3.x version, this additional memory would be around ~50MB) 

```
In [2]: import os
   ...: import psutil
   ...: 
   ...: def mem():
   ...:     return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
   ...: 
   ...: print(f"Start: {mem():.1f} MiB")
   ...: from langchain_text_splitters import RecursiveCharacterTextSplitter
   ...: print(f"After RecursiveCharacterTextSplitter: {mem():.1f} MiB")
Start: 74.4 MiB
/usr/local/python/python-3.11/std/lib64/python3.11/site-packages/torch/cuda/__init__.py:611: UserWarning: Can't initialize NVML
  warnings.warn("Can't initialize NVML")
After RecursiveCharacterTextSplitter: 736.3 MiB

```
If there isn't any big reason behind this, we should try reverting it and make the imports lazy. Let me know if you want me to raise a PR with the change

**cbornet:**
That's ruff rule [PLC0415](https://docs.astral.sh/ruff/rules/import-outside-top-level/). Modules should be loaded lazily only if they have a high instantiation cost. Which seems to be the case here ! Is there really a module that takes 650MB at init ?? We should indeed identify which one is so greedy. I'll have a look.

**caravin:**
@cbornet, I see some PRs linked to this bug. While they are only making some imports lazy, I would prefer making everything lazy --exactly as it was earlier, before your PR changes. Can you add if you are planning to push this change? And if so, any timelines that you can share would be helpful

**gitbalaji:**
Hi, I have an open PR (#35469) that fixes this issue. Could you please assign this to me? Happy to address any review feedback.
