"""MkDocs plugin: rewrite `[text](../path)` and `[ref]: ../path` links to forge view URLs.

Runs during `on_page_markdown`.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mkdocs-source-links")
except PackageNotFoundError:  # package not installed (e.g. running from source)
    __version__ = "0.0.0.dev0"
