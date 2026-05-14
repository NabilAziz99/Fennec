"""
Legacy prompt templates — DEPRECATED.

These functions relied on the now-removed Subtask / ToolExecution dataclasses
and are no longer called by any agent.  All active agents use the modular
prompt builder in ``prompts/builder.py`` and ``prompts/sections.py``.

This file is kept solely so that stale third-party imports get a clear error
rather than an ``ImportError`` with no explanation.
"""
