# GoogleSearchAPIWrapper：TimeoutError[WinError 10060]

**Issue #29038** | State: closed | Created: 2025-01-06 | Updated: 2026-03-06
**Author:** SetonLiang
**Labels:** external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
os.environ["GOOGLE_CSE_ID"] = "" # Your Google CSE ID
os.environ["GOOGLE_API_KEY"] = ""
search = GoogleSearchAPIWrapper()

tool = Tool(
    name="google_search",
    description="Search Google for recent results.",
    func=search.run,
)

result = tool.run("Obama's first name?")
print(result)

```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

I want to call the Google Search API, and successfully run this website:
https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CX&q=SEARCH_QUERY

However, when I use the GoogleSearchAPIWrapper with the key and cx_id, it will generate an error: TimeoutError: [WinError 10060]

### System Info

pip install google-api-python-client >=2.100.0

## Comments

**dosubot[bot]:**
Hi, @SetonLiang. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- Encountering `TimeoutError [WinError 10060]` with `GoogleSearchAPIWrapper`.
- Direct access to the Google Search API via browser works fine.
- Issue persists even after updating to the latest LangChain version.
- No further comments or developments have been made.

**Next Steps**
- Is this issue still relevant with the latest version of LangChain? If so, please comment to keep the discussion open.
- Otherwise, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
