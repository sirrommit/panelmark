# Extensions and Compatibility

## Purpose

This document defines how renderers should expose nonstandard additions and how
compatibility levels should be described.


## Why Extension Policy Matters

Without an extension policy:

- renderer-specific features appear portable when they are not
- documentation becomes ambiguous
- applications accidentally depend on nonportable behavior


## Extension Rule

Renderer-specific additions are allowed, but they must be clearly marked as
renderer-specific.

This applies to:

- interactions
- widgets
- helpers
- hosting modes
- native integrations


## Marking Rules

Nonstandard additions must:

- live under the renderer package namespace
- be documented as renderer-specific
- not be presented as part of the portable contract unless formally standardized

Examples:

- `panelmark_tui.Toast` is renderer-specific unless added to the portable standard library
- `panelmark_qt.NativeFileDialog` is renderer-specific


## Compatibility Labels

Renderers should declare one of the following compatibility levels.


### `core-compatible`

The renderer implements the required shell and interaction hosting contract defined in
[contract.md](contract.md).  This is the minimum for any compatible renderer.


### `portable-library-compatible`

The renderer implements the core contract and also implements the portable standard
library defined in [portable-library.md](portable-library.md).


### `extended`

The renderer implements the core contract (and optionally the portable library) and also
provides renderer-specific additions beyond the portable contract.

Extended additions must be documented as renderer-specific.


## Documentation Expectations

Every renderer should document:

- which compatibility level it claims
- which portable widgets or interactions it implements (if claiming portable-library
  compatibility)
- which additions are renderer-specific
- any known limitations or deviations from the spec


## Deviation Policy

A renderer may:

- omit optional capabilities (those listed in the contract as optional)
- provide approximations for portable features if call syntax and return semantics remain
  intact

A renderer must not:

- claim compatibility while changing call syntax or return semantics for standardized APIs


## Open Questions

- Whether compatibility claims are self-declared or backed by a conformance test suite
- How strict approximation rules should be for portable widgets
