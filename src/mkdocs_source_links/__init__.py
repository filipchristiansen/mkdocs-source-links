"""MkDocs plugin: rewrite ../ repo links to forge view URLs during on_page_markdown."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mkdocs-source-links")
except PackageNotFoundError:  # package not installed (e.g. running from source)
    __version__ = "0.0.0.dev0"
