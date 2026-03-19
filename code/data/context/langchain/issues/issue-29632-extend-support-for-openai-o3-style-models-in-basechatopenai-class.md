# Extend support for OpenAI o3 style models in BaseChatOpenAI class

**Issue #29632** | State: closed | Created: 2025-02-06 | Updated: 2026-03-08
**Author:** zachschillaci27
**Labels:** bug, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

NA

### Error Message and Stack Trace (if applicable)

_No response_

### Description

The `BaseChatOpenAI` class of `langchain_openai` contains some hard-coded references to the `o1` model, such as the one below:
```
    @model_validator(mode="before")
    @classmethod
    def validate_temperature(cls, values: Dict[str, Any]) -> Any:
        """Currently o1 models only allow temperature=1."""
        model = values.get("model_name") or values.get("model") or ""
        if model.startswith("o1") and "temperature" not in values:
            values["temperature"] = 1
        return values
```
taken from https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/chat_models/base.py#L558.

These need to be extended to support the `o3` series of models - namely `o3-mini` for now. Perhaps using `model.startswith("o")` is a good enough patch for now, but something more future-proof may want to be considered.

### System Info

I took the references directly from langchain's master branch on GitHub

## Comments

**ccurme:**
`validate_temperature` was added in langchain-openai ~0.2, which set a default temperature of 0.7. So `o1` would break with the default value.

langchain-openai ~0.3 updated this default to None. I don't run into any issues using `o1`, `o1-preview`, `o1-mini`, or `o3-mini`.

What is the motivation for extending this?

**zachschillaci27:**
> `validate_temperature` was added in langchain-openai ~0.2, which set a default temperature of 0.7. So `o1` would break with the default value.
> 
> langchain-openai ~0.3 updated this default to None. I don't run into any issues using `o1`, `o1-preview`, `o1-mini`, or `o3-mini`.
> 
> What is the motivation for extending this?

Thanks for the quick response! I can better understand the context now.

I personally find it a bit confusing that the patch only handles `o1`. It's still the case that `temperature` is not a valid parameter for `o3-mini`, unless it's set to 1:
```
BadRequestError: Error code: 400 - {'error': {'message': "Unsupported parameter: 'temperature' is not supported with this model.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_parameter'}}
```
I feel it would make sense to align the treatment for `o1` and `o3-mini` or remove the validation altogether

**helenadeus:**
Is there a resolution for this? It's getting pretty silly that we cannot use langchain / langflow with any of the reasoning models. openAI changed the API slightly with these models, it's likely that they will continuing doing so...

**ccurme:**
> Is there a resolution for this? It's getting pretty silly that we cannot use langchain / langflow with any of the reasoning models. openAI changed the API slightly with these models, it's likely that they will continuing doing so...

@helenadeus They are all supported. What version of `langchain-openai` are you using?

**nimrod29:**
I am encountering the same error mentioned above:
```
self.llm = ChatOpenAI(model="o3-mini", verbose=True, temperature=0.0)
```

```
BadRequestError('Error code: 400 - {\'error\': {\'message\': "Unsupported parameter: \'temperature\' is not supported with this model.", \'type\': \'invalid_request_error\', \'param\': \'temperature\', \'code\': \'unsupported_parameter\'}}')
```

When I remove the temperature parameter, I no longer receive an error, but the o3-mini model does not call any tools, even though it should. However, the gpt-4o model works as expected.

Using the o1 model without the temperature parameter:
```self.llm = ChatOpenAI(model="o1", verbose=True)```

While I don't receive any temperature-related errors, I encounter a different error after the first tool is called:
```
BadRequestError('Error code: 400 - {\'error\': {\'message\': "Unsupported value: \'messages[3].role\' does not support \'function\' with this model.", \'type\': \'invalid_request_error\', \'param\': \'messages[3].role\', \'code\': \'unsupported_value\'}}')
```

Btw these are the versions of langchain I am using:
```
langchain==0.3.19
langchain-community==0.3.18
langchain-core==0.3.40
langchain-openai==0.3.7
langchain-text-splitters==0.3.6
```

**ccurme:**
@nimrod29 can you please post a minimal reproducible example?

Here is one attempt, which confirms tool calling is supported with `o3-mini`.
```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return "It's sunny."

llm = ChatOpenAI(model="o3-mini").bind_tools([get_weather])
response = llm.invoke("What is the weather in San Francisco?")
assert response.tool_calls
```

For your second problem, if:
- Your version of `langchain-core` is up to date
- Your version of `langchain-openai` is up to date
- You are using `langchain-openai` and not `langchain-community` for the OpenAI integration

You should not be receiving FunctionMessage objects from a tool. Please post an example that would help someone debug.

**nimrod29:**
Hey, appreciate the response!

here is a minimal reproducible example with the way I am using the agents:

```python
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import MessagesPlaceholder

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return "It's sunny."

llm = ChatOpenAI(model="o3-mini", temperature=0.0)

# Create a prompt template for the Executor
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_openai_functions_agent(llm, [get_weather], prompt)

# The executor that can actually call the tools
agent_executor = AgentExecutor(
    agent=agent,
    tools=[get_weather],
    verbose=True,
    max_iterations=60,
    early_stopping_method="generate",
)

response = agent_executor.invoke(
    {"input": "What is the weather in San Francisco?", "chat_history": []}
)

print(response)
```

```python
openai.BadRequestError: Error code: 400 - {'error': {'message': "Unsupported parameter: 'temperature' is not supported with this model.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_parameter'}}
```

**satishgunasekaran:**
Any updates for this

**ccurme:**
@nimrod29 the error message indicates that temperature is not supported with this model, but you are providing it when you pass `temperature=0.0`. Can you omit the `temperature` kwarg and confirm it resolves your issue?

**lgibelli:**
> [@nimrod29](https://github.com/nimrod29) the error message indicates that temperature is not supported with this model, but you are providing it when you pass `temperature=0.0`. Can you omit the `temperature` kwarg and confirm it resolves your issue?

He already did that, so did I. The problem with calling tools remains though: 

`BadRequestError('Error code: 400 - {\'error\': {\'message\': "Unsupported value: \'messages[3].role\' does not support \'function\' with this model.", \'type\': \'invalid_request_error\', \'param\': \'messages[3].role\', \'code\': \'unsupported_value\'}}')
`
