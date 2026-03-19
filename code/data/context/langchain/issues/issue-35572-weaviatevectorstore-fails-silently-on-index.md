# WeaviateVectorStore fails silently on index

**Issue #35572** | State: open | Created: 2026-03-05 | Updated: 2026-03-09
**Author:** xQsM3
**Labels:** bug, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
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
def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        tenant: Optional[str] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Upload texts with metadata (properties) to Weaviate."""
        from weaviate.util import get_valid_uuid  # type: ignore

        if tenant and not self._does_tenant_exist(tenant):
            logger.info(
                f"Tenant {tenant} does not exist in index {self._index_name}. "
                "Creating tenant."
            )
            tenant_objs = [weaviate.classes.tenants.Tenant(name=tenant)]
            self._collection.tenants.create(tenants=tenant_objs)

        ids = []
        embeddings: Optional[List[List[float]]] = None
        if self._embedding:
            embeddings = self._embedding.embed_documents(list(texts))

        with self._client.batch.dynamic() as batch:
            for i, text in enumerate(texts):
                data_properties = {self._text_key: text}
                if metadatas is not None:
                    for key, val in metadatas[i].items():
                        data_properties[key] = _json_serializable(val)

                # Allow for ids (consistent w/ other methods)
                # # Or uuids (backwards compatible w/ existing arg)
                # If the UUID of one of the objects already exists
                # then the existing object will be replaced by the new object.
                _id = get_valid_uuid(uuid4())
                if "uuids" in kwargs:
                    _id = kwargs["uuids"][i]
                elif "ids" in kwargs:
                    _id = kwargs["ids"][i]

                batch.add_object(
                    collection=self._index_name,
                    properties=data_properties,
                    uuid=_id,
                    vector=embeddings[i] if embeddings else None,
                    tenant=tenant,
                )

                ids.append(_id)

        failed_objs = self._client.batch.failed_objects
        for obj in failed_objs:
            err_message = (
                f"Failed to add object: {obj.original_uuid}\nReason: {obj.message}"
            )

            logger.error(err_message)

        return ids
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

the add_documents / add_texts in WeaviateVectorStore logs errors during indexing but still returns a valid list of chunk IDs, giving the impression that indexing was successfull especially in fastapi apps where the langchain logger is not attached to the runtime. there should be imho a way at least something like failed_objects, success_objects = store.add_documents(), so that it becomes clear for the implementation side of add_documents which chunks failed:

### System Info

python -m langchain_core.sys_info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Tue Nov 5 00:21:55 UTC 2024
> Python Version:  3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 13:27:36) [GCC 11.2.0]

Package Information
-------------------
> langchain_core: 1.2.6
> langchain: 1.2.0
> langchain_community: 0.4.1
> langsmith: 0.3.45
> langchain_anthropic: 1.0.0
> langchain_classic: 1.0.1
> langchain_openai: 1.1.6
> langchain_text_splitters: 1.1.0
> langchain_weaviate: 0.0.6
> langgraph_api: 0.6.24
> langgraph_cli: 0.4.11
> langgraph_runtime_inmem: 0.21.1
> langgraph_sdk: 0.3.1

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.12.14
> anthropic: 0.75.0
> blockbuster: 1.5.25
> click: 8.1.8
> cloudpickle: 3.1.1
> cryptography: 44.0.1
> dataclasses-json: 0.6.7
> grpcio: 1.76.0
> grpcio-health-checking: 1.76.0
> grpcio-tools: 1.75.1
> httpx: 0.28.1
> httpx-sse: 0.4.0
> jsonpatch: 1.33
> jsonschema-rs: 0.29.1
> langgraph: 1.0.5
> langgraph-checkpoint: 3.0.1
> numpy: 2.2.6
> openai: 2.14.0
> opentelemetry-api: 1.39.0
> opentelemetry-exporter-otlp-proto-http: 1.39.0
> opentelemetry-sdk: 1.39.0
> orjson: 3.11.5
> packaging: 25.0
> protobuf: 6.33.2
> pydantic: 2.12.5
> pydantic-settings: 2.12.0
> pyjwt: 2.10.1
> pytest: 8.3.4
> python-dotenv: 1.1.0
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 13.9.4
> simsimd: 6.5.12
> sqlalchemy: 2.0.40
> SQLAlchemy: 2.0.40
> sse-starlette: 2.1.3
> starlette: 0.46.2
> structlog: 25.2.0
> tenacity: 9.1.2
> tiktoken: 0.8.0
> truststore: 0.10.4
> typing-extensions: 4.15.0
> uuid-utils: 0.12.0
> uvicorn: 0.34.0
> watchfiles: 1.0.4
> weaviate-client: 4.14.0
> zstandard: 0.23.0
(venv) x@LAPTOP-97M072GO:~/Repos/chain-pipes$

## Comments

**JiwaniZakir:**
Happy to tackle this one. Working on it. I'll include a test to prevent regression.

**JiwaniZakir:**
Submitted a PR: https://github.com/langchain-ai/langchain/pull/35632
