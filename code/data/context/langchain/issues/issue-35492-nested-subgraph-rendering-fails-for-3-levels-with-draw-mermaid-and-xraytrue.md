# Nested subgraph rendering fails for 3+ levels with `draw_mermaid` and `xray=True`

**Issue #35492** | State: open | Created: 2026-03-01 | Updated: 2026-03-15
**Author:** taehan79-kim
**Labels:** bug, core, external

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
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

# --- Grandchild graph ---
class GrandChildState(TypedDict):
    my_grandchild_key: str

def grandchild_1(state: GrandChildState) -> GrandChildState:
    return {"my_grandchild_key": f'([GrandChild] {state["my_grandchild_key"]})'}

grandchild = StateGraph(GrandChildState)
grandchild.add_node("grandchild", grandchild_1)
grandchild.add_edge(START, "grandchild")
grandchild.add_edge("grandchild", END)
grandchild_graph = grandchild.compile()

# --- Child graph (calls grandchild) ---
class ChildState(TypedDict):
    my_child_key: str

def call_grandchild_graph(state: ChildState) -> ChildState:
    grandchild_graph_input = {"my_grandchild_key": state["my_child_key"]}
    grandchild_graph_output = grandchild_graph.invoke(grandchild_graph_input)
    return {"my_child_key": f'([Child] {grandchild_graph_output["my_grandchild_key"]})'}

child = StateGraph(ChildState)
child.add_node("child", call_grandchild_graph)
child.add_edge(START, "child")
child.add_edge("child", END)
child_graph = child.compile()

# --- Parent graph (calls child) ---
class ParentState(TypedDict):
    my_parent_key: str

def call_child_graph(state: ParentState) -> ParentState:
    child_graph_input = {"my_child_key": state["my_parent_key"]}
    child_graph_output = child_graph.invoke(child_graph_input)
    return {"my_parent_key": f'([Parent] {child_graph_output["my_child_key"]})'}

parent = StateGraph(ParentState)
parent.add_node("parent", call_child_graph)
parent.add_edge(START, "parent")
parent.add_edge("parent", END)
parent_graph = parent.compile()

# --- Reproduce the bug ---

# 2-level nesting: renders correctly
display(Image(child_graph.get_graph(xray=True).draw_mermaid_png()))

# 3-level nesting: node IDs show \3a instead of readable names
display(Image(parent_graph.get_graph(xray=True).draw_mermaid_png()))

# Check the raw Mermaid syntax to see the escaped IDs
print(parent_graph.get_graph(xray=True).draw_mermaid())
```

### Error Message and Stack Trace (if applicable)

```shell
No error is raised. The issue is a **rendering defect** — the generated Mermaid diagram fails to properly render nested subgraph boxes for 3 or more levels of nesting.

For 3+ level nesting, the diagram shows flat node IDs with escaped colons instead of properly nested subgraph containers:

graph TD;
	__start__([__start__]):::first
	__end__([__end__]):::last
	__start__ --> parent\3achild\3agrandchild;
	parent\3achild\3agrandchild --> __end__;

No subgraph boxes are created at all — the nested node appears as a flat element with `\3a` (CSS-escaped colon) in its ID.
```

### Description

When visualizing a LangGraph with **3 or more levels of nested subgraphs** using `get_graph(xray=True).draw_mermaid()`, the Mermaid output fails to create proper subgraph boxes for the nested hierarchy. Instead, nodes appear as flat elements with escaped colon characters in their IDs.

### Root Cause

The `Graph.extend()` method creates hierarchical node IDs by joining names with colons (e.g., `parent:child:grandchild`).

The `draw_mermaid()` function in `langchain_core/runnables/graph_mermaid.py` has two code paths for subgraph rendering:

1. **`add_subgraph()` function (recursive)** - Handles subgraphs that contain internal edges between their nodes
2. **"Empty subgraphs" section (around line 239)** - Handles subgraphs where all nodes connect to nodes outside the subgraph (no internal edges)

The bug exists in the "empty subgraphs" section. The original code used this condition:

```python
if ":" not in prefix:
    # ... create subgraph box
```

This condition completely skipped multi-level prefixes like `parent:child`. Since each graph wraps its child as a single subgraph node, the nested subgraph's nodes have no internal edges (they connect only to parent nodes), which forces the code into the "empty subgraphs" path. With `":" not in prefix` being false for `parent:child`, the subgraph boxes never get created in the Mermaid output.

As a result, 3+ level nested subgraphs don't render their subgraph containers, causing the nodes to appear flat with escaped colons in their IDs (`parent\3achild\3agrandchild`).

### Behavior Comparison

| Nesting Level | Behavior | Status |
|---------------|----------|--------|
| 2 levels (child → grandchild) | Subgraph boxes render correctly | OK |
| 3 levels (parent → child → grandchild) | Subgraph boxes not created, nodes shown as flat with escaped colons | **Bug** |

The issue manifests when nested subgraph nodes have no internal edges between them, which forces the "empty subgraphs" code path.

### Screenshots

**2-level nesting (correct):**

The child graph with `xray=True` correctly renders `grandchild` inside a `child` subgraph box.

**3-level nesting (bug):**

The parent graph with `xray=True` shows `parent\3achild\3agrandchild` as a flat node label instead of properly nesting grandchild within subgraph boxes.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Mon Jul 14 11:30:40 PDT 2025; root:xnu-11417.140.69~1/RELEASE_ARM64_T6041
> Python Version:  3.13.10 (main, Dec  2 2025, 22:01:27) [Clang 21.1.4 ]

Package Information
-------------------
> langchain_core: 1.2.16
> langsmith: 0.7.9
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> tenacity: 9.1.4
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> xxhash: 3.6.0
> zstandard: 0.25.0

> langgraph: 1.0.10

## Comments

**JiwaniZakir:**
I'd like to work on this issue. I'll submit a PR shortly.

**JiwaniZakir:**
This looks like something I can help with -- I'll put up a PR. I'll include a test to prevent regression.

**JiwaniZakir:**
Put up a fix here: https://github.com/langchain-ai/langchain/pull/35596 -- let me know if anything needs adjusting.

**shivamtiwari3:**
Hi @christian-bromann , I'd like to work on this. I've identified the root cause and have a fix ready in PR #35933.

The issue is in the "empty subgraphs" section of `draw_mermaid` — the guard `if ":" not in prefix` silently skips multi-level prefixes like `parent:child`, so no subgraph boxes are ever created for 3+ level nesting. The fix replaces the flat loop with a recursive helper that properly nests `subgraph`/`end` blocks for arbitrary depth.

Could you please assign this issue to me so I can reopen the PR? Thanks!
