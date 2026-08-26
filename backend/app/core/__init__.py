"""Core subscription-detection engine: ingestion, merchant normalization,
recurrence detection, pricing analysis, evaluation, and report rendering.
Pure logic, no I/O framework or LLM dependency - this layer is what's
actually being tested and is safe to reuse outside the API (e.g. a CLI).
"""
