# Agents always load trained_agents_data.pkl, ignoring custom filename; custom training file not respected on inference

**Issue #4905** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** manoharnv
**Labels:** bug

### Description

When training a CrewAI crew with a custom file name (`-f .pkl`), the consolidated agent guidance is correctly written to the given path (e.g., `my_custom_trained.pkl`). However, during normal (non-training) execution, agents **always** load from the hardcoded `trained_agents_data.pkl`, ignoring the custom file supplied at training time.

---
**Relevant code:**
```python
    if data := CrewTrainingHandler(TRAINED_AGENTS_DATA_FILE).load():  # ❌ HARDCODED!
```
From `agent/core.py`

### Steps to Reproduce

1. Train a crew with a custom file:
   ```shell
   crewai train -n 5 -f my_custom_trained.pkl
   ```
2. Observe that `my_custom_trained.pkl` is created and populated after training.
3. Run the crew (or agents) for inference **without renaming** the file.
4. The agents will not use your custom file; only `trained_agents_data.pkl` is loaded.

### Expected behavior

Agents should be able to load and apply trained suggestions from the actual file used in training, not just `trained_agents_data.pkl`. Ideally, the system should either:
- Track and propagate the custom path used (e.g., as `Crew(..., trained_file="my_custom_trained.pkl")`), **or**
- Provide an API, environment variable, or config to specify the trained data file to read during inference, **or**
- At minimum, clearly warn users and suggest renaming the file post-training.

### Screenshots/Code snippets

```python
    if data := CrewTrainingHandler(TRAINED_AGENTS_DATA_FILE).load():  # ❌ HARDCODED!
```
**File:** `agent/core.py` (lines 3-3)

### Operating System

Other (specify in additional context)

### Python Version

3.12

### crewAI Version

N/A

### crewAI Tools Version

N/A

### Virtual Environment

Venv

### Evidence

Trained models saved to custom path are not respected in inference; always loads `trained_agents_data.pkl` by default. Only workaround is to rename the file manually.

### Possible Solution

- Accept a `trained_file` parameter when instantiating a Crew or agent so this path is respected everywhere.
- Fall back to `trained_agents_data.pkl` only when no custom filename is provided.
- Add documentation warnings if this is intentional

### Additional context

This is especially confusing for multi-experiment workflows, CI, cloud, or production runs where explicit filenames are essential.
