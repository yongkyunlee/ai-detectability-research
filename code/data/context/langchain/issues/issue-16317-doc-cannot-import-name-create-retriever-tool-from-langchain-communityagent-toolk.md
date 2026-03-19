# DOC: cannot import name 'create_retriever_tool' from 'langchain_community.agent_toolkits'

**Issue #16317** | State: closed | Created: 2024-01-20 | Updated: 2026-03-06
**Author:** weibangpeng

### Issue with current documentation:

In the LangChain documentation about SQL use cases, there seems to be an error with the import statement. The class 'create_retriever_tool' does not exist as specified. According to my understanding, the proper usage might require specifying extra_tools as a parameter when calling create_sql_agent, which should accept a sequence of BaseTool objects.


### Idea or request for content:

_No response_

## Comments

**dosubot[bot]:**
_🤖_

Hey @weibangpeng! Good to see you around here again. I hope you're doing well! Let's dive right in and see what's up with this issue.

Thank you for bringing this to our attention. You are correct, the 'create_retriever_tool' should be used in conjunction with the 'extra_tools' parameter when calling 'create_sql_agent'. This parameter should accept a sequence of BaseTool objects.

Here is an example of how to use it:

```python
from langchain_community.agent_toolkits import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever, name="sql_get_similar_examples", description=tool_description
)
custom_tool_list = [retriever_tool]

from langchain.agents import AgentType, create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

db = SQLDatabase.from_uri("sqlite:///Chinook.db")
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    extra_tools=custom_tool_list,
    suffix=custom_suffix,
)
```

The 'create_retriever_tool' function in the LangChain codebase is used to create a tool for retrieving documents. It takes three arguments: a retriever, a name, and a description. The 'retriever' argument is an instance of the BaseRetriever class, which is used for the retrieval of documents. The 'name' argument is a string that represents the name of the tool. This name will be passed to the language model, so it should be unique and somewhat descriptive. The 'description' argument is a string that provides a description for the tool. This description will also be passed to the language model, so it should be descriptive.

You can find more details in the [LangChain documentation](https://github.com/langchain-ai/langchain/blob/master/docs/docs/use_cases/qa_structured/sql.ipynb) and the [LangChain codebase](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/tools/retriever.py).

I hope this helps! If you have any other questions, feel free to ask.

Best,
[Dosu](https://dosu.dev)

## Sources
- [docs/docs/use_cases/qa_structured/sql.ipynb](https://github.com/langchain-ai/langchain/blob/master/docs/docs/use_cases/qa_structured/sql.ipynb)
- [libs/langchain/langchain/tools/retriever.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/tools/retriever.py)

---

This response is meant to be useful and save you time. It is **not meant to be a precise solution**, but rather a starting point for your own research.

Help me be more useful! Please leave a 👍 if this is helpful and 👎 if it is irrelevant.

If you want to continue the conversation, start your reply with @dosu-bot.

**Lokeshwar-V:**
@dosu-bot you just copy pasted the documentation , which did not work. please give proper answer if you know.

**Lokeshwar-V:**
@weibangpeng facing the same issue, if you have the answer post here. I think the problem is with langchain end , few weeks before they changed many imports and deleted some document pages.

**sankar-forrester:**
I faced the same issue. I was able to copy the code from https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/tools/retriever.py and got it to work. for now.  (meaning not getting compile error) seems to be working as expected. @Lokeshwar-V

**ManishKanaparthi:**
use this:
from langchain_core.tools import create_retriever_tool
