<!-- markdownlint-disable-file MD041 -->

| Target | Source markdown | Built HTML |
| ------ | --------------- | ---------- |
| Page in `docs/` | `[runbook](other.md)` | unchanged (MkDocs handles it) |
| Repo file outside `docs/` | `[config](../backend/config.py)` | forge blob URL |
| Repo directory | `[scripts](../scripts/)` or `[scripts](../scripts)` | forge tree URL |
| Reference definition | `[cfg]: ../backend/config.py` | `[cfg]:` forge blob URL |
