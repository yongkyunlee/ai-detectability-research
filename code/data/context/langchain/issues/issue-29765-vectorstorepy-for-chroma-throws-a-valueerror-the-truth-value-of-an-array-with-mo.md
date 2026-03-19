# vectorstore.py for chroma throws a ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()

**Issue #29765** | State: closed | Created: 2025-02-12 | Updated: 2026-03-07
**Author:** sundeepChandhoke
**Labels:** bug, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
 if non_empty_ids:
                metadatas = [metadatas[idx] for idx in non_empty_ids]
                texts_with_metadatas = [texts[idx] for idx in non_empty_ids]
                embeddings_with_metadatas = (
                    [embeddings[idx] for idx in non_empty_ids] if embeddings else None
                )
                ids_with_metadata = [ids[idx] for idx in non_empty_ids]
                try:
                    self._collection.upsert(
                        metadatas=metadatas,  # type: ignore
                        embeddings=embeddings_with_metadatas,  # type: ignore
                        documents=texts_with_metadatas,
                        ids=ids_with_metadata,
                    )
                except ValueError as e:
                    if "Expected metadata value to be" in str(e):
                        msg = (
                            "Try filtering complex metadata from the document using "
                            "langchain_community.vectorstores.utils.filter_complex_metadata."
                        )
                        raise ValueError(e.args[0] + "\n\n" + msg)
                    else:
                        raise e
```

### Error Message and Stack Trace (if applicable)

This code in vectorstores.py for chroma db has a bug.  The check
```python
embeddings_with_metadatas = (
                    [embeddings[idx] for idx in non_empty_ids] if embeddings else None
                )
```
should be
```python
embeddings_with_metadatas = (
                  [embeddings[idx] for idx in non_empty_ids] if embeddings is not None else None
)
```

### Description

I am trying to save embeddings  in Chroma db which are created using sentence transformer.  This results in a ValueError as listed in the title

### System Info

[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
pypdf = "*"
langchain = "*"
flask = "*"
chromadb = "*"
pytest = "*"
requests = "*"
minio = "*"
ollama = "*"
langchain-ollama = "*"
sentence-transformers = "*"
langchain-community = "*"
celery = "*"
python-dotenv = "*"
marshmallow = "*"
boto3 = "*"
unstructured = {extras = ["all-docs"], version = "*"}
pymupdf4llm = "*"
xformers = "*"
langchain-chroma = "*"
markdown-to-json = "*"

[dev-packages]

[requires]
python_version = "3.12"
