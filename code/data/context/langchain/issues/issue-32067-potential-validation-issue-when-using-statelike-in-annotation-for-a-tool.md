# Potential validation issue when using `StateLike` in `Annotation` for a tool

**Issue #32067** | State: open | Created: 2025-07-16 | Updated: 2026-03-04
**Author:** eyurtsev
**Labels:** help wanted, internal

### Privileged issue

- [x] I am a LangChain maintainer, or was asked directly by a LangChain maintainer to create an issue here.

### Issue Content

This code snippet triggers a validation issue. Likely issue in how langchain_core is using Pydantic for the run time validation.

```python
    from langgraph.typing import StateLike

    @tool(name, description=description)
    def handoff_to_agent(
        # Annotation is typed as Any instead of StateLike. StateLike 
        # trigger validation issues from Pydantic / langchain_core interaction.
        state: Annotated[StateLike, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:

```

Stack trace:

```
    def create_schema_validator(
        schema: CoreSchema,
        schema_type: Any,
        schema_type_module: str,
        schema_type_name: str,
        schema_kind: SchemaKind,
        config: CoreConfig | None = None,
        plugin_settings: dict[str, Any] | None = None,
    ) -> SchemaValidator | PluggableSchemaValidator:
        """Create a `SchemaValidator` or `PluggableSchemaValidator` if plugins are installed.
    
        Returns:
            If plugins are installed then return `PluggableSchemaValidator`, otherwise return `SchemaValidator`.
        """
        from . import SchemaTypePath
        from ._loader import get_plugins
    
        plugins = get_plugins()
        if plugins:
            return PluggableSchemaValidator(
                schema,
                schema_type,
                SchemaTypePath(schema_type_module, schema_type_name),
                schema_kind,
                config,
                plugins,
                plugin_settings or {},
            )
        else:
>           return SchemaValidator(schema, config)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           pydantic_core._pydantic_core.SchemaError: Error building "model" validator:
E             SchemaError: Error building "model-fields" validator:
E             SchemaError: Field "state":
E             SchemaError: Error building "union" validator:
E             SchemaError: Error building "is-instance" validator:
E             SchemaError: 'cls' must be valid as the first argument to 'isinstance'

```

Workaround:

For now implementation will rely on an Any type

## Comments

**ArjunJagdale:**
@eyurtsev SO, Pydantic cannot validate StateLike because it’s not a real class -- Correct me if i am wrong.
Will the minimal way we can consider is -
Use `arbitrary_types_allowed=True` in the model config for `StateLike`, or Implement a custom `Pydantic` validator that checks the expected structure of `StateLike`.

**SanjanaB123:**
Hi @eyurtsev , I'd like to work on this! My approach would be to look at how langchain_core builds the tool input schema and see if fields annotated with InjectedState can be excluded from Pydantic validation entirely, since they're injected at runtime rather than user-provided. Does that direction sound right to you? Happy to discuss before submitting a PR.
