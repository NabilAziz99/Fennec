"""FastAPI server for the OSS dashboard.

This package provides an HTTP+SSE surface over the agent loop so the
React dashboard at frontend/ can drive scans and read results. The
implementation is single-process and in-memory — no database, no queue.
For production use, run one server per user/machine.
"""
