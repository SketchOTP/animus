"""Skill/tool context protocol + auto-router beta module.

Import submodules explicitly (e.g. ``beta_config``, ``request_adapter``) so
lightweight callers — ANIMUS ``server.py`` config normalization — do not pull
heavy dependencies (``openai``, gateway helpers) through this package.
"""

__all__: list[str] = []
