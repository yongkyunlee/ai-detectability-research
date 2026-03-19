# unable to pass ToolNode to createAgent() in tools parameter

**Issue #35824** | State: closed | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** VarinThakur01
**Labels:** bug, core, langchain, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [x] langchain
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
tool_node = ToolNode([sample_tool_1], handle_tool_errors=True)

agent = create_agent(
    model=llm,
    tools= tool_node,
    system_prompt=system_prompt
)
```

### Error Message and Stack Trace (if applicable)

```shell
tool_node = ToolNode([extract_ontology, query_rdf_graph], handle_tool_errors=True)
---> 83 agent = create_agent(
     84     model=llm,
     85     tools= tool_node,
     86     system_prompt=system_prompt
     87 )

create_agent(model, tools, system_prompt, middleware, response_format, state_schema, context_schema, checkpointer, store, interrupt_before, interrupt_after, debug, name, cache)
    880 tool_node: ToolNode | None = None
    881 # Extract built-in provider tools (dict format) and regular tools (BaseTool/callables)
--> 882 built_in_tools = [t for t in tools if isinstance(t, dict)]
    883 regular_tools = [t for t in tools if not isinstance(t, dict)]
    885 # Tools that require client-side execution (must be in ToolNode)

TypeError: 'ToolNode' object is not iterable
```

### Description

I am trying to use langchain react agent to with tools.
I want the error messages to be propagated to the LLM model, I saw tutorials where a ToolNode object can be passed to the create_agent() function.
https://github.com/laxmimerit/Langchain-v1-Agents/blob/main/code_notebooks/05_tool_configurations.ipynb
But when I do that, it throws an error.

If the API is updated, to now not allow ToolNode values inside the tools parameter, please update the documentation to show that.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Tue Feb 3 10:43:24 UTC 2026 (e548905)
> Python Version:  3.13.0 (main, Sep  5 2025, 20:17:57) [GCC 7.5.0]

Package Information
-------------------
> langchain_core: 1.2.13
> langchain: 1.2.10
> langchain_community: 0.4.1
> langsmith: 0.7.4
> langchain_aws: 1.1.0
> langchain_classic: 1.0.1
> langchain_google_genai: 4.2.0
> langchain_google_vertexai: 2.1.1
> langchain_hana: 1.0.2
> langchain_openai: 1.1.7
> langchain_text_splitters: 1.1.0
> langgraph_sdk: 0.3.6

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.13.1
> beautifulsoup4: 4.14.3
> boto3: 1.40.61
> bottleneck: 1.6.0
> dataclasses-json: 0.6.7
> filetype: 1.2.0
> google-cloud-aiplatform: 1.113.0
> google-cloud-storage: 2.19.0
> google-genai: 1.60.0
> hdbcli: 2.27.23
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.8
> numexpr: 2.14.1
> numpy: 2.4.2
> openai: 2.6.0
> orjson: 3.11.7
> packaging: 26.0
> pyarrow: 21.0.0
> pydantic: 2.12.5
> pydantic-settings: 2.11.0
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> rdflib: 7.6.0
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.46
> sqlalchemy: 2.0.46
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> validators: 0.35.0
> wrapt: 1.17.3
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**rawathemant246:**
Hi, thanks for the report!                                                                                         
                                                                                                                       
  This is actually expected behavior — create_agent() does not accept a ToolNode as the tools parameter.             
                                                                                                                       
  The function signature expects a list of tools:                                                                    
                                                                                                                       
  tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]] | None                                             
                                                                                                                     
  create_agent() builds its own ToolNode internally from the tools list you provide                                    
  (https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/factory.py#L920-L928), so
  you don't need to create one yourself.                                                                               
                                                                                                                     
  Fix — pass the tools list directly:                                                                                  
                                                                                                                     
  agent = create_agent(                                                                                                
      model=llm,                                                                                                       
      tools=[sample_tool_1],                                                                                         
      system_prompt=system_prompt,                                                                                     
  )                                                                                                                  
                                                                                                                       
  If you need handle_tool_errors=True behavior, you can handle tool errors within the tool itself (e.g., try/except and
   return an error string), or build the graph manually using LangGraph's lower-level APIs where you can pass a        
  ToolNode directly.                                                                                                   
                                                                                                                     
  The tutorial you referenced likely uses an older or different API. Hope this helps!

**VarinThakur01:**
> Hi, thanks for the report!
> 
> This is actually expected behavior — create_agent() does not accept a ToolNode as the tools parameter.
> 
> The function signature expects a list of tools:
> 
> tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]] | None
> 
> create_agent() builds its own ToolNode internally from the tools list you provide (https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/factory.py#L920-L928), so you don't need to create one yourself.
> 
> Fix — pass the tools list directly:
> 
> agent = create_agent( model=llm, tools=[sample_tool_1], system_prompt=system_prompt, )
> 
> If you need handle_tool_errors=True behavior, you can handle tool errors within the tool itself (e.g., try/except and return an error string), or build the graph manually using LangGraph's lower-level APIs where you can pass a ToolNode directly.
> 
> The tutorial you referenced likely uses an older or different API. Hope this helps!

The older API supported this? Can this be reflected in the documentation?
```text
Note: Since v1.x the API for create_agent() doesn't accept a ToolNode() as an argument for the parameter tools. 
```

**ccurme:**
`create_agent` was new in 1.0, it never accepted ToolNode. `langgraph.prebuilt.create_react_agent` did accept ToolNode. The migration guide for 1.0 mentions this here: https://docs.langchain.com/oss/python/migrate/langchain-v1#tools

**VarinThakur01:**
Thanks for the info!
