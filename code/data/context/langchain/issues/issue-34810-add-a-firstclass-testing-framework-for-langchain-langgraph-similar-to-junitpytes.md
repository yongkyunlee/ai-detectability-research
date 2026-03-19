# Add a First‑Class Testing Framework for LangChain + LangGraph (Similar to JUnit/PyTest/LangTest)

**Issue #34810** | State: closed | Created: 2026-01-19 | Updated: 2026-03-15
**Author:** rbhattarai
**Labels:** langchain, cli, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [x] [langgraph](https://github.com/langchain-ai/langgraph)
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
- [x] langchain-cli
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
- [ ] Other / not sure / general

### Feature Description

As LLM applications grow more complex, reliable testing becomes essential. Today, both LangChain and LangGraph rely on ad‑hoc PyTest patterns, manual mocks, and custom assertions. There is no unified, first‑class testing framework that supports deterministic LLM mocking, chain/graph assertions, snapshot testing, or workflow‑level validation. A dedicated testing module—shared across LangChain and LangGraph and similar in spirit to JUnit, NUnit, PyTest, or LangTest—would dramatically improve reliability, developer confidence, ecosystem maturity and enterprise readiness.

LangChain and LangGraph are becoming the de‑facto standard for LLMs and agentic workflow orchestration. LangChain and LangGraph are increasingly used together. A shared testing framework would:

- Provide consistent testing patterns across both libraries
- Reduce fragmentation in the ecosystem
- Improve reliability of agentic and multi‑step workflows
- Make enterprise adoption easier
- Encourage best practices for LLM application testing

This would position LangChain + LangGraph as not only powerful orchestration tools, but also **production‑grade engineering frameworks**.

### Use Case

Developers currently rely on ad‑hoc mocks, manual assertions, or external libraries. This leads to inconsistent testing practices, brittle tests, and reduced confidence in production deployments. Developers face several challenges when testing LLM‑based systems:

- **Nondeterministic LLM outputs** make traditional unit tests unreliable
- **No standard mocking utilities** for LLMs, tools, or agents
- **No snapshot testing** for prompts, chain outputs, or graph states
- **No built‑in evaluators** for similarity, factuality, or safety
- **Graph workflows are difficult to test** due to dynamic transitions and state evolution
- **Testing patterns are fragmented** across the ecosystem
- No standard way to test prompt regressions
- Limited support for evaluating chain correctness or safety
- Hard‑to‑maintain test setups across projects

A unified testing framework would solve these issues.

### Proposed Solution

Create a **Unified LangChain/LangGraph Testing Framework** with the following capabilities:

**1. Unit Testing for Chains and Nodes**

- Test individual chain components
- Assert on output structure, content, metadata 
- Validate tool calls and intermediate steps
- Validate node logic in LangGraph
- Provide fixtures for common components (chat models, tools, memory, state)

**2. Deterministic LLM Mocking**

- Static responses
- Pattern‑based mocks
- Response sequences
- Simulated failures (timeouts, errors, hallucinations)

**3. Integration Testing for Full Workflows**

- Run entire chains or graphs end‑to‑end
- Validate final outputs
- Validate intermediate transitions and state updates
- Support async and streaming workflows

**4. Snapshot Testing**

- Prompt templates
- Chain outputs
- Graph state at each node
- Diffing snapshots to detect regressions

**5. Built‑in Evaluators**

- Similarity scoring (embedding‑based)
- Factuality checks
- Toxicity/bias checks
- Custom evaluator plugin support

**6. Coverage‑Like Metrics**

- Node coverage (LangGraph)
- Transition coverage
- Chain step coverage
 

**7. CLI Tooling**

- `langtest run` 
- `langtest report` or `langtest watch`
- JSON/HTML reports
- Snapshot diffs

**8. CI/CD Integration**

- GitHub Actions templates
- Docker‑friendly test runner
- Example workflows:

**9. Example Usage**

- LangChain example:

```
def test_order_chain(mock_llm):
    chain = OrderChain(llm=mock_llm)
    mock_llm.expect("What would you like to order?", "I want pizza")
    result = chain.invoke({"input": "Order food"})
    assert result["item"] == "pizza"
```

- LangGraph example:

```
def test_graph_state_transition(graph, mock_llm):
    mock_llm.enqueue("Sure, booking a flight to Tokyo.")
    final_state = graph.invoke({"task": "Book a flight to Tokyo"})
    assert final_state["destination"] == "Tokyo"
```

**Scope**
This proposal does not require implementing all features at once; even starting with deterministic LLM mocks + chain/graph assertions would deliver immediate value.

#### Why now?

With LangGraph’s rapid adoption for agentic workflows and LangChain’s expanding ecosystem, a unified testing framework would meet a growing need for reliability and production readiness.

#### What would this framework be called ?

The framework could live under a new package (e.g., `langchain-test` or `langgraph-test`), or be integrated into existing packages depending on maintainers’ preference.

### Alternatives Considered

Prior Art

- LangTest (focus on testing Language Models, not integrated with LangChain/Graph)
- PyTest (excellent runner but lacks LLM‑specific utilities)
- JUnit/NUnit (inspiration for structure)
- Jest snapshot testing
- Workflow testing patterns from Airflow, Temporal, Dagster

### Additional Context

A unified testing framework would fill one of the most significant gaps in the LangChain/LangGraph ecosystem. It would empower developers to build safer, more reliable, and more maintainable LLM applications—while reducing friction and increasing confidence in production deployments.

I’d be happy to help with early design discussions or contribute to an initial prototype.

## Comments

**keenborder786:**
Have you seen `langchain-tests`?

**raye-deng:**
The need for a unified testing framework for LLM apps is real. The main challenge is that LLM outputs are inherently non-deterministic, so traditional assertion-based testing breaks down. From our experience reviewing AI-generated LangChain code, the most common failure modes are:

1. **Tool hallucination** — chains calling tools that don't exist or with wrong signatures
2. **Schema drift** — output parsers expecting one format but getting another as models update
3. **Context window overflow** — tests passing with short inputs but failing with production-length prompts
4. **Mock-reality gap** — mocked LLM responses that don't match real model behavior

A good testing framework would need first-class support for: (a) semantic similarity assertions instead of exact matches, (b) snapshot testing with model-version-aware diffing, (c) tool-call validation against the actual tool schema, and (d) cost-aware replay of real LLM calls.

We've been tackling a subset of these problems in [open-code-review](https://github.com/raye-deng/open-code-review), which scans AI-generated code for hallucinated packages, fabricated APIs, and schema mismatches. The overlap with what a LangChain testing framework would need is significant — especially schema validation and tool-call verification.
