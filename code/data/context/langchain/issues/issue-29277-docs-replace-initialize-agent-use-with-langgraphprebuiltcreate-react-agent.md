# docs: Replace `initialize_agent` use with langgraph.prebuilt.create_react_agent

**Issue #29277** | State: closed | Created: 2025-01-17 | Updated: 2026-03-04
**Author:** efriis
**Labels:** documentation, help wanted, external

### Privileged issue

- [x] I am a LangChain maintainer, or was asked directly by a LangChain maintainer to create an issue here.

### Issue Content

Currently there's a bunch of tools and other integrations that use `initialize_agent` in their docs page (search langchain/docs for "initialize_agent")

This function has been deprecated since 0.1 and should be replaced with basic langgraph usage as a demo

Deprecated function: https://python.langchain.com/api_reference/langchain/agents/langchain.agents.initialize.initialize_agent.html

Example page using create_react_agent in an example: https://python.langchain.com/docs/integrations/tools/gmail/#use-within-an-agent

This issue doesn't need to be resolved by a single PR and can be tackled incrementally! Just tag this issue for tracking purposes :)

## Comments

**aybdee:**
I want to try working on this

**Thejaswi05:**
@efriis do you expect the changes in the documentation for the tools and integrations using `initialize_agent'  listed at the bottom of the page you shared? 

Such as: 
[AINetwork Toolkit](https://python.langchain.com/docs/integrations/tools/ainetwork/)

[AWS Lambda](https://python.langchain.com/docs/integrations/tools/awslambda/)

**turboslapper:**
Hi everyone,  

I’ve partially updated the documentation to replace deprecated references to `initialize_agent` with `langgraph.prebuilt.create_react_agent`. Specifically:  

- I addressed the instances for **page 1 of 3** in the search:  
  **`repo:langchain-ai/langchain path:/^docs\// initialize_agent`**.  
- I plan to work on pages 2 and 3 shortly to complete the updates.  

Additionally, I noticed a recurring pattern in examples, such as:  
```python
agent.run("what is google's stock")
```

This doesn't inherently print the output of the agent.run command, and I considered adding something like:

```python
response = agent.run("what is google's stock")
print(response)
```

to improve clarity for users. However, as this is my first commit, I didn’t want to overstep the scope without further guidance. Let me know if you’d like me to include such improvements!

Looking forward to completing the remaining pages soon.

**AffanShaikhsurab:**
If no one is working on this issue , can I work on this ?

**Yeonseolee:**
I noticed that some parts of the documentation still reference `initialize_agent`.  
Would it be alright if I take over and help with the remaining updates?

**rthummaluru:**
Hi! I’d like to update the EdenAI example in edenai_tools.ipynb to remove initialize_agent and use the recommended approach. Tagging this as part of #29277 and will send a PR shortly.

**ccurme:**
Hi all, please make sure that the code you update in the docs runs without error. Thank you!

**colichar:**
Hi, I'd like to contribute to this issue as well. As I understand it, there are still quite a few tools that still use the deprecated `initialize_agent`.  Should I just pick one page out to edit the docs that is not modified with existing PRs?

**tskrrish:**
Hi! I'd like to work on this issue. Please let me know if it's still available.

**Vahed-SK:**
Hi! I'd like to work on replacing `initialize_agent` with `create_react_agent` in the remaining documentation files. I will update the examples to reflect the new recommended usage. Let me know if that's good to proceed!
