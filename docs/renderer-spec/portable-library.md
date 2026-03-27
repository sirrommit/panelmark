# Portable Standard Library

## Purpose

This layer sits above the core shell/runtime contract and below renderer-specific
libraries.  It defines optional but standardized portable interactions and widgets.

This layer is not required for core compatibility.  See [extensions.md](extensions.md)
for compatibility levels.


## Core Idea

If the project wants portable applications beyond the shell and interaction core, it needs
a standard portable library with:

- common names
- common call signatures
- common return semantics

while still allowing each renderer to choose the best implementation and visual shape for
its surface.


## Important Constraint

The portable standard library defines semantic contracts, not exact UI shape.

For example, a portable file picker may exist.  A TUI renderer may implement it as a
shell-defined browser.  A desktop renderer may implement it as a native file dialog.  A
web renderer may implement it as a browser file input.

The portable part is:

- how it is called
- what it returns
- what options it accepts
- cancellation semantics

Not:

- what regions it contains
- whether it is modal
- whether it uses native controls
- visual layout


## Recommended Scope

Keep the portable standard library small.

Good candidates for a minimal portable widget set:

- `Alert`
- `Confirm`
- `InputPrompt`
- `ListSelect`

Possible candidates, but higher risk of renderer-shape disagreement:

- `FilePicker`
- `Progress`

Not ideal as required portable minimum initially:

- `Toast`
- `DatePicker`
- `Spinner`

The larger the portable library becomes, the more likely renderers are forced into awkward
compatibility and the more likely portability claims drift from reality.


## Widget Contract Format

For each portable widget, the spec defines:

- name
- call syntax
- parameters
- return value
- cancellation semantics
- lifecycle semantics
- whether sync and async implementations are both acceptable


## Example: `Confirm`

- **Name:** `Confirm`
- **Parameters:**
  - `title: str = "Confirm"`
  - `message_lines: list[str] | None = None`
  - `buttons: dict | None = None`
- **Returns:** selected mapped value, or `None` on cancel if cancellation is allowed
- **Renderer freedom:** may be a native modal dialog, a shell-defined popup, or an inline
  confirmation control

The important thing is that the same application code can call the same API and receive the
same semantic result regardless of renderer.


## Relationship to Interactions

Portable widgets do not need to be single-region interactions.  They may be:

- interactions
- shell-based widget compositions
- native dialogs
- renderer-managed overlays

That is acceptable as long as the semantic API is stable.


## Open Questions

The portable library layer has not yet been adopted.  Before adding widgets here, the
project needs to decide:

- is the portable standard library required for renderer compatibility, or a higher tier?
- how much async variation is acceptable across renderers?
- how much parameter surface is allowed before APIs stop being portable?
