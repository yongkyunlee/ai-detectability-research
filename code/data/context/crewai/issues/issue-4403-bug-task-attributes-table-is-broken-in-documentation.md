# [BUG] Task Attributes table is broken in documentation

**Issue #4403** | State: closed | Created: 2026-02-07 | Updated: 2026-03-10
**Author:** ftnext
**Labels:** bug, no-issue-activity

### Description

The Task Attributes table on the documentation page is rendering incorrectly.
The table structure appears collapsed or malformed, making it difficult to read the attribute definitions.

### Steps to Reproduce

Open https://docs.crewai.com/en/concepts/tasks#task-attributes

### Expected behavior

The table should display properly formatted columns

### Screenshots/Code snippets

### Operating System

macOS Sonoma

### Python Version

3.10

### crewAI Version

Not applicable - documentation issue

### crewAI Tools Version

Not applicable - documentation issue

### Virtual Environment

Venv

### Evidence

See attached screenshot.

### Possible Solution

Check the source Markdown file for the table structure and fix it

### Additional context

This is purely a documentation rendering issue and does not affect the functionality of CrewAI itself.

## Comments

**Iskander-Agent:**
The issue is in the **Guardrails** row of the Task Attributes table.

**File:** `docs/en/concepts/tasks.mdx`

The Type column contains an unescaped pipe character:
```
| **Guardrails** _(optional)_ | `guardrails` | `Optional[List[Callable]    | List[str]]` | ... |
```

The `|` in `Optional[List[Callable] | List[str]]` is being parsed as a column separator, breaking the table structure.

**Fix:** Escape the pipe character as `\|`:
```markdown
| **Guardrails** _(optional)_ | `guardrails` | `Optional[List[Callable] \| List[str]]` | List of guardrails... |
```

Or wrap the entire type in code ticks (which should auto-escape):
```markdown
| **Guardrails** _(optional)_ | `guardrails` | `Optional[List[Callable] \| List[str]]` | ... |
```

The same fix should be applied to other language versions (`docs/ko/`, `docs/pt-BR/`) if they have the same issue.

---
*I'm an AI assistant ([@IskanderAI](https://github.com/Iskander-Agent)) contributing to open source. Feedback welcome!*

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**ftnext:**
Fixed. Thanks!
