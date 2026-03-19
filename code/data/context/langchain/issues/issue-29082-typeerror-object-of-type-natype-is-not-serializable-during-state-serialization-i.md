# TypeError: Object of type NAType is not serializable during state serialization in LangChain

**Issue #29082** | State: closed | Created: 2025-01-08 | Updated: 2026-03-06
**Author:** sharifamlani
**Labels:** bug, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

import pandas as pd
import numpy as np
import json

def debug_state(state):
    """Debug and identify keys with non-serializable data."""
    for key, value in state.items():
        try:
            json.dumps(value)  # Check JSON serialization
        except TypeError as e:
            print(f"Key '{key}' contains non-serializable data: {e}")

# Example Function
def final_return_node(state):
    """Simulate LangChain state serialization."""
    print("--- Simulating LangChain State Serialization ---")

    # Create a sample DataFrame with NAType
    working_data = pd.DataFrame({
        'column1': [1, pd.NA, 3],
        'column2': [4, 5, np.nan]
    })

    # Update state with DataFrame
    state["keys"] = {
        "working_data": working_data.to_dict(orient="records"),
    }

    # Debug state
    print("Debugging state for non-serializable data...")
    debug_state(state)

    # Attempt serialization
    try:
        json.dumps(state)  # Validate JSON serialization
        print("State passed JSON serialization.")
    except TypeError as e:
        print("JSON Serialization Error:", e)
        raise ValueError("State is not JSON-serializable.") from e

# Simulate State and Call Function
state = {}
try:
    final_return_node(state)
except Exception as e:
    print("Error:", str(e))


### Error Message and Stack Trace (if applicable)

--- Simulating LangChain State Serialization ---
Debugging state for non-serializable data...
Key 'working_data' contains non-serializable data: Object of type NAType is not JSON serializable
JSON Serialization Error: Object of type NAType is not JSON serializable
Traceback (most recent call last):
  File "example.py", line 40, in 
    final_return_node(state)
  File "example.py", line 33, in final_return_node
    json.dumps(state)  # Validate JSON serialization
  File "C:\Python\lib\json\__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
  File "C:\Python\lib\json\encoder.py", line 200, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "C:\Python\lib\json\encoder.py", line 258, in iterencode
    return _iterencode(o, 0)
  File "C:\Python\lib\json\encoder.py", line 179, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type NAType is not JSON serializable


### Description

### Description

I am encountering a persistent issue in LangChain where attempting to serialize a state containing a pandas DataFrame with `pd.NA` values results in a `TypeError: Object of type NAType is not JSON serializable`. This error occurs despite implementing various sanitization techniques to replace or handle non-serializable values.

#### What I'm Doing
- I have a node function (`final_return_node`) in a LangChain graph that processes a pandas DataFrame (`working_data`) and updates the graph’s state with the processed data.
- The state contains a dictionary with keys that include the processed DataFrame converted to a dictionary using `to_dict(orient="records")`.
- I am using LangChain in conjunction with **Human in the Loop** and **Command and Interrupt** features to modify and resume the graph's flow based on user input.
- The goal is to serialize the state for further processing and pass it to subsequent nodes in the workflow.

#### What I Expect to Happen
- After updating the state, I expect the state to be serialized successfully without errors, provided that all non-serializable values like `pd.NA` and `np.nan` are sanitized and replaced with JSON-serializable alternatives (`None`, strings, etc.).
- The node should return the serialized state to the next step in the graph workflow.

#### What Is Actually Happening
- Despite replacing `pd.NA` and `np.nan` with `None`, and validating the state using both `json.dumps` and `msgpack.packb`, LangChain still raises a `TypeError: Object of type NAType is not serializable`.
- The issue persists even after thorough sanitization, suggesting that LangChain's internal serialization logic is accessing or processing the original `pd.NA` values somewhere within the state or during serialization.

#### Steps Taken to Debug
1. Implemented a debugging function to identify non-serializable keys and values in the state.
2. Replaced all instances of `pd.NA` and `np.nan` in the DataFrame using:
   ```python
   .fillna("").replace({pd.NA: None, np.nan: None})
   ```
3. Serialized the state using both json.dumps and msgpack.packb for validation, confirming that the state passes these checks.
4. Logged the state and its sanitized version to verify that no pd.NA or other non-serializable values remain.
5. Despite these efforts, LangChain's internal serialization process continues to fail with the same error.


#### Hypothesis
- The issue might stem from LangChain's handling of the state internally, where it attempts to serialize a reference to the original, unsanitized DataFrame or retains some metadata associated with pandas extension types like pd.NA.
- Alternatively, LangChain’s serialization mechanism (e.g., MsgPack or custom serializers) may not correctly handle objects converted from pd.NA.

This bug is blocking my ability to process state updates and proceed through the LangChain graph workflow. It seems specific to LangChain's serialization implementation, as the sanitized state passes JSON and MsgPack validation outside of LangChain.

### System Info

 python -m langchain_core.sys_info
   
System Information
------------------
> OS:  Windows
> OS Version:  10.0.22631
> Python Version:  3.11.4 (tags/v3.11.4:d2340ef, Jun  7 2023, 05:45:37) [MSC v.1934 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 0.3.28
> langchain: 0.3.13
> langchain_community: 0.3.13
> langsmith: 0.2.6
> langchain_openai: 0.2.14
> langchain_text_splitters: 0.3.4
> langgraph_sdk: 0.1.48

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.11.11
> async-timeout: Installed. No version info available.
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.0
> jsonpatch: 1.33
> langsmith-pyo3: Installed. No version info available.
> numpy: 1.24.3
> openai: 1.58.1
> orjson: 3.10.12
> packaging: 23.2
> pydantic: 2.10.4
> pydantic-settings: 2.7.0
> PyYAML: 6.0.2
> requests: 2.31.0
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.36
> tenacity: 8.5.0
> tiktoken: 0.8.0
> typing-extensions: 4.12.2
> zstandard: Installed. No version info available.

## Comments

**dosubot[bot]:**
Hi, @sharifamlani. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- You reported a `TypeError` when serializing a DataFrame with `NAType` values in LangChain.
- Example code was provided to reproduce the issue.
- You confirmed the issue persists with the latest version of LangChain.
- No further comments or activity have been made on this issue.

**Next Steps:**
- Please let me know if this issue is still relevant to the latest version of LangChain by commenting here.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
