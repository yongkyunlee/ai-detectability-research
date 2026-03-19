# The Qdrant Vector Store, for filtering is not using the right imports.

**Issue #28012** | State: closed | Created: 2024-11-10 | Updated: 2026-03-06
**Author:** andresnatanael

### URL

https://python.langchain.com/docs/integrations/vectorstores/qdrant/

### Checklist

- [X] I added a very descriptive title to this issue.
- [X] I included a link to the documentation page I am referring to (if applicable).

### Issue with current documentation:

The code https://github.com/langchain-ai/langchain/blob/master/docs/docs/integrations/vectorstores/qdrant.ipynb

```python
from qdrant_client.http import models

results = vector_store.similarity_search(
    query="Who are the best soccer players in the world?",
    k=1,
    filter=models.Filter(
        should=[
            models.FieldCondition(
                key="page_content",
                match=models.MatchValue(
                    value="The top 10 soccer players in the world right now."
                ),
            ),
        ]
    ),
)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
```

Uses a wrong import the right is: 

from qdrant_client import models

```python
from qdrant_client import models

results = vector_store.similarity_search(
    query="Who are the best soccer players in the world?",
    k=1,
    filter=models.Filter(
        should=[
            models.FieldCondition(
                key="page_content",
                match=models.MatchValue(
                    value="The top 10 soccer players in the world right now."
                ),
            ),
        ]
    ),
)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")
```

Source:

https://qdrant.tech/documentation/concepts/filtering/



### Idea or request for content:

Please update the import since I changed with the one used in the Qdrant documentation the metadata filtering started working fine.

Source File: https://github.com/langchain-ai/langchain/blob/master/docs/docs/integrations/vectorstores/qdrant.ipynb

## Comments

**ZhangShenao:**
Try to fix it in #28286

**dosubot[bot]:**
Hi, @andresnatanael. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- The issue highlights an incorrect import statement in the Qdrant Vector Store documentation.
- The import should be updated from `from qdrant_client.http import models` to `from qdrant_client import models`.
- @ZhangShenao has submitted pull request #28286 to address this issue.

**Next Steps**
- Please confirm if this issue is still relevant to the latest version of the LangChain repository by commenting here.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
