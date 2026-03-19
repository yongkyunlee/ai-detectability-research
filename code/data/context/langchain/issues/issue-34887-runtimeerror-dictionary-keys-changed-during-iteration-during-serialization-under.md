# RuntimeError: dictionary keys changed during iteration during serialization under thread concurrency

**Issue #34887** | State: open | Created: 2026-01-26 | Updated: 2026-03-18
**Author:** sugawara-miti0722
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Reproduction Steps / Example Code (Python)

```python
"""
# Run:
# uv run python mre_langchain_dict_race.py --iters 300000 --serial-threads 4 --invoke-threads 4

MRE: RuntimeError: dictionary changed size during iteration

狙い:
- Thread A: dumpd(prompt) で Serializable.to_json() が __dict__.items() を反復
- Thread B: prompt.invoke(...) で BasePromptTemplate._serialized (cached_property) が __dict__ に書き込み

タイミングが噛み合うと以下が発火することがあります（確率的）:
  RuntimeError: dictionary changed size during iteration
"""

from __future__ import annotations

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.load import dumpd
from langchain_core.prompts import ChatPromptTemplate

def main(
    *,
    iters: int,
    serial_threads: int,
    invoke_threads: int,
    reset_serialized_each_time: bool,
) -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            ("human", "{q}"),
        ]
    )

    start = threading.Event()
    stop = threading.Event()
    err: list[BaseException] = []

    def ser_worker(worker_id: int) -> None:
        start.wait()
        try:
            for _ in range(iters):
                if stop.is_set():
                    return
                dumpd(prompt)
        except BaseException as e:
            err.append(e)
            stop.set()

    def invoke_worker(worker_id: int) -> None:
        start.wait()
        try:
            for i in range(iters):
                if stop.is_set():
                    return
                if reset_serialized_each_time:
                    # cached_property のキャッシュを毎回外して、
                    # invoke() 内の self._serialized 参照で __dict__ に再書き込みさせる。
                    prompt.__dict__.pop("_serialized", None)
                # invoke() は内部で serialized=self._serialized を触るため
                # cached_property が __dict__ を更新しやすい
                prompt.invoke({"q": f"hi {worker_id}-{i}"})
        except BaseException as e:
            err.append(e)
            stop.set()

    with ThreadPoolExecutor(max_workers=serial_threads + invoke_threads) as ex:
        futures = []
        for wid in range(serial_threads):
            futures.append(ex.submit(ser_worker, wid))
        for wid in range(invoke_threads):
            futures.append(ex.submit(invoke_worker, wid))
        # 同時スタート
        start.set()
        for f in futures:
            f.result()

    if err:
        raise err[0]

    print(
        "Completed without error. "
        f"(iters={iters}, serial_threads={serial_threads}, invoke_threads={invoke_threads}, "
        f"reset_serialized_each_time={reset_serialized_each_time})"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=300_000)
    parser.add_argument("--serial-threads", type=int, default=4)
    parser.add_argument("--invoke-threads", type=int, default=4)
    parser.add_argument(
        "--no-reset-serialized-each-time",
        action="store_true",
        help="Disable popping _serialized cache each iteration (reduces repro rate).",
    )
    args = parser.parse_args()

    t0 = time.time()
    main(
        iters=args.iters,
        serial_threads=args.serial_threads,
        invoke_threads=args.invoke_threads,
        reset_serialized_each_time=not args.no_reset_serialized_each_time,
    )
    print(f"duration={time.time() - t0:.2f}s")
```

### Error Message and Stack Trace (if applicable)

```shell
/path/to/site-packages/langchain_core/globals.py:148: UserWarning: Importing debug from langchain root module is no longer supported. Please use langchain.globals.set_debug() / langchain.globals.get_debug() instead.
  old_debug = langchain.debug
Traceback (most recent call last):
  File "/path/to/mre_langchain_dict_race.py ", line 103, in 
    main(
    ~~~~^
        iters=args.iters,
        ^^^^^^^^^^^^^^^^^
    ......
        reset_serialized_each_time=not args.no_reset_serialized_each_time,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/path/to/mre_langchain_dict_race.py ", line 81, in main
    raise err[0]
  File "/path/to/mre_langchain_dict_race.py ", line 47, in ser_worker
    dumpd(prompt)
    ~~~~~^^^^^^^^
  File "/path/to/site-packages/langchain_core/load/dump.py", line 85, in dumpd
    return json.loads(dumps(obj))
                      ~~~~~^^^^^
  File "/path/to/site-packages/langchain_core/load/dump.py", line 64, in dumps
    return json.dumps(obj, default=default, **kwargs)
           ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/json/__init__.py", line 238, in dumps
    **kw).encode(obj)
          ~~~~~~^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/json/encoder.py", line 200, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/json/encoder.py", line 261, in iterencode
    return _iterencode(o, 0)
  File "/path/to/site-packages/langchain_core/load/dump.py", line 23, in default
    return obj.to_json()
           ~~~~~~~~~~~^^
  File "/path/to/site-packages/langchain_core/runnables/base.py", line 2652, in to_json
    dumped = super().to_json()
  File "/path/to/site-packages/langchain_core/load/serializable.py", line 207, in to_json
    for k, v in self:
                ^^^^
  File "/path/to/site-packages/pydantic/main.py", line 1196, in __iter__
    yield from [(k, v) for (k, v) in self.__dict__.items() if not k.startswith('_')]
                                     ~~~~~~~~~~~~~~~~~~~^^
RuntimeError: dictionary keys changed during iteration
```

### Description

Note: `reset_serialized_each_time` is only used to increase reproduction probability; in production this occurred naturally under thread concurrency (e.g., Runnable `.map()` / `.batch()` / LangGraph execution).

When serializing a Prompt/Runnable under thread concurrency, serialization sometimes fails with:

RuntimeError: dictionary keys changed during iteration

Repro uses multiple threads calling dumpd(prompt) while other threads call prompt.invoke() and reset the cached_property _serialized to force concurrent __dict__ mutation.

This originates from Serializable.to_json iterating via pydantic BaseModel.__iter__ (self.__dict__.items()) while another thread mutates __dict__ (e.g., cached_property writes).

Expected: serialization should not crash under thread concurrency.

### System Info

uv run python -m langchain_core.sys_info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.2.0: Tue Nov 18 21:07:05 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T6020
> Python Version:  3.13.7 (v3.13.7:bcee1c32211, Aug 14 2025, 19:10:51) [Clang 16.0.0 (clang-1600.0.26.6)]

Package Information
-------------------
> langchain_core: 0.3.79
> langchain: 0.3.27
> langchain_community: 0.3.31
> langsmith: 0.4.43
> langchain_aws: 0.2.35
> langchain_google_genai: 2.1.12
> langchain_text_splitters: 0.3.11
> langgraph_sdk: 0.2.9

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp=3.8.3: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> beautifulsoup4: 4.14.2
> bedrock-agentcore: Installed. No version info available.
> boto3: 1.40.35
> claude-agent-sdk>=0.1.0;: Installed. No version info available.
> dataclasses-json=0.6.7: Installed. No version info available.
> filetype=1.2: Installed. No version info available.
> google-ai-generativelanguage=0.7: Installed. No version info available.
> httpx-sse=0.4.0: Installed. No version info available.
> httpx=0.23.0: Installed. No version info available.
> httpx>=0.25.2: Installed. No version info available.
> jsonpatch=1.33.0: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.72: Installed. No version info available.
> langchain-core=0.3.75: Installed. No version info available.
> langchain-core=0.3.78: Installed. No version info available.
> langchain-core>=0.3.75: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=0.3.9: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langchain=0.3.27: Installed. No version info available.
> langsmith-pyo3>=0.1.0rc2;: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> langsmith=0.3.45: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> numpy: 2.1.0
> numpy>=1.26.2;: Installed. No version info available.
> numpy>=2.1.0;: Installed. No version info available.
> openai-agents>=0.0.3;: Installed. No version info available.
> opentelemetry-api>=1.30.0;: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http>=1.30.0;: Installed. No version info available.
> opentelemetry-sdk>=1.30.0;: Installed. No version info available.
> orjson>=3.10.1: Installed. No version info available.
> orjson>=3.9.14;: Installed. No version info available.
> packaging=23.2.0: Installed. No version info available.
> packaging>=23.2: Installed. No version info available.
> playwright: Installed. No version info available.
> pydantic: 2.11.10
> pydantic-settings=2.10.1: Installed. No version info available.
> pydantic=1: Installed. No version info available.
> pydantic=2: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pytest>=7.0.0;: Installed. No version info available.
> PyYAML=5.3.0: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> requests-toolbelt>=1.0.0: Installed. No version info available.
> requests=2: Installed. No version info available.
> requests=2.32.5: Installed. No version info available.
> requests>=2.0.0: Installed. No version info available.
> rich>=13.9.4;: Installed. No version info available.
> SQLAlchemy=1.4: Installed. No version info available.
> SQLAlchemy=1.4.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> typing-extensions=4.7.0: Installed. No version info available.
> vcrpy>=7.0.0;: Installed. No version info available.
> zstandard>=0.23.0: Installed. No version info available.

## Comments

**sugawara-miti0722:**
@ccurme @eyurtsev 
Hi,

We’re also hitting this problem in production under concurrent usage, and it seems to stem from iteration over mutable state during serialization.

I noticed there is a related PR (#35340). Is there any plan to merge or release a fix for this?

If helpful, I’m happy to test a patch on our side and report back. Thanks!

**gitbalaji:**
Hi, I have an open PR (#35340) that fixes this issue. Could you please assign this to me? Happy to address any review feedback.
