# sql_agent demo Action and Final Answer appear together to cause an exception

**Issue #28818** | State: closed | Created: 2024-12-19 | Updated: 2026-03-06
**Author:** reatang
**Labels:** bug, investigate

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
# llm = ChatOpenAI()

db = SQLDatabase.from_uri("sqlite:///../somedb/db.sqlite")

agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    verbose=True,
)
agent_executor.handle_parsing_errors=True

resp = agent_executor.invoke("查询三分球命中率最高的球员")
print(resp)

```

### Error Message and Stack Trace (if applicable)

langsmith:

https://smith.langchain.com/public/e8196299-7b02-4314-a38e-bbae8f2f857e/r

### Description

I am using sql_agent at an example time, when the agent is currently running, it is not possible to run the program.

My current LLM analysis calculation time is likely to be a hit. `includes_answer = FINAL_ANSWER_ACTION in text` Use `includes_answer == True` ,then the result is `FINAL_ANSWER_AND_PARSABLE_ACTION_ERROR_MESSAGE`

### System Info

look  langsmith

## Comments

**keenborder786:**
Can you try the following:

```python


from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain_openai.chat_models import ChatOpenAI
llm = ChatOpenAI(model="gpt-4")
db = SQLDatabase.from_uri("sqlite:///Chinook.db")
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    verbose=True,
    agent_executor_kwargs={
        "handle_parsing_errors": True
    }
)
resp = agent_executor.invoke("How many customers are only?")
print(resp)
```

**reatang:**
yes, i am try.

https://smith.langchain.com/public/971bc360-8f64-4bd3-a020-b512bfe199aa/r

I think it may be the problem with the prompt words, Make `Action` and `Final Answer` appear in the same answer.

ReActSingleInputOutputParser@parse

![image](https://github.com/user-attachments/assets/a0626e4a-9576-4498-856c-019adc8fea30)

**dosubot[bot]:**
Hi, @reatang. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- You reported an exception in LangChain's `sql_agent` when "Action" and "Final Answer" appear together in the output.
- The issue persists even after updating to the latest version, indicating a potential parsing error.
- @keenborder786 suggested a code snippet to handle parsing errors.
- You suspect the issue might be related to the prompt structure causing both terms to appear simultaneously.

**Next Steps**
- Could you please confirm if this issue is still relevant with the latest version of the LangChain repository? If so, feel free to comment and keep the discussion open.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
