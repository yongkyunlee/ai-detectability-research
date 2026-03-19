# Feature Request: Encrypted Memory Backends for LangChain

**Issue #34953** | State: open | Created: 2026-02-01 | Updated: 2026-03-03
**Author:** HATAKEkakshi
**Labels:** core, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

# Encrypted Chat Memory for LangChain  
### Feature Proposal

## Feature Description

Introduce first-class encrypted memory backends to LangChain for secure, PII-safe chat history storage across Redis, MongoDB, and other datastores.  
This enables LangChain to be safely used in healthcare, finance, enterprise, and any production environment requiring encrypted data-at-rest.

---

## Use Case

Existing LangChain memory backends (such as `RedisChatMessageHistory` and `MongoDBChatMessageHistory`) store all messages in plaintext.

This creates major limitations for:

1. PII-heavy applications  
2. Healthcare systems (HIPAA)  
3. Financial systems (PCI/KYC)  
4. Enterprise copilots  
5. Regulated or privacy-sensitive workflows  

Because memory is unencrypted, many teams cannot adopt LangChain memory in production, even though they rely on LangChain for agents, RAG, and chat pipelines.

---

## Proposed Solution  
### Encrypted Chat Memory History Modules

Introduce encrypted versions of LangChain's existing chat memory adapters as official integrations.

These modules already exist, are open-source, and have been production-tested.

---

## 1. Encrypted Redis Chat Memory History

**Package:** `langchain-encrypted-redis-memory`  
A secure, drop-in replacement for `RedisChatMessageHistory`.

**Features:**
- AES-128 (Fernet) message encryption  
- Same API as LangChain's built-in Redis memory  
- No migration required  
- Transparent encryption/decryption  
- Suitable for short-term memory in agents and RAG flows  

**PyPI:** https://pypi.org/project/langchain-encrypted-redis-memory/  
**GitHub:** https://github.com/HATAKEkakshi/langchain-encrypted-redis-memory

---

## 2. Encrypted MongoDB Chat Memory History

**Package:** `langchain-encrypted-mongo-memory`  
A secure alternative to `MongoDBChatMessageHistory` designed for persistent, long-term storage.

**Features:**
- AES-128 encrypted message documents  
- Protects message content and session identifiers  
- Designed for healthcare, finance, and compliance-heavy workloads  

**PyPI:** https://pypi.org/project/langchain-encrypted-mongo-memory/  
**GitHub:** https://github.com/HATAKEkakshi/langchain-encrypted-mongo-memory

---

## Shared Encryption Layer  
### mores-encryption

**Package:** `mores-encryption`  
Cryptographic foundation for both memory modules.

**Capabilities:**
- AES-128 (Fernet) encryption  
- Deterministic hashing (PBKDF2-SHA256)  
- JSON encryption helpers  
- Environment-based key management (`ENCRYPTION_KEY`)

**PyPI:** https://pypi.org/project/mores-encryption/

---

## Why This Should Be Part of LangChain

- Addresses a critical security gap in chat memory  
- Enables compliance with HIPAA, PCI, GDPR, enterprise security requirements  
- Zero breaking changes  
- Maintains LangChain's message schema  
- Production-ready and actively maintained  
- Fits naturally within LangChain’s ecosystem

---

## Integration Guide

A complete notebook demonstrating encrypted memory usage:

https://github.com/HATAKEkakshi/integration-guide/blob/main/examples/langchain-encrypted-memory-example.ipynb

**Includes:**
- Encrypted Redis + MongoDB examples  
- Plaintext vs encrypted memory comparison  
- Hashed session ID best practices  
- Drop-in integration with existing LangChain pipelines  

---

## Requested Category

Feature Proposal → Memory → Security → Encrypted Chat Memory History

---

## Alternatives Considered

### Using existing LangChain memory modules  
Rejected because all store plaintext and cannot be used in regulated environments.

### Manual encryption before writing to memory  
Adds complexity, breaks LangChain's plug-and-play design, and requires rewriting multiple parts of the codebase.

### Subclassing memory modules within individual applications  
Leads to duplicated implementations and long-term maintenance burden.

### Searching for existing encrypted memory modules  
None existed with transparent encryption and full LangChain compatibility.

Because no secure and compatible solution existed, these encrypted backends were implemented by extending LangChain’s official classes and overriding only the persistence layer.  
This provides fully automatic encryption/decryption without affecting application logic.

---

## Additional Context

These modules were developed while building CuraDocs, a healthcare-grade AI system requiring encrypted data storage for doctor-patient interactions.

Plaintext memory backends could not be used, leading to the creation of:

- `langchain-encrypted-redis-memory`  
- `langchain-encrypted-mongo-memory`  
- `mores-encryption`  

All implementations are actively maintained, open-source, and compatible with LangChain’s chat message schema.

---

## Example Notebook

Full integration example (Redis + MongoDB):

https://github.com/HATAKEkakshi/integration-guide/blob/main/examples/langchain-encrypted-memory-example.ipynb

This notebook demonstrates:

- Encrypted memory in real LangChain workflows  
- How decrypted messages are retrieved  
- How session IDs are protected via deterministic hashing  
- Side-by-side behavior: encrypted vs plaintext memory  

---

## Comments

**keenborder786:**
@HATAKEkakshi Please do check this out: https://docs.langchain.com/langsmith/encryption
