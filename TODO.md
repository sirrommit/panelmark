# TODO — panelmark

This file tracks work that should be done in the `panelmark` core repository. It should stay
focused on the core package and not include renderer-specific implementation work.

## Current priorities

- [ ] Add a validation pass for shell definitions so structurally irregular layouts can be rejected explicitly instead of being accepted by the permissive parser.
- [ ] Document the validation boundary clearly once it exists:
  - what parsing accepts
  - what validation rejects
  - what errors callers should expect
- [ ] Keep the renderer-boundary documentation current as the core `Shell`, layout, or draw-command contracts evolve.

## Developer workflow

- [ ] Add a local `CONTRIBUTING.md` for `panelmark` with core-only test commands, architecture notes, and guidance on when a change may require renderer follow-up.
- [ ] Add a small `Makefile` or `justfile` for common `panelmark` tasks such as `test`.

## Future design work

- [ ] Only after the core contracts are stable, do serious design work for additional renderers such as `panelmark-html`.
- [ ] If a core change would require `panelmark-tui` to change how it interacts with `panelmark`, record the required follow-up in `/home/sirrommit/claude_play/panelmark-tui/UPDATES.md` only after explicit user approval.
