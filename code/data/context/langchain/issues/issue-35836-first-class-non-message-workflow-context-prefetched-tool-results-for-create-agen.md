# First-class non-message workflow context / prefetched tool results for `create_agent`

**Issue #35836** | State: open | Created: 2026-03-13 | Updated: 2026-03-18
**Author:** yetanotherion
**Labels:** langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
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

### Feature Description

## Summary

`create_agent` should support workflow nodes that compute and inject context **before** the main model step runs.

Today, one workaround is to replay precomputed tool output as message history. That worked for us with models until `gemini-2.5-flash-lite`, but it breaks with `gemini-3.1-flash-lite-preview`, which rejects this message pattern.

## Problem

Newer Gemini models appear to validate tool-call turn structure more strictly, and reject this pattern.

## Reproduction

```python
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI, ChatGoogleGenerativeAIError

from app.config import settings

pytestmark = [
    pytest.mark.integration,
]

@pytest.mark.parametrize(
    ("model_name", "expected_content", "expected_error_match"),
    [
        pytest.param("gemini-2.5-flash-lite", "world", None, id="gemini-2.5-flash-lite"),
        pytest.param(
            "gemini-3.1-flash-lite-preview",
            None,
            "function call turn comes immediately after a user turn or after a function response turn",
            id="gemini-3.1-flash-lite-preview",
        ),
    ],
)
def test_native_gemini_preview_rejects_replayed_tool_context(
    model_name: str,
    expected_content: str | None,
    expected_error_match: str | None,
) -> None:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.0,
        project=settings.GCP_VERTEXAI_PROJECT_ID,
        location=settings.GCP_VERTEXAI_LOCATION,
        vertexai=True,
    )
    tool_call_id = "hello-world-tool-call"
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": tool_call_id,
                    "name": "hello_world_tool",
                    "args": {"query": "hello"},
                }
            ],
        ),
        ToolMessage(
            content='{"results":[{"name": "world"}]}',
            name="hello_world_tool",
            tool_call_id=tool_call_id,
        ),
        HumanMessage(content="What is after hello?"),
    ]

    if expected_error_match is None:
        response = llm.invoke(messages)
        assert response.content == expected_content
        return

    with pytest.raises(ChatGoogleGenerativeAIError, match=expected_error_match):
        llm.invoke(messages)
```

### Use Case

We have an agent that supports multiple use cases, including conversational chat.

In certain scenarios, the user interacts with precomputed screens that launch predefined static workflows. These workflows usually perform a specific tool call and then allow the agent to continue the interaction.

While the same behavior can often be reproduced through a natural-language query to the chatbot, letting the LLM infer which tool calls to make, static workflows provide greater reliability. We chose this design because LLM-driven tool selection is not fully deterministic and may not always produce the expected execution path.

### Proposed Solution

Provide an API that lets an agent call tools programmatically, supporting both UX-driven and chat-driven workflows in a single codebase.

### Alternatives Considered

See the workaround on top.

### Additional Context

_No response_

## Comments

**yetanotherion:**
Actually it's a regression on 3.1-flash-lite only, we will follow-up with Google and share the result here 👍 

```python
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI, ChatGoogleGenerativeAIError

from app.config import settings

pytestmark = [
    pytest.mark.integration,
]

def _build_llm(model_name: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.0,
        project=settings.GCP_VERTEXAI_PROJECT_ID,
        location=settings.GCP_VERTEXAI_LOCATION,
        vertexai=True,
    )

def _extract_text(content: str | list[str | dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content

    texts: list[str] = []
    for block in content:
        if isinstance(block, str):
            texts.append(block)
            continue
        text = block.get("text")
        if isinstance(text, str):
            texts.append(text)

    return " ".join(texts)

@pytest.mark.parametrize(
    ("model_name", "expected_content", "expected_error_match"),
    [
        pytest.param("gemini-2.5-flash-lite", "world", None, id="gemini-2.5-flash-lite"),
        pytest.param(
            "gemini-3.1-flash-lite-preview",
            None,
            "function call turn comes immediately after a user turn or after a function response turn",
            id="gemini-3.1-flash-lite-preview",
        ),
        pytest.param(
            "gemini-3-pro-preview",
            "world",
            None,
            id="gemini-3-pro-preview",
        ),
        pytest.param(
            "gemini-3-flash-preview",
            "world",
            None,
            id="gemini-3-flash-preview",
        ),
    ],
)
def test_native_gemini_preview_rejects_replayed_tool_context(
    model_name: str,
    expected_content: str | None,
    expected_error_match: str | None,
) -> None:
    llm = _build_llm(model_name)
    tool_call_id = "hello-world-tool-call"
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": tool_call_id,
                    "name": "hello_world_tool",
                    "args": {"query": "hello"},
                }
            ],
        ),
        ToolMessage(
            content='{"results":[{"name": "world"}]}',
            name="hello_world_tool",
            tool_call_id=tool_call_id,
        ),
        HumanMessage(content="What is after hello?"),
    ]

    if expected_error_match is None:
        response = llm.invoke(messages)
        assert expected_content in _extract_text(response.content)
        return

    with pytest.raises(ChatGoogleGenerativeAIError, match=expected_error_match):
        llm.invoke(messages)

```

**yetanotherion:**
Sharing a reproduction of the bug using google adk
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14,=1.27.2",
# ]
# ///

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from uuid import uuid4

from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.auth.exceptions import RefreshError
from google.genai import errors, types

APP_NAME = "gemini-tool-message-repro"
AGENT_NAME = "gemini_repro_agent"
DEFAULT_PROJECT = "backend-producti-b8633498"
DEFAULT_LOCATION = "global"

@dataclass(frozen=True)
class Case:
    model_name: str
    expected_content: str | None
    expected_error_match: str | None

CASES = (
    Case("gemini-2.5-flash-lite", "world", None),
    Case(
        "gemini-3.1-flash-lite-preview",
        None,
        "function call turn comes immediately after a user turn or after a function response turn",
    ),
    Case("gemini-3-pro-preview", "world", None),
    Case("gemini-3-flash-preview", "world", None),
)

def _build_tool_call_event(tool_call_id: str) -> Event:
    tool_call_part = types.Part.from_function_call(
        name="hello_world_tool",
        args={"query": "hello"},
    )
    [tool_call_part.function_call.id](http://tool_call_part.function_call.id/) = tool_call_id
    return Event(
        author=AGENT_NAME,
        content=types.ModelContent(parts=[tool_call_part]),
    )

def _build_tool_response_event(tool_call_id: str) -> Event:
    tool_response_part = types.Part.from_function_response(
        name="hello_world_tool",
        response={"results": [{"name": "world"}]},
    )
    [tool_response_part.function_response.id](http://tool_response_part.function_response.id/) = tool_call_id
    return Event(
        author=AGENT_NAME,
        content=types.UserContent(parts=[tool_response_part]),
    )

def _extract_text(content: types.Content) -> str:
    return " ".join(part.text for part in (content.parts or []) if part.text)

def _configure_vertex_env(project: str, location: str) -> None:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    os.environ["GOOGLE_CLOUD_LOCATION"] = location

async def _invoke_with_replayed_tool_context(model_name: str) -> str:
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME,
        agent=LlmAgent(
            name=AGENT_NAME,
            model=Gemini(model=model_name),
            instruction="Answer the user's question using the available tool context.",
        ),
        session_service=session_service,
    )
    user_id = "test-user"
    session_id = str(uuid4())
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    tool_call_id = "hello-world-tool-call"
    await session_service.append_event(session, _build_tool_call_event(tool_call_id))
    await session_service.append_event(session, _build_tool_response_event(tool_call_id))

    final_response_text: str | None = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.UserContent(
            parts=[types.Part.from_text(text="What is after hello?")],
        ),
    ):
        if event.is_final_response() and event.content:
            final_response_text = _extract_text(event.content)

    if final_response_text is None:
        raise AssertionError("Expected a final ADK response event.")

    return final_response_text

async def _run_case(case: Case) -> tuple[bool, str]:
    if case.expected_error_match is None:
        response = await _invoke_with_replayed_tool_context(case.model_name)
        if case.expected_content is not None and case.expected_content in response:
            return True, f"{case.model_name}: response contained {case.expected_content!r}"
        return False, f"{case.model_name}: expected {case.expected_content!r}, got {response!r}"

    try:
        await _invoke_with_replayed_tool_context(case.model_name)
    except errors.ClientError as exc:
        if case.expected_error_match in str(exc):
            return True, f"{case.model_name}: raised expected ClientError"
        return False, f"{case.model_name}: unexpected ClientError: {exc}"

    return False, f"{case.model_name}: expected ClientError matching {case.expected_error_match!r}"

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce Gemini replayed-tool-context behavior via Google ADK.",
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Run only the specified model. May be passed multiple times.",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_VERTEXAI_PROJECT_ID") or DEFAULT_PROJECT,
        help="Vertex AI project id.",
    )
    parser.add_argument(
        "--location",
        default=os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_VERTEXAI_LOCATION") or DEFAULT_LOCATION,
        help="Vertex AI location.",
    )
    return parser.parse_args()

async def _main() -> int:
    args = _parse_args()
    _configure_vertex_env(args.project, args.location)

    selected_models = set(args.models or [case.model_name for case in CASES])
    selected_cases = [case for case in CASES if case.model_name in selected_models]
    unknown_models = sorted(selected_models - {case.model_name for case in CASES})
    if unknown_models:
        print(f"Unknown model(s): {', '.join(unknown_models)}", file=sys.stderr)
        return 2

    try:
        results = [await _run_case(case) for case in selected_cases]
    except RefreshError as exc:
        print(f"ADC authentication error: {exc}", file=sys.stderr)
        print("Run `gcloud auth application-default login` and retry.", file=sys.stderr)
        return 2

    failures = 0
    for ok, message in results:
        prefix = "PASS" if ok else "FAIL"
        print(f"{prefix} {message}")
        if not ok:
            failures += 1

    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))```
