# [FEATURE] Agent Loop Detection Middleware — detect and break repetitive behavioral patterns

**Issue #4682** | State: open | Created: 2026-03-03 | Updated: 2026-03-03
**Author:** sicmundu

## Feature Area
Core functionality / Agent behavior

## Description
When agents run in autonomous loops (especially with `allow_delegation=True` or complex multi-step tasks), they can fall into repetitive behavioral patterns — executing the same sequence of actions, re-researching the same information, or generating similar outputs across iterations without making real progress toward the goal.

## Proposed Solution: Agent Loop Detection Middleware

A lightweight middleware layer that monitors agent action history and detects repetitive patterns in real-time. When a loop is detected, the middleware could:

1. **Detect repetition** — Track a sliding window of recent actions/tool calls and flag when similarity exceeds a threshold (e.g., same tool called 3+ times with similar arguments)
2. **Escalate or intervene** — Automatically inject a meta-prompt like "You appear to be repeating actions. Consider a different approach" or trigger a configurable callback
3. **Log loop events** — Emit structured telemetry so users can diagnose where agents get stuck

### Example API sketch:

```python
from crewai import Agent, Crew
from crewai.middleware import LoopDetector

loop_detector = LoopDetector(
    window_size=5,           # actions to track
    similarity_threshold=0.8, # how similar actions need to be
    on_loop="inject_reflection",  # or "stop", "callback", "escalate_to_manager"
)

agent = Agent(
    role="Researcher",
    goal="Find novel insights about X",
    middleware=[loop_detector],
)
```

## Why This Matters

This is a well-known failure mode in autonomous agent systems. In my experience building and running long-lived autonomous agents, loop detection is one of the most impactful reliability improvements you can add. Agents that run for extended periods (100+ iterations) inevitably encounter states where they repeat without progress — and without detection, they burn tokens and time.

The CrewAI framework is well-positioned to solve this at the framework level rather than leaving it to individual implementations.

## Additional Context

Related concepts:
- [LangGraph's cycle detection](https://langchain-ai.github.io/langgraph/) in graph-based agent flows
- The `max_iter` parameter in CrewAI already provides a crude upper bound, but doesn't detect *behavioral* repetition
- Research on "agent drift" and metacognitive monitoring in autonomous systems

Happy to contribute a proof-of-concept implementation if there's interest.

## Comments

**sicmundu:**
## Implementation Proposal: Loop Detection Middleware

After further research and experimentation with autonomous agent loops, here's a concrete implementation approach:

### Architecture

```python
from collections import deque
from hashlib import sha256
from typing import Optional

class LoopDetector:
    """Middleware that detects repetitive agent behavior patterns."""
    
    def __init__(self, window_size: int = 10, similarity_threshold: float = 0.85, max_repeats: int = 3):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.max_repeats = max_repeats
        self.action_history: deque = deque(maxlen=window_size * 2)
        self.pattern_cache: dict = {}
    
    def record_action(self, action_type: str, action_content: str, result_summary: str) -> None:
        """Record an agent action for pattern analysis."""
        fingerprint = self._fingerprint(action_type, action_content)
        self.action_history.append({
            "type": action_type,
            "fingerprint": fingerprint,
            "result_hash": sha256(result_summary.encode()).hexdigest()[:8]
        })
    
    def detect_loop(self) -> Optional[dict]:
        """Check if the agent is stuck in a loop. Returns loop info or None."""
        if len(self.action_history)  threshold)
        type_counts = {}
        for a in list(self.action_history)[-self.window_size:]:
            type_counts[a["type"]] = type_counts.get(a["type"], 0) + 1
        for action_type, count in type_counts.items():
            if count / self.window_size > self.similarity_threshold:
                return {"type": "action_clustering", "dominant_action": action_type, "ratio": count/self.window_size}
        
        return None
    
    def suggest_intervention(self, loop_info: dict) -> str:
        """Suggest how to break the detected loop."""
        if loop_info["type"] == "exact_repeat":
            return "BREAK: Exact action sequence repeating. Try a fundamentally different approach."
        elif loop_info["type"] == "action_clustering":
            return f"WARNING: {loop_info['dominant_action']} dominates recent actions ({loop_info['ratio']:.0%}). Diversify your approach."
        return "Consider changing strategy."
    
    def _fingerprint(self, action_type: str, content: str) -> str:
        return sha256(f"{action_type}:{content[:200]}".encode()).hexdigest()[:12]
```

### Integration Point

This could hook into CrewAI's `AgentExecutor` or the task execution pipeline. The key integration points:

1. **Before each tool call**: `detector.record_action(tool_name, tool_input, prev_result)`
2. **After recording**: `loop_info = detector.detect_loop()`  
3. **On detection**: Inject a system message like `"Loop detected: you've repeated this pattern {n} times. Try a different approach."` or force-escalate to human/different agent.

### Why This Matters

Speaking from experience running autonomous agent loops: the failure mode isn't catastrophic errors — it's *subtle repetition*. An agent researching the same topic repeatedly, re-analyzing the same file, or cycling between two actions without converging. This middleware catches those patterns early.

Happy to submit a PR implementing this if there's interest from maintainers. Would integrate with the existing callback/middleware system.
