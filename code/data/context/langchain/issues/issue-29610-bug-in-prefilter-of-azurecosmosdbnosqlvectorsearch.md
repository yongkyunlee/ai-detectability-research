# Bug in PreFilter of AzureCosmosDBNoSqlVectorSearch

**Issue #29610** | State: closed | Created: 2025-02-05 | Updated: 2026-03-08
**Author:** jesusfbes
**Labels:** bug, investigate, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python

from langchain_community.vectorstores.azure_cosmos_db_no_sql import (
    AzureCosmosDBNoSqlVectorSearch,
    Condition,
    PreFilter,
)

# instantiate the vector_store as needed for instance:
# vector_store = AzureCosmosDBNoSqlVectorSearch.from_texts( ...)

dict_condition = {"property": "metadata.page_number", "operator":"$eq", "value": 1}   
condition = Condition(**dict_condition)
pre_filter = PreFilter(conditions = [condition],logical_operator="$and")
query = "look for some info in document"
vector_store.similarity_search(query=query, k=100, pre_filter= pre_filter)
``` 

### Error Message and Stack Trace (if applicable)

 Failed to retrieve documents from DB: local variable 'value' referenced before assignment

### Description

I am testing the pre_filter capability of Azure CosmosDB NoSQL and I think that there is a bug around line  792 of 

```python
                sql_operator = operator_map[condition.operator]
                if isinstance(condition.value, str):
                    value = f"'{condition.value}'"
                elif isinstance(condition.value, list):
                    # e.g., for IN clauses
                    value = f"({', '.join(map(str, condition.value))})"
                clauses.append(f"c.{condition.property} {sql_operator} {value}")
```

In this snippet the filtering condition is converted in a where clause. The cases when `condition.value` is a str or list are treated as exceptions. However when it is for example an int, the correct value is not used in the condition. It used previously defined `value` that can be undefined if that condition if the first one.

 

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Tue Nov 5 00:21:55 UTC 2024
> Python Version:  3.9.20 (main, Oct 16 2024, 04:36:33) 
[Clang 18.1.8 ]

Package Information
-------------------
> langchain_core: 0.3.29
> langchain: 0.3.14
> langchain_community: 0.3.14
> langsmith: 0.2.10
> langchain_chroma: 0.2.0
> langchain_cohere: 0.3.4
> langchain_experimental: 0.3.4
> langchain_google_genai: 2.0.8
> langchain_openai: 0.3.0
> langchain_text_splitters: 0.3.5

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.11.11
> async-timeout: 4.0.3
> chromadb: 0.5.20
> cohere: 5.13.8
> dataclasses-json: 0.6.7
> fastapi: 0.115.6
> filetype: 1.2.0
> google-generativeai: 0.8.3
> httpx: 0.28.1
> httpx-sse: 0.4.0
> jsonpatch: 1.33
> langsmith-pyo3: Installed. No version info available.
> numpy: 1.26.4
> openai: 1.59.7
> orjson: 3.10.14
> packaging: 24.2
> pandas: 2.2.3
> pydantic: 2.10.5
> pydantic-settings: 2.7.1
> PyYAML: 6.0.2
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.37
> tabulate: 0.9.0
> tenacity: 9.0.0
> tiktoken: 0.8.0
> typing-extensions: 4.12.2
> zstandard: Installed. No version info available.
