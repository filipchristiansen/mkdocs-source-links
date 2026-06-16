---
name: github-issue-workflow
description: >-
  Create GitHub issues with conventional titles, structured bodies, and matching labels via gh.
  Use when the user asks to create a GitHub issue, file an issue, open an issue, gh issue,
  track this in an issue, or similar.
---

# GitHub issue workflow

## Create an issue

When the user asks to **create a GitHub issue** (or uses a short phrase like *"file an issue"*, *"open an issue"*, *"gh issue"*, *"track this in an issue"*, or similar), do the following without asking for confirmation unless something is ambiguous (e.g. title, scope, or which repo):

1. **Title**: Use a **clear, actionable title**. Prefer lowercase with a conventional prefix when it fits the work type: `fix:`, `feat:`, `chore:`, `docs:`, `refactor:`, `test:`, `enhance:` (same vocabulary as PRs). Keep it short; put detail in the body.
2. **Body**: Write a **structured description** from the user’s request, recent conversation, or referenced files. Use GitHub-flavored Markdown: headings, bullet lists, and `- [ ]` task items when the issue is a checklist. Link to relevant paths in the repo (e.g. `src/mkdocs_source_links/plugin.py`, `tests/test_rewrite.py`).
3. **Create**: Use `gh issue create` when available. For multiline bodies, use `--body-file` with a temporary file or a heredoc; avoid stuffing unescaped quotes in a single `--body` argument.
4. **Label**: If the title uses a conventional prefix, add the matching label: **fix**, **feat**, **chore**, **docs**, **refactor**, **test**, **enhance**. Use `gh issue create ... --label "<label>"` or `gh issue edit <number> --add-label "<label>"` after creation. Skip labels if the user specified none and prefix is unclear.
5. **Reply**: Return the **issue URL** (and number) to the user.

Infer title and body from context; if the user only says “create an issue” with no substance, ask what the issue should cover or which file to base it on.

Use `gh issue create` when available. If `gh` is not authenticated or the remote is not GitHub, say what failed and what the user should run locally.
