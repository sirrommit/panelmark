# Claude Instructions for panelmark

This repository is `panelmark`, the core package. Treat it as independently releasable.

## Scope

- Work only inside `/home/sirrommit/claude_play/panelmark` by default.
- Do not read, edit, or search `../panelmark-tui` unless the user explicitly asks.
- Do not rely on `panelmark-tui` to understand or justify `panelmark` changes.

## Dependency direction

- `panelmark` must remain conceptually independent of `panelmark-tui`.
- Do not make changes to `panelmark` that require `panelmark-tui` changes unless that is
  genuinely required.
- If a `panelmark` change would require `panelmark-tui` to change how it interacts with
  `panelmark`, stop and get explicit user approval before making that `panelmark` change.

## Only allowed edit outside this repo

The only file you may edit outside this repo is:

- `/home/sirrommit/claude_play/panelmark-tui/UPDATES.md`

And only under all of these conditions:

1. A change in `panelmark` requires `panelmark-tui` to change how it interacts with
   `panelmark`
2. The user has explicitly approved making that `panelmark` change
3. You are only recording the required follow-up for `panelmark-tui`

Do not edit any other file in `../panelmark-tui`.

## Context-efficiency rules

- Minimize context usage.
- Start with the smallest useful file set:
  1. User request
  2. `README.md`
  3. Relevant docs in `docs/`
  4. The specific implementation file being changed
  5. The smallest relevant test file
- Do not scan the whole repo by default.
- Prefer targeted `rg` searches and partial file reads.

## Validation

Every change must be tested before completion.

- Run the narrowest relevant test first.
- If the change is broader, run:
  - `cd /home/sirrommit/claude_play/panelmark && pytest -q`
- For doc-only changes, run the nearest relevant check if one exists; otherwise say that no
  automated doc check exists.

## Git

Each completed update should be committed and pushed unless the user says not to.

- Remote: `origin git@github.com:sirrommit/panelmark.git`
- Default branch: `main`

Before pushing:

- Check `git status --short`
- Confirm only intended files changed
- Use a clear scoped commit message

## Working style

- Make the smallest change that fully solves the task.
- Do not perform speculative cleanup.
- Preserve unrelated user changes.
- If a change appears to cross the repo boundary, pause and ask for approval unless the user
  already gave it.
