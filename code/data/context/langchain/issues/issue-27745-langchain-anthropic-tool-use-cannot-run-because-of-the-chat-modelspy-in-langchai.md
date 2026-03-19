# langchain_anthropic tool use cannot run because of the chat_models.py in langchain_anthropic  has problem with  "args": event.delta.partial_json, and   "stop_reason": event.delta.stop_reason

**Issue #27745** | State: closed | Created: 2024-10-30 | Updated: 2026-03-06
**Author:** LaiosOvO
**Labels:** bug, investigate

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import (
    AgentExecutor,
    create_react_agent,
)
from langchain_core.tools import Tool

# Load environment variables from .env file
load_dotenv()


# Define a very simple tool function that returns the current time
def get_current_time(*args, **kwargs):
    """Returns the current time in H:MM AM/PM format."""
    import datetime  # Import datetime module to get current time

    now = datetime.datetime.now()  # Get current time
    return now.strftime("%I:%M %p")  # Format time in H:MM AM/PM format

def get_user_name(*args, **kwargs):
    return "laios"

# List of tools available to the agent
tools = [
    Tool(
        name="Time",  # Name of the tool
        func=get_current_time,  # Function that the tool will execute
        # Description of the tool
        description="Useful for when you need to know the current time",
    ),
]

# Pull the prompt template from the hub
# ReAct = Reason and Action
# https://smith.langchain.com/hub/hwchase17/react
prompt = hub.pull("hwchase17/react")

# Initialize a ChatAnthropic model
from langchain_anthropic import ChatAnthropic
ANTHROPIC_API_KEY="sk-ZmdryaQOkdidlKX9hIvOEi4daloVTSmxRtwfVft0pPn9hy3k"
model="claude-3-5-sonnet-20241022"
llm = ChatAnthropic(model=model , api_key =  ANTHROPIC_API_KEY)

# Create the ReAct agent using the create_react_agent function
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
    stop_sequence=True,
)

# Create an agent executor from the agent and tools
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
)

# Run the agent with a test query
response = agent_executor.invoke({"input": "What time is it?"})

# Print the response from the agent
print("response:", response)

“”“
can not pass the simple tool use demo of agent_executor in langchain_anthropic  .
the chat_models.py in langchain_anthropic  has problem with  "args": event.delta.partial_json, and   "stop_reason": event.delta.stop_reason.
code 1223 and code 1235.
”“”

### Error Message and Stack Trace (if applicable)

Traceback (most recent call last):
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\5_agents_and_tools\1_agent_and_tools_basics.py", line 68, in 
    response = agent_executor.invoke({"input": "What time is it?"})
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\chains\base.py", line 170, in invoke
    raise e
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\chains\base.py", line 160, in invoke
    self._call(inputs, run_manager=run_manager)
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\agents\agent.py", line 1629, in _call
    next_step_output = self._take_next_step(
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\agents\agent.py", line 1335, in _take_next_step
    [
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\agents\agent.py", line 1335, in 
    [
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\agents\agent.py", line 1363, in _iter_next_step
    output = self._action_agent.plan(
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain\agents\agent.py", line 464, in plan
    for chunk in self.runnable.stream(inputs, config={"callbacks": callbacks}):
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 3407, in stream
    yield from self.transform(iter([input]), config, **kwargs)
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 3394, in transform
    yield from self._transform_stream_with_config(
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 2197, in _transform_stream_with_config
    chunk: Output = context.run(next, iterator)  # type: ignore
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 3357, in _transform
    yield from final_pipeline
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 1413, in transform
    for ichunk in input:
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 5561, in transform
    yield from self.bound.transform(
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\runnables\base.py", line 1431, in transform
    yield from self.stream(final, config, **kwargs)
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\language_models\chat_models.py", line 420, in stream
    raise e
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_core\language_models\chat_models.py", line 400, in stream
    for chunk in self._stream(messages, stop=stop, **kwargs):
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_anthropic\chat_models.py", line 716, in _stream
    msg = _make_message_chunk_from_anthropic_event(
  File "D:\.workspace\web3\0camp\hackston\ai\tutorial\langchain-crash-course\langchain-demo\lib\site-packages\langchain_anthropic\chat_models.py", line 1235, in _make_message_chunk_from_anthropic_event
    "stop_reason": event.delta.stop_reason,
AttributeError: 'NoneType' object has no attribute 'stop_reason'

### Description

can not pass the simple tool use demo of agent_executor in langchain_anthropic.
the chat_models.py in langchain_anthropic  has problem with  "args": event.delta.partial_json, and   "stop_reason": event.delta.stop_reason.
code 1223 and code 1235.

when you called this code
response = agent_executor.invoke({"input": "What time is it?"})
finally they will goto the _make_message_chunk_from_anthropic_event() in models.py and  event.delta.partial_json donot have partial_json ;and event.delta is None.

please check it.

### System Info

win10
pycharm

requirements.txt
langchain-openai>=0.2.2
langchain_ollama>=0.2.0
python-dotenv>=1.0.1
langchain>=0.3.0
langchain-community>=0.3.0
langchain-anthropic>=0.2.0
langchain-google-genai>=1.1.0
langchain-google-firestore>=0.3.1
firestore>=0.0.8
chromadb>=0.5.15
tiktoken>=0.8.0
sentence-transformers>=3.1.0
bs4>=0.0.2
firecrawl-py>=0.0.14
langchainhub>=0.1.21
wikipedia>=1.4.0
tavily-python>=0.3.4
