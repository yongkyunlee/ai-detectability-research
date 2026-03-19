# [BUG] async_execution=True loses ContextVar state — threading.Thread not using copy_context()

**Issue #4822** | State: closed | Created: 2026-03-12 | Updated: 2026-03-13
**Author:** danglies007
**Labels:** bug

### Description

  ## Summary      
                                                                                                              
  Tasks with `async_execution=True` are executed via `threading.Thread()` without copying
  the current `contextvars.Context`. This causes any `ContextVar` set on the calling thread
  to silently reset to its default value inside the worker thread.

  Related to #4168 (token tracking race condition) — same root cause, different symptom.

  ## Environment

  - crewai: 1.7.2 but checked 1.10.0.1
  - Python: 3.12

  ## Root Cause

  `execute_async()` in `task.py` spawns the worker thread without a context copy:

  ```python
  def execute_async(self, agent, context, tools) -> Future[TaskOutput]:
      future: Future[TaskOutput] = Future()
      threading.Thread(
          daemon=True,
          target=self._execute_task_async,
          args=(agent, context, tools, future),
      ).start()
      return future

  threading.Thread() does not inherit contextvars.Context from the spawning thread.
  asyncio.to_thread() and loop.run_in_executor() do, which is why the kickoff_async()
  path doesn't have this problem.
```

  ## Impact

  Libraries that rely on ContextVar for request-scoped state are silently broken for
  tasks using async_execution=True:

  - OpenTelemetry — trace context and baggage are lost. LLM calls inside these tasks
  appear as orphaned traces with no parent span.
  - Langfuse and other tracing SDKs — session context set on the calling thread is
  not visible in the worker.
  - Any custom ContextVar state — resets to default with no error raised.

### Steps to Reproduce

```
  import contextvars, threading

  my_var = contextvars.ContextVar("my_var", default=None)
  my_var.set("hello")

  threading.Thread(target=lambda: print(my_var.get())).start()
  # prints: None

  vs. asyncio.to_thread():

  import asyncio, contextvars

  my_var = contextvars.ContextVar("my_var", default=None)
  my_var.set("hello")

  async def main():
      await asyncio.to_thread(lambda: print(my_var.get()))
      # prints: hello

  asyncio.run(main())
```

### Expected behavior

  ContextVar values set on the calling thread should be accessible inside the worker                          
  thread spawned by async_execution=True, consistent with how asyncio.to_thread()                             
  and run_in_executor() behave.     

### Screenshots/Code snippets

```
  import contextvars, threading                                                                               
                                                                                                              
  my_var = contextvars.ContextVar("my_var", default=None)                                                     
  my_var.set("hello")                                                 
```                                        
                  
  # Current behaviour — context is lost
```
  threading.Thread(target=lambda: print(my_var.get())).start()
  # prints: None
```

  # Expected behaviour — context is preserved
```
  import asyncio
  async def main():
      await asyncio.to_thread(lambda: print(my_var.get()))
  asyncio.run(main())
  # prints: hello
```

### Operating System

Other (specify in additional context)

### Python Version

3.12

### crewAI Version

1.7.2

### crewAI Tools Version

1.7.2

### Virtual Environment

Venv

### Evidence

  Evidence:
  Verified by inspecting task.py in crewai 1.10.0.1:                                                          
                  
      def execute_async(self, agent, context, tools) -> Future[TaskOutput]:                                   
          future: Future[TaskOutput] = Future()
          threading.Thread(
              daemon=True,
              target=self._execute_task_async,
              args=(agent, context, tools, future),
          ).start()
          return future

  threading.Thread() does not copy contextvars.Context from the spawning thread.
  ContextVar values set before execute_async() is called read as their default
  values inside the worker thread. No exception is raised — the failure is silent.

  This affects OpenTelemetry (trace context lost, spans appear orphaned), Langfuse
  (session context lost), and any library using ContextVar for request-scoped state.

  Related: #4168 (token tracking race condition, same root cause), #4286 (open PR).

### Possible Solution

```
  import contextvars

  def execute_async(self, agent, context, tools) -> Future[TaskOutput]:
      future: Future[TaskOutput] = Future()
      ctx = contextvars.copy_context()
      threading.Thread(
          daemon=True,
          target=ctx.run,
          args=(self._execute_task_async, agent, context, tools, future),
      ).start()
      return future
```

  ## Workaround

  Use async def @listen with await crew.kickoff_async() inside asyncio.gather()
  instead of async_execution=True in sync crews — the async path propagates context
  correctly.

### Additional context

  References

  - #4168 — token tracking race condition in async_execution (same root cause)
  - #4286 — open PR for #4168
  - Python docs: contextvars.copy_context()
  - CPython: asyncio.to_thread implementation

## Comments

**gvelesandro:**
@danglies007 I'm researching failures where agent runtimes lose operational context at orchestration boundaries rather than from weak model reasoning. Your report is a strong example because request-scoped trace and session context disappear silently when `async_execution=True` hops threads.

If you're open to it, I'd value one short written postmortem here: https://www.agentsneedcontext.com/agent-failure-postmortem

I'm looking for five specifics: what the agent was trying to do, what context disappeared, where that context should have lived, what workaround you used, and what it cost. No pitch, just research.
