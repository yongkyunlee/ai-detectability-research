# Inconsistent package naming in your security advisories

**Issue #36082** | State: closed | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** joshbressers
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
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
N/A
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

Your security page lists 3 advisories

https://github.com/langchain-ai/langchain/security

Two of them have package details errors

## GHSA-2g6r-c272-w58r
https://github.com/langchain-ai/langchain/security/advisories/GHSA-2g6r-c272-w58r

That advisory doesn't list a package name, but included the package name in the version information
`langchain-core==0.3.81`

## GHSA-6qv9-48xg-fc7f
https://github.com/langchain-ai/langchain/security/advisories/GHSA-6qv9-48xg-fc7f

The package name listed is langchain_core instead of langchain-core

Thanks in advance

### System Info

N/A

## Comments

**mdrxy:**
does this create downstream problems? genuinely asking -- on PyPI we use `langchain-core`, in code imports you use `langchain_core`

**joshbressers:**
The various downstream things (I work with Grype for example) expect the GHSA to reference the package name, not the import

**mdrxy:**
I see, thanks @joshbressers 

should be fixed now
