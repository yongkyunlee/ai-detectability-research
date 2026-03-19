# DOC: Incorrect usage of `getpass` module in Google Generative AI Embedding documentation

**Issue #29809** | State: closed | Created: 2025-02-14 | Updated: 2026-03-08
**Author:** jasminaaa20
**Labels:** external

### URL

https://python.langchain.com/docs/integrations/text_embedding/google_generative_ai/

### Checklist

- [x] I added a very descriptive title to this issue.
- [x] I included a link to the documentation page I am referring to (if applicable).

### Issue with current documentation:

The LangChain documentation for Google Generative AI Embedding contains an incorrect usage of the `getpass` module. The provided code:

```python
os.environ["GOOGLE_API_KEY"] = getpass("Provide your Google API key here")
```

results in:

```
TypeError: 'module' object is not callable
```

**Correct Code:**

```python
os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API key here")
```

The `getpass.getpass()` function should be used instead of calling `getpass` directly.

**Error Screenshot:**  

![Image](https://github.com/user-attachments/assets/12fb4845-aa33-45f6-8d44-4ddb6cbab543)

**URL:** [LangChain Documentation](https://python.langchain.com/docs/integrations/text_embedding/google_generative_ai/)

### Idea or request for content:

_No response_

## Comments

**dosubot[bot]:**
Hi, @jasminaaa20. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- The issue highlights a documentation error related to Google Generative AI Embedding.
- The error involves the incorrect use of the `getpass` module, leading to a `TypeError`.
- You provided the corrected code and a screenshot to illustrate the issue.
- No further comments or activities have been made on this issue.

**Next Steps:**
- Please confirm if this issue is still relevant to the latest version of the LangChain repository. If so, you can keep the discussion open by commenting here.
- If there is no response, the issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
