# Renderer Contract

## Scope

This document defines the minimum required behavior for a compatible `panelmark` renderer.

It is about behavior and API boundary, not internal implementation strategy.  A renderer
that satisfies all requirements here is considered core-compatible regardless of how it is
implemented internally.


## Core Principle

`panelmark` core owns the shell model.

A renderer owns:

- presentation
- event collection and input mapping
- focus routing into assigned interactions
- execution of draw commands
- any renderer-specific hosting or widget behavior


## What `panelmark` Core Provides

The following modules form the panelmark core API surface that renderers depend on.

| Component | Module | Role |
|-----------|--------|------|
| Shell definition parser | `panelmark.parser` | Converts the shell string into a `LayoutModel` tree |
| Layout model | `panelmark.layout` | `HSplit`, `VSplit`, `Panel`, `Region`; resolves geometry |
| `Shell` state machine | `panelmark.shell` | Assigns interactions, manages focus, dispatches keys, tracks dirty regions |
| `Interaction` ABC | `panelmark.interactions` | Abstract base: `render`, `handle_key`, `get_value`, `set_value`, `is_focusable`, `signal_return` |
| Draw command types | `panelmark.draw` | `WriteCmd`, `FillCmd`, `CursorCmd`, `RenderContext`, `DrawCommand` |
| Style tag parser | `panelmark.style` | Parses `<bold>text</>` markup in border titles |
| Exceptions | `panelmark.exceptions` | `RegionNotFoundError`, `CircularUpdateError` |

**`panelmark` has zero runtime dependencies.**  It does not import `blessed`, any GUI
toolkit, or any web framework.


## Required Capabilities

### 1. Shell Hosting

A renderer must be able to host a `panelmark.Shell` instance and drive it to completion.

Minimum responsibilities:

- resolve layout geometry for the target viewport
- render shell chrome (borders, headings, dividers) based on resolved geometry
- render each assigned interaction into its resolved region
- drive the event loop until the shell exits
- observe and act on shell exit signals

A renderer must provide a concrete `Shell` subclass with a `run()` method that sets up
the output surface, runs the event loop, and tears down the surface on exit.


### 2. Region Rendering

A renderer must render interactions into their resolved named regions.

Minimum responsibilities:

- construct a `RenderContext` for each region, using the known viewport dimensions and
  capability flags
- call `interaction.render(context, focused)` to obtain draw commands
- execute the returned command list through a command executor
- handle redraw after dirty state changes

The `Interaction.render()` contract:

```python
def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
    ...
```

- `context.width` / `context.height` — dimensions of the assigned region in character
  columns and rows.
- `context.supports(feature)` — capability query.  Known features: `'color'`,
  `'256color'`, `'truecolor'`, `'unicode'`, `'cursor'`, `'italic'`.
- **All coordinates in returned commands are region-relative.**  `(0, 0)` is the top-left
  cell of the region.  The executor maps region-relative coordinates to screen-absolute
  coordinates when executing commands.
- `render()` must have no side effects.  It returns data; it does not write output.

Interactions may branch on renderer capabilities inside `render()` via
`context.supports(feature)`.  They do not have direct access to terminal objects or
renderer internals.


### 3. Draw Command Execution

A renderer must correctly execute every draw command type defined in `panelmark.draw`.

Command types:

- `WriteCmd` — write text at a position, with optional style
- `FillCmd` — fill a region with a character
- `CursorCmd` — position the cursor

The executor is responsible for clipping.  Interactions should not emit commands that
exceed `context.width` columns from the given column, but the executor must handle
clipping defensively.

**Why draw commands, not direct output or a Canvas:** `render()` returns data rather than
performing side effects.  This keeps interactions as pure functions of state, which makes
them easy to unit-test by asserting on the returned command list without capturing stdout.
See `RENDER_ABSTRACTION.md` for the full design decision record.


### 4. Input Dispatch

A renderer must collect input events and route them through the shell.

Minimum responsibilities:

- collect input events from its surface
- convert them into the input form expected by `Shell.handle_key()`
- pass each event to `shell.handle_key(key)` and observe the return value

`Shell.handle_key(key)` returns either `('exit', value)` or `('continue', None)`.


#### Key string format

`Shell.handle_key` accepts a single `str` argument in one of three forms:

| Category | Form | Examples |
|----------|------|---------|
| Printable character | The character itself | `'a'`, `'Z'`, `' '`, `'\t'` |
| Named key | `KEY_` prefix | `'KEY_UP'`, `'KEY_DOWN'`, `'KEY_LEFT'`, `'KEY_RIGHT'`, `'KEY_ENTER'`, `'KEY_TAB'`, `'KEY_BTAB'`, `'KEY_BACKSPACE'`, `'KEY_DELETE'`, `'KEY_HOME'`, `'KEY_END'`, `'KEY_PGUP'`, `'KEY_PGDN'`, `'KEY_F1'`–`'KEY_F12'` |
| Control character | Literal escape value | `'\x11'` (Ctrl+Q), `'\x1b'` (Escape) |

These names are panelmark's canonical contract — they are not blessed-specific.  Any
renderer must map its native input events to these forms before calling `handle_key`.

By default, the base `Shell` treats `'\x1b'` (Escape) and `'\x11'` (Ctrl+Q) as exit
signals.  Renderers should pass them through unmodified so that the shell's exit
semantics are preserved.


### 5. Focus Handling

A renderer must honor shell focus behavior.

Minimum responsibilities:

- pass the correct `focused` boolean to `interaction.render(context, focused)` for each
  region
- route input to the focused interaction via shell dispatch
- support shell-level focus movement semantics

The spec does not constrain surface-specific focus affordances (cursor blinking, highlight
colors, etc.).  Those are renderer decisions.


### 6. Dirty / Redraw Behavior

A renderer must support redraw based on shell dirty state.

Minimum responsibilities:

- observe dirty regions after key handling or update operations
- redraw those regions
- call `shell.mark_all_clean()` after redraw

The spec does not constrain whether the renderer uses incremental redraw, full redraw,
retained buffers, or other optimizations.


#### Dirty-region tracking

`shell.dirty_regions` is a `set[str]` of region names that need re-rendering.  It is
updated by:

- `shell.handle_key(key)` — any interaction or focus change that modifies state marks
  affected regions dirty
- `shell.update(name, value)` — marks the named region dirty
- focus transitions — both the previously focused region and the newly focused region
  are added to the dirty set, so a renderer that re-renders only `dirty_regions` will
  automatically repaint focus changes without extra logic

`shell.mark_all_clean()` clears the dirty set.  Call it after the renderer has finished
re-rendering all dirty regions.

Expected render loop:

```python
while True:
    key = collect_input()          # renderer-specific
    result, value = shell.handle_key(key)
    for name in shell.dirty_regions:
        region = shell.get_region(name)
        interaction = shell.get_interaction(name)
        ctx = RenderContext(width=region.width, height=region.height, ...)
        cmds = interaction.render(ctx, focused=(name == shell.focused))
        executor.execute(region, cmds)
    shell.mark_all_clean()
    if result == 'exit':
        break
```


### 7. Shell Return Semantics

A renderer must implement shell return behavior consistently.

Minimum responsibilities:

- when `shell.handle_key(key)` returns `('exit', value)`, stop the current shell host and
  return `value` to the caller
- honor interaction `signal_return()` behavior through the shell


### 8. Interaction Semantics

The renderer must preserve the core interaction semantics.

- `get_value()` — returns current logical state
- `set_value(value)` — restores logical state
- `signal_return()` — explicit accept/submit behavior

The renderer is not responsible for inventing these semantics.  It must not break them.


## Optional Renderer Capabilities

The following are allowed but not required for core compatibility.

- modal shell hosting
- embedded shell hosting (non-fullscreen)
- mouse support
- clipboard integration
- native dialogs
- animation support
- timers and async repaint helpers
- accessibility integrations

Optional capabilities must be documented as renderer-specific unless they are part of the
portable standard library.  See [extensions.md](extensions.md).


## Compatibility Levels

See [extensions.md](extensions.md) for the full compatibility label definitions.  In
brief:

- `core-compatible` — implements this contract
- `portable-library-compatible` — also implements the portable widget layer
- `extended` — adds renderer-specific capabilities beyond the portable contract
