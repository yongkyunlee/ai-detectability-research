# Add RunnableConfig Access in Agent Middleware Functions

**Issue #33726** | State: open | Created: 2025-10-29 | Updated: 2026-03-10
**Author:** beastrog
**Labels:** core, langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Feature Description

When using `create_agent` with middleware functions (specifically `before_model` hooks), developers cannot access the `RunnableConfig` object that was passed during agent invocation. This prevents implementing context-aware middleware behavior based on configuration parameters like metadata, tags, or custom settings.

### Current Limitation
```python
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig

def logging_middleware(runtime):
    # PROBLEM: Cannot access the RunnableConfig passed to agent.invoke()
    # Need: runtime.config or similar to access metadata, tags, etc.
    
    # Desired behavior:
    # config = runtime.config
    # if config.metadata.get("log_level") == "debug":
    #     enable_detailed_logging()
    pass

# Setup
agent = create_agent(llm=my_llm, tools=my_tools, middleware=[logging_middleware])

# The config here is invisible to middleware
config = RunnableConfig(metadata={"log_level": "debug", "user_id": "123"})
result = agent.invoke("Hello", config=config)

### Use Case

## **Use Case**
```markdown
I need to implement sophisticated middleware for production LangChain applications that requires context-aware behavior based on the configuration passed during agent invocation.

### Specific Use Cases:

1. **Context-Aware Logging**: Log different levels of detail based on `config.metadata.get("log_level")`
2. **User-Specific Behavior**: Implement different middleware logic based on `config.metadata.get("user_id")` or user roles
3. **Environment-Specific Processing**: Handle production vs development differently using `config.tags`
4. **Audit Trail**: Track operations with run names and metadata for compliance
5. **Conditional Security**: Apply different security measures based on config parameters

### Current Problem:
- Must use global state or external configuration management (bad practice)
- Cannot implement dynamic middleware behavior based on invocation context
- Limits the usefulness of middleware for advanced monitoring and debugging
- Forces workarounds that make code harder to maintain and test

### Business Impact:
This limitation prevents building production-ready LangChain applications that need sophisticated logging, monitoring, and conditional behavior in middleware layers.

### Example Production Use Case:
```python
def audit_middleware(runtime):
    config = runtime.config
    user_id = config.metadata.get("user_id")
    operation = config.metadata.get("operation")
    
    # Log to audit system
    audit_logger.info(f"User {user_id} performing {operation}", 
                     extra={"run_name": config.run_name, "tags": config.tags})
    
    return runtime

def security_middleware(runtime):
    config = runtime.config
    if "sensitive" in (config.tags or []):
        # Apply additional security measures
        enable_data_redaction()
    
    return runtime

## Comments

**sydney-runkle:**
yeah... we should probably add to runtime.

**aran-yogesh:**
@beastrog @sydney-runkle can i take this feature request

**aran-yogesh:**
@beastrog @sydney-runkle i have made the PR lmk if there is anything that needs to be added

**joy7758:**
Thanks for raising this. I've been experimenting with thin runtime-control adapters around `create_agent`, and the lack of `RunnableConfig` access inside middleware is a real limitation.

Budget-aware gating and compact post-run receipts often need per-invocation metadata, tags, or settings that only exist at invoke time.

A small way to read config from middleware would be much cleaner than pushing more of this into core agent state.

If useful, I'd be happy to help validate that against adapter-style middleware use cases.
