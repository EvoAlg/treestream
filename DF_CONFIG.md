# DF_CONFIG.md — Dark Factory Project Configuration

Version: v0.1.0
Project: TreeStream
Status: Active

This file sits at governance Level 2 alongside AGENT_RULES.md. It
defines which tools and models fill each DF role for this project.
It is human-authored and human-maintained only. No agent may modify
it under any circumstances.

In the Template Repo, fields marked [ASSIGN] are placeholders to be
filled in by the Human when instantiating a new DF project.

---

## Role Assignments

| Role | Tool / Model | Notes |
|------|-------------|-------|
| Human | [ASSIGN: operator name or identifier] | Sole authority for commits, deletions, AGENT_RULES.md and DF_CONFIG.md modifications, SPEC locked declarations |
| Spec Agent | Claude Code | Spec authorship, repo scaffolding, archive management, test stubs |
| Implementation Agent | Codex (via Cursor) | Implementation against locked SPEC.md, test execution |
| Adversarial Auditor | Claude (Project session) | Independent spec and implementation review; evaluation proxy for scenarios |

---

## Scenario Storage Model

Model A — out-of-repo storage.

Scenarios are held outside the repository in the Adversarial Auditor's
Claude Project session. The Implementation Agent has no access to
scenario content. This model is required because the Claude Code and
Codex workspace may index files via RAG.

---

## Governance Level Reminder

This file and AGENT_RULES.md sit at the same governance level (Level 2).
Neither supersedes the other:
- AGENT_RULES.md defines what each role may do
- This file defines which tool/model fills each role

Both must be consistent with the Dark Factory Methodology document
(Level 1). Any conflict between this file and AGENT_RULES.md must be
resolved by the Human — no agent may interpret its way past such a
conflict.

---

## Project Notes

- Primary test vehicle for Dark Factory Round 1
- SPEC.md is the single source of truth
- Full test suite: `$env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_core tests.test_exclusion_filter`
- Serialise repo: `python -m treestream serialize <source> <output>`
- Default exclusions via `.treestreamignore`: `.git`, `__pycache__`, `artifacts`, `fixtures`, `.claude`
- Methodology document: `DARK_FACTORY_METHODOLOGY_v2.3.md` (in this repo)
