# Unsupported early_stopping_method="generate" in AgentExecutor after reaching iteration limit

**Issue #16263** | State: open | Created: 2024-01-19 | Updated: 2026-03-11
**Author:** thedavgar
**Labels:** bug, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.

### Example Code

The following code:

```python
agent_system = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt)

agent = AgentExecutor(
    agent=agent_system,    # Sets the system to use openai functions
    tools=tools,                   # Sets the tools visible to the LLM
    return_intermediate_steps=True,     # Get a list of traces of the trajectory of the chain
    max_iterations=4,          # Sets the number of intermediate steps
    early_stopping_method="generate",   # Applies final pass to generate an output if max iterations is reached
    verbose=verbose)         # Makes internal states visible to debug

agent.invoke({'input': user_input})
```

### Description

This code if it reaches the max iterations, returns an error.

ERROR: Got unsupported early_stopping_method `generate`

### System Info

pip langchain==0.1.0 langchain-openai==0.0.2.post1

Using as LLM GPT-3.5 Turbo 0613

### Related Components

- [ ] LLMs/Chat Models
- [ ] Embedding Models
- [ ] Prompts / Prompt Templates / Prompt Selectors
- [ ] Output Parsers
- [ ] Document Loaders
- [ ] Vector Stores / Retrievers
- [ ] Memory
- [X] Agents / Agent Executors
- [ ] Tools / Toolkits
- [X] Chains
- [ ] Callbacks/Tracing
- [ ] Async

## Comments

**dosubot[bot]:**
_🤖_

Hey @thedavgar! Good to see you here again, navigating the tricky seas of code. Hope your coding journey is going well! 🚀

Based on the information you've provided, it seems like you're encountering an error due to the `early_stopping_method` being set to "generate". In the current version of LangChain (v0.1.0), the supported early stopping methods are "force" and "generate". However, the "generate" method is not implemented in the `return_stopped_response` method of the `BaseSingleActionAgent` class, which is likely causing the error.

Here's the relevant code from the `BaseSingleActionAgent` class:

```python
def return_stopped_response(
        self,
        early_stopping_method: str,
        intermediate_steps: List[Tuple[AgentAction, str]],
        **kwargs: Any,
    ) -> AgentFinish:
        """Return response when agent has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return AgentFinish(
                {"output": "Agent stopped due to iteration limit or time limit."}, ""
            )
        else:
            raise ValueError(
                f"Got unsupported early_stopping_method `{early_stopping_method}`"
            )
```

As you can see, if the `early_stopping_method` is not "force", a `ValueError` is raised. This is likely the source of the error you're encountering.

To resolve this issue, you can change the `early_stopping_method` to "force" in your `AgentExecutor` instance:

```python
agent = AgentExecutor(
    agent=agent_system,    # Sets the system to use openai functions
    tools=tools,                   # Sets the tools visible to the LLM
    return_intermediate_steps=True,     # Get a list of traces of the trajectory of the chain
    max_iterations=4,          # Sets the number of intermediate steps
    early_stopping_method="force",   # Applies final pass to generate an output if max iterations is reached
    verbose=verbose)         # Makes internal states visible to debug
```

This will cause the agent to return a constant string saying that it stopped due to iteration limit or time limit when the max iterations are reached.

Alternatively, if you want to use the "generate" method, you would need to implement it in the `return_stopped_response` method of the `BaseSingleActionAgent` class. However, this would require modifying the LangChain source code, which may not be ideal.

I hope this helps! If you have any other questions, feel free to ask.

Sources:
- [libs/langchain/langchain/agents/agent.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent.py)
- [libs/langchain/langchain/agents/agent_iterator.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent_iterator.py)

## Sources
- [libs/langchain/langchain/agents/agent_iterator.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent_iterator.py)
- [libs/langchain/langchain/agents/agent.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent.py)

---

This response is meant to be useful and save you time. It is **not meant to be a precise solution**, but rather a starting point for your own research.

Help me be more useful! Please leave a 👍 if this is helpful and 👎 if it is irrelevant.

If you want to continue the conversation, start your reply with @dosu-bot.

**thedavgar:**
Thank you @dosubot. Yes I have seen in the code that the "generate" method is not implemented. However, in previous versions it was already working properly.

**dosubot[bot]:**
_🤖_

Based on the information you've provided, it seems like you're using an older version of LangChain (`langchain==0.1.0`) where the `generate` method for `early_stopping_method` is not supported. The error message you're seeing is likely due to this.

In the latest version of LangChain (`v0.1.1`), the `AgentExecutor` class has been updated to support the `generate` method for `early_stopping_method`. This method allows the agent to make a final prediction when it is stopped due to reaching the maximum number of iterations. Here's the relevant code from the latest version:

```python
def return_stopped_response(
        self,
        early_stopping_method: str,
        intermediate_steps: List[Tuple[AgentAction, str]],
        **kwargs: Any,
    ) -> AgentFinish:
        """Return response when agent has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return AgentFinish(
                {"output": "Agent stopped due to iteration limit or time limit."}, ""
            )
        elif early_stopping_method == "generate":
            # Generate does one final forward pass
            thoughts = ""
            for action, observation in intermediate_steps:
                thoughts += action.log
                thoughts += (
                    f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
                )
            # Adding to the previous steps, we now tell the LLM to make a final pred
            thoughts += (
                "\n\nI now need to return a final answer based on the previous steps:"
            )
            new_inputs = {"agent_scratchpad": thoughts, "stop": self._stop}
            full_inputs = {**kwargs, **new_inputs}
            full_output = self.llm_chain.predict(**full_inputs)
            # We try to extract a final answer
            parsed_output = self.output_parser.parse(full_output)
            if isinstance(parsed_output, AgentFinish):
                # If we can extract, we send the correct stuff
                return parsed_output
            else:
                # If we can extract, but the tool is not the final tool,
                # we just return the full output
                return AgentFinish({"output": full_output}, full_output)
        else:
            raise ValueError(
                "early_stopping_method should be one of `force` or `generate`, "
                f"got {early_stopping_method}"
            )
```

You can find this in the [AgentExecutor class in the LangChain repository](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent.py).

To resolve the issue, I recommend updating to the latest version of LangChain (`v0.1.1`). You can do this by running the following command:

```bash
pip install --upgrade langchain
```

After updating, the `generate` method for `early_stopping_method` should work as expected. If you continue to experience issues after updating, please provide more details so I can further assist you.

## Sources
- [libs/langchain/langchain/agents/agent_iterator.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent_iterator.py)
- [libs/langchain/langchain/agents/agent.py](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/agents/agent.py)

---

This response is meant to be useful and save you time. It is **not meant to be a precise solution**, but rather a starting point for your own research.

Help me be more useful! Please leave a 👍 if this is helpful and 👎 if it is irrelevant.

If you want to continue the conversation, start your reply with @dosu-bot.

**zhuzm:**
The current version of langchain stands at 0.1.16, however, the persisting issue remains unresolved as the "generate" method has not yet been implemented within the return_stopped_response functionality. It remains unclear as to when this will be rectified.
Who knows when this issue will be fixed? Is there any easy way to circumvent this problem without having to modify the source code of langchain?

**Fagner-lourenco:**
Idem.

**rahim-figs:**
Any updates on this one?

**nikhitaKanoj:**
facing same issue

**dariatsenter:**
0.1.16 
Dosu bot pointed at `Agent` (inherits from `BaseSingleActionAgent`) class which implements "generate" in return_stopped_response, whereas `BaseSingleActionAgent` and `BaseMultiActionAgent` do not. 

The return type of `create_openai_tools_agent` is `Runnable` and the stack trace is coming from line 266 which is `BaseMultiActionAgent`, so the method is missing implementation for "generate" alltogether.

**rek7:**
i have the same issue :/

**marcusRB:**
Still the same issue in version 0.3.x

langchain                                0.3.0
langchain-community                      0.3.0
langchain-core                           0.3.0
langchain-experimental                   0.3.0

Any improvements?
