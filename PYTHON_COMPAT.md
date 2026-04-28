# Python Version Compatibility Log

This file tracks CPython changes that broke `logger_tt` and how each was resolved
while maintaining backward compatibility with older versions.

Tested range: **Python 3.7 -- 3.14** (via `nox`, see `noxfile.py`)

---

## Python 3.13 -- `StackSummary.format_frame_summary` became instance-dependent

**Broke in:** 3.13.0  
**Detected:** 2026-04  
**Affected file:** `logger_tt/inspector.py` (`get_basic_exception_info`)

### What changed

`traceback.StackSummary.format_frame_summary` added a call to
`self._should_show_carets(...)` internally. Previously the method did not
reference `self` in a way that required a real instance, so the codebase
called it as an unbound method with `None`:

```python
# Worked on 3.11-3.12, crashes on 3.13+
data = StackSummary.format_frame_summary(None, summary)
```

On 3.13 this raises `AttributeError: 'NoneType' object has no attribute
'_should_show_carets'`.

### Fix

Create a real `StackSummary` instance wrapping the single frame:

```python
data = StackSummary([summary]).format()[0]
```

This works identically on 3.11-3.14 and doesn't affect older versions
(the code path is guarded by `colno` presence, which only exists on 3.11+).

### Compat guard

```python
if not getattr(summary, 'colno', None):
    # Pre-3.11: format manually
else:
    # 3.11+: use StackSummary([summary]).format()[0]
```

---

## Python 3.13 -- Caret indicator style change (`^` to `~`/`^`)

**Broke in:** 3.13.0 (test-only)  
**Detected:** 2026-04  
**Affected file:** `tests/test_inspector.py` (`test_py_311`)

### What changed

Python 3.13 changed traceback caret indicators to distinguish context from
the actual error:

```
# 3.11-3.12
    return lel2(x) / 23
           ^^^^^^^

# 3.13+
    return lel2(x) / 23
           ~~~~^^^
```

Additionally, 3.13 adds indicator lines to frames that previously had none
(e.g., simple function calls like `lel3(xx)`).

### Fix

Version-conditional expected output in the test:

```python
if sys.version_info >= (3, 13):
    expected_traceback = r"""...~~~~^^^..."""
else:
    expected_traceback = r"""...^^^^^^^..."""
```

No library code change was needed -- the traceback output is correct on
both versions, just formatted differently by CPython.

---

## Python 3.11 -- Traceback column indicators

**Broke in:** n/a (new feature)  
**Handled in:** prior to v1.7.4  
**Affected file:** `logger_tt/inspector.py`

### What changed

Python 3.11 added fine-grained column indicators to tracebacks
(`colno`/`end_colno` on `FrameSummary`). The private API
`_walk_tb_with_full_positions` replaced `walk_tb` for extracting this info.

### Compat guard

```python
try:
    from traceback import StackSummary, _walk_tb_with_full_positions as walk_tb
    stack_summary_extract = StackSummary._extract_from_extended_frame_gen
except ImportError:
    from traceback import StackSummary, walk_tb
    stack_summary_extract = StackSummary.extract
```

---

## Python 3.10 -- Logging `FileHandler` re-opens after `shutdown()`

**Broke in:** 3.10.0  
**Handled in:** prior to v1.7.4  
**Affected file:** `logger_tt/core.py` (`LogConfig.__exit__`)

### What changed

CPython commit `45df61fd` added a workaround in `logging.shutdown()` that
re-opens `FileHandler` streams to avoid a `NameError` on the `open` builtin.
This means `FileHandler`s stay open after `logging.shutdown()`.

### Fix

Explicitly close `FileHandler`s after stopping `QueueListener`:

```python
for handler in ql.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.close()
```

---

## Python 3.8 -- `stacklevel` parameter in `Logger._log()`

**Broke in:** n/a (new parameter)  
**Handled in:** prior to v1.7.4  
**Affected file:** `logger_tt/enhanced_class.py` (`ExceptionLogger._log`)

### What changed

Python 3.8 added the `stacklevel` parameter to `Logger._log()`. Calling
`super()._log(..., stacklevel=2)` on 3.7 raises `TypeError`.

### Compat guard

```python
PY_VER = sys.version_info.major, sys.version_info.minor

if PY_VER > (3, 7):
    super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)
else:
    super()._log(level, msg, args, exc_info, extra, stack_info)
```

---

## Python 3.7 -- `tokenize` behavior change

**Broke in:** 3.7.0 (test-only)  
**Affected file:** `tests/test_inspector.py` (`test_multiline`)

### What changed

The `tokenize` module changed behavior for multi-line statement detection,
causing `test_multiline` to produce different results.

### Fix

Test is skipped on 3.7+:

```python
@pytest.mark.skipif(sys.version_info >= (3, 7),
                    reason="'tokenize' module changed behavior")
```
