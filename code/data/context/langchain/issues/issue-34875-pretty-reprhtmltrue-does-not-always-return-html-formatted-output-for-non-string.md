# pretty_repr(html=True) does not always return HTML-formatted output for non-string content

**Issue #34875** | State: open | Created: 2026-01-25 | Updated: 2026-03-18
**Author:** Alioth99
**Labels:** bug, core, external

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
- [x] langchain-core
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Reproduction Steps / Example Code (Python)

```python
from langchain_core.messages import BaseMessage

message = BaseMessage(
    content=["First", "Second", "Third"],
    type="ai",
    name="bot"
)

text = message.text()
print("text():", text)

html_repr = message.pretty_repr(html=True)
print("pretty_repr(html=True):", html_repr)
```

### Error Message and Stack Trace (if applicable)

```shell
text(): FirstSecondThird
pretty_repr(html=True): ================================== Ai Message ==================================
Name: bot

['First', 'Second', 'Third']
```

### Description

I am using `BaseMessage.pretty_repr(html=True)` and expect the output to be HTML-formatted, as stated in the docstring:

> *If `True`, the message will be formatted with HTML tags.*

However, when `content` is provided as a non-string type (e.g. `list[str]`, which is a valid and supported type for `BaseMessage.content`), the returned value is plain text and contains no HTML tags at all. Instead, the Python `repr` of the list is included in the output.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #148-Ubuntu SMP Fri Mar 14 19:05:48 UTC 2025
> Python Version:  3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]

Package Information
-------------------
> langchain_core: 0.3.68
> langchain: 0.3.26
> langsmith: 0.4.5
> langchain_text_splitters: 0.3.8

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> async-timeout=4.0.0;: Installed. No version info available.
> httpx: 0.28.1
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.51: Installed. No version info available.
> langchain-core=0.3.66: Installed. No version info available.
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
> langchain-text-splitters=0.3.8: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> langsmith>=0.3.45: Installed. No version info available.
> openai-agents: Installed. No version info available.
> opentelemetry-api: 1.36.0
> opentelemetry-exporter-otlp-proto-http: 1.36.0
> opentelemetry-sdk: 1.36.0
> orjson: 3.10.16
> packaging: 24.2
> packaging=23.2: Installed. No version info available.
> pydantic: 2.11.7
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.7.4: Installed. No version info available.
> pytest: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.4
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 14.1.0
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**Devpatel1901:**
Hey @Alioth99, If you look at their codebase then we can confirm two things:

1. According to them, the html=True flag is only used to make the title of a message type (in our case, type ai) appear bold. They append “Message” to the type name and then format it using the get_bolded_text function. You can observe the difference by removing the html argument — the title will no longer be bold. I believe the docstring means that the text will be HTML-compatible bold text displayed in the console, not actual HTML tags. Take a look at the code below for reference.
2. They haven’t added support for non-string content yet, as indicated by the TODO comment in the `pretty_repr` method. 

I believe they should update the docstring, as the current one is misleading.

```python

def get_bolded_text(text: str) -> str:
    """Get bolded text.

    Args:
        text: The text to bold.

    Returns:
        The bolded text.
    """
    return f"\033[1m{text}\033[0m"

def get_msg_title_repr(title: str, *, bold: bool = False) -> str:
    """Get a title representation for a message.

    Args:
        title: The title.
        bold: Whether to bold the title.

    Returns:
        The title representation.

    """
    padded = " " + title + " "
    sep_len = (80 - len(padded)) // 2
    sep = "=" * sep_len
    second_sep = sep + "=" if len(padded) % 2 else sep
    if bold:
        padded = get_bolded_text(padded)
    return f"{sep}{padded}{second_sep}"

def pretty_repr(
        self,
        html: bool = False,  # noqa: FBT001,FBT002
    ) -> str:
        """Get a pretty representation of the message.

        Args:
            html: Whether to format the message as HTML. If `True`, the message will be
                formatted with HTML tags.

        Returns:
            A pretty representation of the message.

        """
        title = get_msg_title_repr(self.type.title() + " Message", bold=html)
        # TODO: handle non-string content.
        if self.name is not None:
            title += f"\nName: {self.name}"
        return f"{title}\n\n{self.content}"
```

**RajGajjar-01:**
I want to work on that issue if possible. Any suggestions how can I ?
I am new to open source contributions and I want to do them to improve my skills and help code something real that people uses.

Thank you,
Raj Gajjar

**gitbalaji:**
Hi, I have an open PR (#35402) that fixes this issue. Could you please assign this to me? Happy to address any review feedback.
