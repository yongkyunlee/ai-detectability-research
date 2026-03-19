# Chain.save() broken in 0.3.28: model_dump() doesn't inject _type

**Issue #35665** | State: open | Created: 2026-03-08 | Updated: 2026-03-09
**Author:** harupy
**Labels:** langchain, external

### Checked other resources

- [X] This is a bug, not a usage question.
- [X] I added a clear and descriptive title that summarizes this issue.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [X] This is not related to the langchain-community package.
- [X] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [X] langchain

### Related Issues / PRs

#33035

### Reproduction Steps / Example Code (Python)

```python
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.llms.fake import FakeListLLM

llm = FakeListLLM(responses=["hello"])
prompt = PromptTemplate(input_variables=["input"], template="{input}")
chain = LLMChain(llm=llm, prompt=prompt)
chain.save("/tmp/test_chain.yaml")  # Works on 0.3.27, fails on 0.3.28
```

### Error Message and Stack Trace

```
Traceback (most recent call last):
  File "", line 9, in 
  File "langchain/chains/base.py", line 785, in save
    raise NotImplementedError(msg)
NotImplementedError: Chain verbose=False prompt=PromptTemplate(input_variables=['input'], input_types={}, partial_variables={}, template='{input}') llm=FakeListLLM(responses=['hello']) output_parser=StrOutputParser() llm_kwargs={} does not support saving.
```

### Description

- #33035 changed `Chain.save()` from `self.dict()` to `self.model_dump()`.
- `dict()` injects `_type` via `_chain_type`; `model_dump()` inherits from Pydantic BaseModel and never includes it.
- `save()` now always hits `"_type" not in chain_dict` and raises `NotImplementedError`.
- This is a regression from 0.3.27 -> 0.3.28.

### System Info

```
> langchain_core: 0.3.83
> langchain: 0.3.28
> langchain_community: 0.3.31
> Python Version: 3.10.17
> OS: Darwin
```

## Comments

**keenborder786:**
After checking it out, a regression was introduced in #33035 which have been taken care of in above PR.
