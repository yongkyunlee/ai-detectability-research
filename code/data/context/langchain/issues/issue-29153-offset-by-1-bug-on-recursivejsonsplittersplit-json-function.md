# Offset by 1 bug on RecursiveJsonSplitter::split_json() function

**Issue #29153** | State: open | Created: 2025-01-11 | Updated: 2026-03-07
**Author:** blupants
**Labels:** bug, text-splitters, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
from langchain_text_splitters import RecursiveJsonSplitter


input_data = {
  "projects": {
    "AS": {
      "AS-1": {}
    },
    "DLP": {
      "DLP-7": {},
      "DLP-6": {},
      "DLP-5": {},
      "DLP-4": {},
      "DLP-3": {},
      "DLP-2": {},
      "DLP-1": {}
    },
    "GTMS": {
      "GTMS-22": {},
      "GTMS-21": {},
      "GTMS-20": {},
      "GTMS-19": {},
      "GTMS-18": {},
      "GTMS-17": {},
      "GTMS-16": {},
      "GTMS-15": {},
      "GTMS-14": {},
      "GTMS-13": {},
      "GTMS-12": {},
      "GTMS-11": {},
      "GTMS-10": {},
      "GTMS-9": {},
      "GTMS-8": {},
      "GTMS-7": {},
      "GTMS-6": {},
      "GTMS-5": {},
      "GTMS-4": {},
      "GTMS-3": {},
      "GTMS-2": {},
      "GTMS-1": {}
    },
    "IT": {
      "IT-3": {},
      "IT-2": {},
      "IT-1": {}
    },
    "ITSAMPLE": {
      "ITSAMPLE-12": {},
      "ITSAMPLE-11": {},
      "ITSAMPLE-10": {},
      "ITSAMPLE-9": {},
      "ITSAMPLE-8": {},
      "ITSAMPLE-7": {},
      "ITSAMPLE-6": {},
      "ITSAMPLE-5": {},
      "ITSAMPLE-4": {},
      "ITSAMPLE-3": {},
      "ITSAMPLE-2": {},
      "ITSAMPLE-1": {}
    },
    "MAR": {
      "MAR-2": {},
      "MAR-1": {}
    }
  }
}

splitter = RecursiveJsonSplitter(max_chunk_size=216)
json_chunks = splitter.split_json(json_data=input_data)

input_data_DLP_5 = input_data.get("projects", {}).get("DLP", {}).get("DLP-5", None)
input_data_GTMS_10 = input_data.get("projects", {}).get("GTMS", {}).get("GTMS-10", None)
input_data_ITSAMPLE_2 = input_data.get("projects", {}).get("ITSAMPLE", {}).get("ITSAMPLE-2", None)

chunk_DLP_5 = None
chunk_GTMS_10 = None
chunk_ITSAMPLE_2 = None

for chunk in json_chunks:
    print(chunk)
    node = chunk.get("projects", {}).get("DLP", {}).get("DLP-5", None)
    if isinstance(node, dict):
        chunk_DLP_5 = node
    node = chunk.get("projects", {}).get("GTMS", {}).get("GTMS-10", None)
    if isinstance(node, dict):
        chunk_GTMS_10 = node
    node = chunk.get("projects", {}).get("ITSAMPLE", {}).get("ITSAMPLE-2", None)
    if isinstance(node, dict):
        chunk_ITSAMPLE_2 = node

print("\nRESULTS:")
if isinstance(chunk_DLP_5, dict):
    print(f"[PASS] - Node DLP-5 was found both in input_data and json_chunks")
else:
    print(f"[TEST FAILED] - Node DLP-5 from input_data was NOT FOUND in json_chunks")

if isinstance(chunk_GTMS_10, dict):
    print(f"[PASS] - Node GTMS-10 was found both in input_data and json_chunks")
else:
    print(f"[TEST FAILED] - Node GTMS-10 from input_data was NOT FOUND in json_chunks")

if isinstance(chunk_ITSAMPLE_2, dict):
    print(f"[PASS] - Node ITSAMPLE-2 was found both in input_data and json_chunks")
else:
    print(f"[TEST FAILED] - Node ITSAMPLE-2 from input_data was NOT FOUND in json_chunks")
```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

I am trying to use `langchain_text_splitters` library to split JSON content using the function `RecursiveJsonSplitter::split_json()`

For most cases it works, however I am experiencing some data being lost depending on the input JSON and the chunk size I am using.

I was able to consistently replicate the issue for the input JSON provided on my sample code. I always get the nodes "GTMS-10" and "ITSAMPLE-2" discarded when I split the JSON using `max_chunk_size=216`.

I noticed this issue always occurs with nodes that would be on the edge of the chunks. When you run my sample code, it will print all the 5 chunks generated:
```
python split_json_bug.py 

{'projects': {'AS': {'AS-1': {}}, 'DLP': {'DLP-7': {}, 'DLP-6': {}, 'DLP-5': {}, 'DLP-4': {}, 'DLP-3': {}, 'DLP-2': {}, 'DLP-1': {}}}}
{'projects': {'GTMS': {'GTMS-22': {}, 'GTMS-21': {}, 'GTMS-20': {}, 'GTMS-19': {}, 'GTMS-18': {}, 'GTMS-17': {}, 'GTMS-16': {}, 'GTMS-15': {}, 'GTMS-14': {}, 'GTMS-13': {}, 'GTMS-12': {}, 'GTMS-11': {}}}}
{'projects': {'GTMS': {'GTMS-9': {}, 'GTMS-8': {}, 'GTMS-7': {}, 'GTMS-6': {}, 'GTMS-5': {}, 'GTMS-4': {}, 'GTMS-3': {}, 'GTMS-2': {}, 'GTMS-1': {}}, 'IT': {'IT-3': {}, 'IT-2': {}, 'IT-1': {}}}}
{'projects': {'ITSAMPLE': {'ITSAMPLE-12': {}, 'ITSAMPLE-11': {}, 'ITSAMPLE-10': {}, 'ITSAMPLE-9': {}, 'ITSAMPLE-8': {}, 'ITSAMPLE-7': {}, 'ITSAMPLE-6': {}, 'ITSAMPLE-5': {}, 'ITSAMPLE-4': {}, 'ITSAMPLE-3': {}}}}
{'projects': {'ITSAMPLE': {'ITSAMPLE-1': {}}, 'MAR': {'MAR-2': {}, 'MAR-1': {}}}}

RESULTS:
[PASS] - Node DLP-5 was found both in input_data and json_chunks
[TEST FAILED] - Node GTMS-10 from input_data was NOT FOUND in json_chunks
[TEST FAILED] - Node ITSAMPLE-2 from input_data was NOT FOUND in json_chunks

```
Please, noticed that the 2nd chunk ends with node "GTMS-11" and the 3rd chunk starts with "GTMS-9". Same thing for chunks number 4 (ends with "ITSAMPLE-3") and chunk number 5 (starts with "ITSAMPLE-1")

Because the chunks "GTMS-10" and "ITSAMPLE-2" were lost on the edges of chunks, I believe that might a case of an "offset by 1 bug" on the RecursiveJsonSplitter::split_json() Python function.

Since I am calling it exactly how it is described in the [documentation](https://python.langchain.com/docs/how_to/recursive_json_splitter/#basic-usage) and I couldn't find any bug and discussion mentioning it, I thought I should file a bug for it.

 

### System Info

```console
(.venv) user@User-MacBook-Air split_json_bug % python -m langchain_core.sys_info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 23.6.0: Thu Sep 12 23:34:49 PDT 2024; root:xnu-10063.141.1.701.1~1/RELEASE_X86_64
> Python Version:  3.11.9 (main, Apr  2 2024, 08:25:04) [Clang 15.0.0 (clang-1500.3.9.4)]

Package Information
-------------------
> langchain_core: 0.3.29
> langsmith: 0.2.10
> langchain_text_splitters: 0.3.5

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langsmith-pyo3: Installed. No version info available.
> orjson: 3.10.14
> packaging: 24.2
> pydantic: 2.10.5
> PyYAML: 6.0.2
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> tenacity: 9.0.0
> typing-extensions: 4.12.2
> zstandard: Installed. No version info available.
```

```console
(.venv) user@User-MacBook-Air split_json_bug % pip freeze
annotated-types==0.7.0
anyio==4.8.0
certifi==2024.12.14
charset-normalizer==3.4.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
idna==3.10
jsonpatch==1.33
jsonpointer==3.0.0
langchain-core==0.3.29
langchain-text-splitters==0.3.5
langsmith==0.2.10
orjson==3.10.14
packaging==24.2
pydantic==2.10.5
pydantic_core==2.27.2
PyYAML==6.0.2
requests==2.32.3
requests-toolbelt==1.0.0
sniffio==1.3.1
tenacity==9.0.0
typing_extensions==4.12.2
urllib3==2.3.0
```

## Comments

**dosubot[bot]:**
Hi, @blupants. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- I identified an off-by-one error in `RecursiveJsonSplitter::split_json()`.
- I verified the issue persists in the latest version of LangChain.
- I provided example code illustrating the JSON data structure.
- There have been no further comments or activity on the issue.

**Next Steps:**
- Please confirm if this issue is still relevant with the latest version of LangChain by commenting here.
- If there is no further activity, the issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!

**blupants:**
> Hi, [@blupants](https://github.com/blupants). I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.
> 
> **Issue Summary:**
> 
> * I identified an off-by-one error in `RecursiveJsonSplitter::split_json()`.
> * I verified the issue persists in the latest version of LangChain.
> * I provided example code illustrating the JSON data structure.
> * There have been no further comments or activity on the issue.
> 
> **Next Steps:**
> 
> * Please confirm if this issue is still relevant with the latest version of LangChain by commenting here.
> * If there is no further activity, the issue will be automatically closed in 7 days.
> 
> Thank you for your understanding and contribution!

I can confirm the issue still persist.

I have just updated to the latest version:
```
langchain-core           0.3.51
langchain-text-splitters 0.3.8
```

I ran the example code after upgrading `langchain-text-splitters` and `langchain-core` and the bug is still active.

```
(.venv) sacchetin@Sacchetins-MacBook-Air split_json_bug % pip freeze
annotated-types==0.7.0
anyio==4.8.0
certifi==2024.12.14
charset-normalizer==3.4.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
idna==3.10
jsonpatch==1.33
jsonpointer==3.0.0
langchain-core==0.3.51
langchain-text-splitters==0.3.8
langsmith==0.2.10
orjson==3.10.14
packaging==24.2
pydantic==2.10.5
pydantic_core==2.27.2
PyYAML==6.0.2
requests==2.32.3
requests-toolbelt==1.0.0
sniffio==1.3.1
tenacity==9.0.0
typing_extensions==4.12.2
urllib3==2.3.0
```

**dosubot[bot]:**
@eyurtsev, the user has confirmed that the off-by-one error in `RecursiveJsonSplitter::split_json()` still persists even after updating to the latest versions of `langchain-core` and `langchain-text-splitters`. Could you please assist them with this issue?

**giulio-leone:**
I have opened a fix for this issue in #35621.

**Root cause:** When a key-value pair does not fit in the current chunk, `_json_split()` unconditionally recurses into the *value*. For leaf values (like empty dicts `{}`), the recursive call finds nothing to iterate — and the key is silently dropped.

**Fix:** Before recursing, check whether the item fits in the (potentially fresh) chunk. Only recurse when the value itself is too large and actually needs splitting.

The exact scenario from this issue (47 keys, `max_chunk_size=216`) is covered by a new regression test — all 47 keys are now preserved across chunks.
