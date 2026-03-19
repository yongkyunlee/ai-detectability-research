# feat: add Sarvam AI partner integration (langchain-sarvamcloud)

**Issue #35951** | State: closed | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** Srinivasulu2003
**Labels:** feature request, external

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
- [x] Other / not sure / general

### Feature Description

I would like LangChain to add `langchain-sarvamcloud` as an official partner package integrating Sarvam AI — India's sovereign AI platform with support for 22+ Indian languages.

This adds 8 new classes:
- `ChatSarvam` — LLM chat completions with tool calling, streaming, structured output
- `SarvamSTT` — Speech-to-text (REST, 30s max, 5 transcription modes, 23 languages)
- `SarvamBatchSTT` — Async batch speech-to-text (up to 1hr/file, diarization)
- `SarvamTTS` — Text-to-speech with 30+ voices across 11 Indian languages
- `SarvamTranslator` — Text translation with formal/colloquial/code-mixed modes
- `SarvamTransliterator` — Script conversion (Devanagari ↔ Roman, etc.)
- `SarvamLanguageDetector` — Language and script identification
- `SarvamDocumentIntelligence` — PDF/image OCR as a LangChain `BaseLoader`

The package is already published on PyPI: https://pypi.org/project/langchain-sarvamcloud/

### Use Case

India has 22 official languages but most AI integrations in LangChain only support English. Sarvam AI is purpose-built for Indian languages and is widely used in India for building AI applications in Hindi, Tamil, Telugu, Bengali, and 18+ other languages.

Currently there is no LangChain integration for Sarvam AI, so developers building Indian language applications have to use the raw sarvamai SDK without LangChain's abstractions (chains, agents, RAG pipelines, etc.).

This integration enables Indian developers to build LangChain-native applications in their native languages — RAG pipelines over Hindi documents, voice bots in Telugu, multilingual agents, etc.

### Proposed Solution

The implementation is complete and ready. The full code is in my fork:
https://github.com/Srinivasulu2003/langchain/tree/feat/sarvamcloud-integration

It follows all LangChain partner package conventions:
- Extends `BaseChatModel`, `BaseLoader` from `langchain-core`
- 76 unit tests passing, integration tests included
- Full README documentation (all 8 classes, parameter tables, language matrix)
- CI/CD config files already updated (dependabot, pr-file-labeler, issue templates, integration tests)
- `ChatSarvam` added to `langchain_core/load/mapping.py` deserialization allowlist

```python
from langchain_sarvamcloud import ChatSarvam, SarvamSTT, SarvamTTS

# Chat in Hindi
model = ChatSarvam(model="sarvam-105b")
response = model.invoke("हिंदी में बताओ कि LangChain क्या है?")

# Speech to text
stt = SarvamSTT()
with open("audio.wav", "rb") as f:
    result = stt.transcribe(f, language_code="hi-IN")

### Alternatives Considered

Using the raw sarvamai SDK directly  but this doesn't integrate with LangChain chains, agents, or RAG pipelines.

### Additional Context

**Additional Context:**
PR ready at: https://github.com/Srinivasulu2003/langchain/tree/feat/sarvamcloud-integration
PyPI: https://pypi.org/project/langchain-sarvamcloud/
Sarvam AI docs: https://docs.sarvam.ai/
API key (free): https://dashboard.sarvam.ai/
**Author:** Srinivasulu Kethanaboina  
**LinkedIn:** [kethanaboina-srinivasulu](https://www.linkedin.com/in/kethanaboina-srinivasulu-1a3452274/)

## Comments

**arun-kumar-c-s:**
I would like to work on this. Is this still open for contribution?

**maxsnow651-dev:**
Yes I guess so

On Tue, Mar 17, 2026, 7:34 AM Arun Kumar C S ***@***.***>
wrote:

> *arun-kumar-c-s* left a comment (langchain-ai/langchain#35951)
> 
>
> I would like to work on this. Is this still open for contribution?
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

**Srinivasulu2003:**
Thanks for your interest!

I’ve already completed the implementation and opened a PR for this integration. Feel free to take a look happy to collaborate on reviews or further improvements 👍

**maxsnow651-dev:**
Alright I will do so and ur welcome

On Tue, Mar 17, 2026, 9:24 AM SRINIVASULU KETHANABOINA  wrote:

> *Srinivasulu2003* left a comment (langchain-ai/langchain#35951)
> 
>
> Thanks for your interest!
>
> I’ve already completed the implementation and opened a PR for this
> integration. Feel free to take a look happy to collaborate on reviews or
> further improvements 👍
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!

**Jairooh:**
This is a common pattern in the LangChain ecosystem now — the `langchain-community` split already set the precedent, and most newer integrations (like `langchain-anthropic`, `langchain-google-genai`) live as standalone packages. For discoverability, you can open a PR to add your package to the [LangChain integrations docs page](https://python.langchain.com/docs/integrations/providers/) and also register it on the [LangChain Hub](https://smith.langchain.com/hub) — those tend to be the canonical discovery paths the community uses when the monorepo isn't an option.

**Srinivasulu2003:**
Thanks for the clarification and guidance!

That makes sense given the shift toward standalone integration packages. I’ve already published the package as **langchain-sarvamcloud** on PyPI and will continue maintaining it independently following LangChain’s partner package patterns.

For discoverability, I’ll proceed with:

* Opening a PR to add this integration to the LangChain integrations docs
* Providing example notebooks and usage guides
* Exploring LangChain Hub for sharing prompts/templates

If there are any specific guidelines or preferred formats for listing integrations in the docs, I’d be happy to follow them.

Appreciate the direction—this helps a lot. Thanks!

**fairchildadrian9-create:**
Let me know if u need more help here

On Tue, Mar 17, 2026, 10:30 AM SRINIVASULU KETHANABOINA  wrote:

> *Srinivasulu2003* left a comment (langchain-ai/langchain#35951)
> 
>
> Thanks for the clarification and guidance!
>
> That makes sense given the shift toward standalone integration packages.
> I’ve already published the package as *langchain-sarvamcloud* on PyPI and
> will continue maintaining it independently following LangChain’s partner
> package patterns.
>
> For discoverability, I’ll proceed with:
>
>    - Opening a PR to add this integration to the LangChain integrations
>    docs
>    - Providing example notebooks and usage guides
>    - Exploring LangChain Hub for sharing prompts/templates
>
> If there are any specific guidelines or preferred formats for listing
> integrations in the docs, I’d be happy to follow them.
>
> Appreciate the direction—this helps a lot. Thanks!
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
