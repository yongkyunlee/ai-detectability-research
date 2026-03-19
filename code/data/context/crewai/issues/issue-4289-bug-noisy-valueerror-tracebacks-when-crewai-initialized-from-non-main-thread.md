# [BUG] Noisy ValueError tracebacks when CrewAI initialized from non-main thread

**Issue #4289** | State: closed | Created: 2026-01-27 | Updated: 2026-03-02
**Author:** Bharath-designer
**Labels:** bug

### Description

When CrewAI is initialized from a thread other than the main thread (e.g., in Streamlit, Flask, Django, Jupyter, etc.), the telemetry module prints multiple `ValueError` tracebacks for each signal handler registration attempt. While these are caught and don't crash the application, they create confusing console output.

### Steps to Reproduce

1. Create a file `reproduce.py` with the following content:
```
import threading

def run_crewai_in_thread():
    from crewai import Agent  # Import triggers Telemetry singleton initialization
    
    print("CrewAI imported successfully in thread")

if __name__ == "__main__":
    print("Starting CrewAI import in non-main thread...\n")
    
    thread = threading.Thread(target=run_crewai_in_thread)
    thread.start()
    thread.join()
    
    print("\nDone")
```

2. Run the script:
```
python reproduce.py
```

3. Observe the output — multiple ValueError tracebacks are printed:
```
Starting CrewAI import in non-main thread...

Cannot register SIGTERM handler: not running in main thread
Traceback (most recent call last):
  File ".../crewai/telemetry/telemetry.py", line 214, in _register_signal_handler
    signal.signal(sig, handler)
ValueError: signal only works in main thread of the main interpreter

Cannot register SIGINT handler: not running in main thread
Traceback (most recent call last):
  ...
ValueError: signal only works in main thread of the main interpreter

(repeated for SIGHUP, SIGTSTP, SIGCONT)

CrewAI imported successfully in thread
Done.
```

### Expected behavior

Starting CrewAI import in non-main thread...

CrewAI telemetry: Skipping signal handler registration (not running in main thread). To disable this warning or disable crewai telemetry entirely, set CREWAI_DISABLE_TELEMETRY=true. See: https://docs.crewai.com/telemetry

CrewAI imported successfully in thread
Done.

### Screenshots/Code snippets

### Operating System

Other (specify in additional context)

### Python Version

3.12

### crewAI Version

1.9.0

### crewAI Tools Version

1.9.0

### Virtual Environment

Venv

### Evidence

### Possible Solution

### Proposed Solution

Add a proactive main thread check in `_register_shutdown_handlers()` before attempting signal registration.

**File:** `src/crewai/telemetry/telemetry.py`

**Current code (lines 170-183):**
```
def _register_shutdown_handlers(self) -> None:
    """Register handlers for graceful shutdown on process exit and signals."""
    atexit.register(self._shutdown)

    self._original_handlers: dict[int, Any] = {}

    self._register_signal_handler(signal.SIGTERM, SigTermEvent, shutdown=True)
    self._register_signal_handler(signal.SIGINT, SigIntEvent, shutdown=True)
    if hasattr(signal, "SIGHUP"):
        self._register_signal_handler(signal.SIGHUP, SigHupEvent, shutdown=False)
    if hasattr(signal, "SIGTSTP"):
        self._register_signal_handler(signal.SIGTSTP, SigTStpEvent, shutdown=False)
    if hasattr(signal, "SIGCONT"):
        self._register_signal_handler(signal.SIGCONT, SigContEvent, shutdown=False)
```

**Proposed fix:**
```
def _register_shutdown_handlers(self) -> None:
    """Register handlers for graceful shutdown on process exit and signals."""
    atexit.register(self._shutdown)

    self._original_handlers: dict[int, Any] = {}

    # Signal handlers can only be registered from the main thread
    if threading.current_thread() is not threading.main_thread():
        logger.warning(
            "CrewAI telemetry: Skipping signal handler registration (not running in main thread). "
            "To disable this warning or disable crewai telemetry entirely, set CREWAI_DISABLE_TELEMETRY=true. "
            "See: https://docs.crewai.com/telemetry"
        )
        return

    self._register_signal_handler(signal.SIGTERM, SigTermEvent, shutdown=True)
    self._register_signal_handler(signal.SIGINT, SigIntEvent, shutdown=True)
    if hasattr(signal, "SIGHUP"):
        self._register_signal_handler(signal.SIGHUP, SigHupEvent, shutdown=False)
    if hasattr(signal, "SIGTSTP"):
        self._register_signal_handler(signal.SIGTSTP, SigTStpEvent, shutdown=False)
    if hasattr(signal, "SIGCONT"):
        self._register_signal_handler(signal.SIGCONT, SigContEvent, shutdown=False)
```

### Additional context

Operating System: MacOS 15.7.3 (Sequoia)

## Comments

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
The `_register_signal_handler()` method was catching `ValueError` exceptions but logging them with `exc_info=e`, which prints the full traceback. This happened for each of the 5 signal handlers (SIGTERM, SIGINT, SIGHUP, SIGTSTP, SIGCONT) when CrewAI is initialized from a non-main thread.

**Fix:**
1. Added a proactive main thread check at the start of `_register_shutdown_handlers()` using `threading.current_thread() is not threading.main_thread()`
2. When not in the main thread, skip signal registration entirely with a clean debug-level log
3. Changed fallback exception handlers from `warning` with traceback to `debug` level without traceback

**What's preserved:**
- The `atexit` handler is still registered regardless of thread context, ensuring telemetry data is flushed on process exit
- Signal handlers are properly registered when running in the main thread

**Testing:**
Added regression test `test_no_noisy_output_when_initialized_from_non_main_thread` that verifies:
- No exceptions are raised when initializing Telemetry from a non-main thread
- No ValueError tracebacks appear in stdout/stderr

This matches the expected behavior outlined in the issue description.
