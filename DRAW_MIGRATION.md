# Migration Plan: Option 3 — Render to Draw Commands

This document is a fully actionable migration plan for replacing the
`Interaction.render(region, term, focused)` interface with a pure,
side-effect-free `render(context, focused) -> list[DrawCommand]` interface.

The rationale for choosing Option 3 over Option 2 (Canvas abstraction) is in
`RENDER_ABSTRACTION.md`. Short version: draw commands allow diffing,
optimisation, serialisation, and pure-function testing. They follow the same
architectural pattern as React (virtual DOM), Flutter (widget tree), and
SwiftUI (value-type views).

---

## Design Decisions

### 1. `RenderContext` replaces both `region` and `term`

The current signature passes `region` so interactions know their width and
height, and `term` so they can draw. After this migration, `RenderContext`
carries the dimensions and capability metadata. The renderer builds a
`RenderContext` for each region before calling `render()`.

```python
# panelmark/draw.py
from dataclasses import dataclass, field

@dataclass(frozen=True)
class RenderContext:
    width: int
    height: int
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def supports(self, feature: str) -> bool:
        """Query renderer capability.

        Known feature strings (renderers may support any subset):
          'color'     — at least 8 colours available
          '256color'  — 256-colour palette available
          'truecolor' — 24-bit colour available
          'unicode'   — Unicode block/box characters render correctly
          'cursor'    — a text cursor can be positioned (TUI, interactive web)
          'italic'    — italic text is visually distinct from normal

        Returns False for unknown or unsupported features.
        """
        return feature in self.capabilities
```

`region` is removed from `render()` entirely. Interactions never need to know
their absolute screen position — that is the executor's concern.

### 2. Draw command types

```python
# panelmark/draw.py (continued)
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class WriteCmd:
    """Write styled text at region-relative (row, col).

    Coordinates are zero-based and region-relative:
    (0, 0) is the top-left cell of the interaction's assigned region.
    The executor maps these to screen-absolute coordinates internally.

    style dict keys (all optional):
        bold      bool
        italic    bool
        underline bool
        reverse   bool
        color     str   — foreground colour name ('red', 'blue', 'green', ...)
        bg        str   — background colour name
    """
    row: int
    col: int
    text: str
    style: dict | None = None


@dataclass
class FillCmd:
    """Fill a rectangle with a repeated character, optionally styled.

    Same coordinate system and style dict as WriteCmd.
    """
    row: int
    col: int
    width: int
    height: int
    char: str = ' '
    style: dict | None = None


@dataclass
class CursorCmd:
    """Hint: place the text cursor at region-relative (row, col).

    Renderers may ignore this. TUI renderers use it to position the
    terminal cursor for blinking-cursor feedback. HTML static renderers
    ignore it; interactive web renderers may translate it to a CSS caret.
    """
    row: int
    col: int


DrawCommand = WriteCmd | FillCmd | CursorCmd
```

### 3. New `Interaction.render()` signature

```python
# panelmark/interactions/base.py (after migration)
@abstractmethod
def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
    """Return draw commands describing the current visual state.

    Commands use region-relative coordinates: (0, 0) is the top-left
    cell of this interaction's assigned region. The renderer maps them
    to screen-absolute positions when executing.

    The returned list must be a complete description of the interaction's
    visual state — the executor may skip calling render() for regions it
    determines are unchanged (future optimisation).
    """
    ...
```

### 4. Executor in `panelmark-tui`

`panelmark_tui/executor.py` translates a `list[DrawCommand]` to blessed
terminal output. It takes `region` to handle the row/col offset mapping:

```python
class TUICommandExecutor:
    def __init__(self, term):
        self._term = term

    def execute(self, commands: list[DrawCommand], region: Region) -> None:
        """Execute commands against the terminal, offset by region position."""
        for cmd in commands:
            if isinstance(cmd, WriteCmd):   self._write(cmd, region)
            elif isinstance(cmd, FillCmd):  self._fill(cmd, region)
            elif isinstance(cmd, CursorCmd): self._cursor(cmd, region)
        # Caller is responsible for sys.stdout.flush()
```

Style translation from the dict to blessed sequences lives in the executor
(or a helper in `style.py`). It does not live in the draw commands themselves.

### 5. `build_render_context()` factory in `panelmark-tui`

```python
# panelmark_tui/context.py
def build_render_context(region: Region, term) -> RenderContext:
    caps = set()
    if term.number_of_colors >= 8:
        caps.add('color')
    if term.number_of_colors >= 256:
        caps.add('256color')
    if term.number_of_colors >= 2**24:
        caps.add('truecolor')
    caps.add('cursor')
    caps.add('unicode')   # blessed terminals support unicode; gate if needed
    return RenderContext(
        width=region.width,
        height=region.height,
        capabilities=frozenset(caps),
    )
```

---

## Web Renderer Compatibility

Nothing in this design blocks the future `panelmark-html` or `panelmark-web`
renderers. Specific notes:

- **Coordinates**: `WriteCmd(row, col)` uses cell-grid coordinates. HTML
  renders these as a CSS grid with character-sized cells (e.g. `ch`/`em`
  units), or as absolute positioning. The row/col model already used by the
  layout engine maps cleanly to either.

- **Style dict**: Keys are renderer-agnostic strings. `panelmark-html` maps
  `bold → font-weight:bold`, `color:'red' → color:red`, `reverse` →
  swap fg/bg, etc. No terminal escape codes appear in DrawCommands.

- **`CursorCmd`**: Static HTML renderers ignore it. An interactive web
  renderer maps it to a CSS caret position or a JS-managed cursor overlay.

- **`RenderContext.supports()`**: The HTML renderer builds its own
  `RenderContext` with capabilities appropriate to its output:
  - Static: `{'color', '256color', 'truecolor', 'unicode'}` — no `'cursor'`
  - Interactive web: adds `'cursor'` when the client has focus

- **No terminal imports anywhere in DrawCommands or RenderContext.** The draw
  module has zero dependencies. A future web renderer imports only
  `panelmark.draw`, not `panelmark_tui` anything.

- **Executor pattern**: Each renderer provides its own executor that consumes
  `list[DrawCommand]`. `TUICommandExecutor` is the first; `HTMLCommandExecutor`
  is the second. The interface is implicit (duck-typed) — no executor ABC is
  needed in core.

- **Row/column vs pixels**: `WriteCmd` and `FillCmd` assume a character-grid
  model. Tkinter and Qt work in pixels. When a desktop renderer is built, the
  executor converts row/col to pixel coordinates using a fixed character cell
  size. This is a local concern of the executor and does not require changing
  the draw command types.

---

## TODO List

Tasks are ordered by dependency. Complete each phase before beginning the next.

---

### Phase 1 — Core: draw module ✓

- [x] **Create `panelmark/draw.py`**
  - Define `RenderContext` as a frozen dataclass with `width`, `height`,
    `capabilities: frozenset[str]`, and `supports(feature) -> bool`
  - Define `WriteCmd(row, col, text, style=None)`
  - Define `FillCmd(row, col, width, height, char=' ', style=None)`
  - Define `CursorCmd(row, col)`
  - Define `DrawCommand = WriteCmd | FillCmd | CursorCmd` type alias
  - Full docstrings on all classes and fields (this is the public API)

- [x] **Update `panelmark/interactions/base.py`**
  - Import `DrawCommand`, `RenderContext` from `panelmark.draw`
  - Change `render(self, region, term, focused)` →
    `render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]`
  - Update the abstract method docstring

- [x] **Update `panelmark/interactions/__init__.py`**
  - Export `DrawCommand`, `RenderContext`, `WriteCmd`, `FillCmd`, `CursorCmd`
    so they are importable from `panelmark.interactions`

- [x] **Update `panelmark/draw.py` exports in `panelmark/__init__.py`**
    (top-level `__init__` only exports `Shell` and `Interaction` — no change needed)

---

### Phase 2 — TUI: executor and context factory

- [ ] **Create `panelmark_tui/executor.py`**
  - `TUICommandExecutor.__init__(self, term)`
  - `execute(self, commands: list[DrawCommand], region: Region) -> None`
    - Iterates commands, dispatches to `_write`, `_fill`, `_cursor`
    - Does NOT flush stdout — caller flushes after all regions are done
  - `_write(self, cmd: WriteCmd, region: Region)` — translate style dict to
    blessed sequences using helper from `style.py`, print at
    `(region.row + cmd.row, region.col + cmd.col)`
  - `_fill(self, cmd: FillCmd, region: Region)` — loop over height rows,
    print `cmd.char * cmd.width` at each row offset
  - `_cursor(self, cmd: CursorCmd, region: Region)` — emit
    `term.move(region.row + cmd.row, region.col + cmd.col)` to position the
    terminal cursor without printing a character
  - Style translation: move style-dict-to-blessed-sequence logic from wherever
    it currently lives (or duplicate from `_apply_attrs` pattern in `style.py`)
    into a private `_apply_style(style: dict, term) -> str` function here

- [ ] **Create `panelmark_tui/context.py`**
  - `build_render_context(region: Region, term) -> RenderContext`
  - Detect capabilities from `term.number_of_colors`, add `'cursor'` and
    `'unicode'` unconditionally for TUI
  - This function is called by `Renderer.render_region()` for each region

- [ ] **Update `panelmark_tui/__init__.py`** to export new public names if any

---

### Phase 3 — TUI: migrate `_ScrollableList` base class

The scrollable base class is used by `MenuFunction`, `MenuReturn`,
`MenuHybrid`, `ListView`, `CheckBox`, and `FormInput`. Migrating it once
migrates the shared rendering logic for all six.

- [ ] **Update `panelmark_tui/interactions/scrollable.py`**
  - Rename `_render_rows(display_lines, region, term, focused, active_marker)`
    to `_build_rows(display_lines, context, focused, active_marker)` — returns
    `list[DrawCommand]` instead of printing
  - Replace `term.reverse + clipped + term.normal` with:
    `WriteCmd(row=screen_i, col=0, text=clipped, style={'reverse': True})`
    when `context.supports('color')` or unconditionally (reverse is always
    meaningful)
  - Active marker without focus: `WriteCmd(row=screen_i, col=0, text=f'> {line}'[:context.width].ljust(context.width))`
  - Plain row: `WriteCmd(row=screen_i, col=0, text=clipped)`
  - Clear trailing rows: `FillCmd(row=len(display_lines), col=0, width=context.width, height=context.height - len(display_lines))`
  - Update class docstring to reflect new return type
  - Remove `region` and `term` parameters from `_build_rows` signature;
    replace with `context: RenderContext`
  - **Future-extraction note:** Keep scroll state (`_scroll_offset`,
    `_last_height`, `_clamp_scroll()`) as a clearly separable block at the
    top of the class, separate from `_build_rows()`. A future `_Scrollable`
    base class (Phase 9) will lift exactly that block out. Mixing scroll
    state with row-building logic makes that extraction surgical rather than
    a clean cut.

---

### Phase 4 — TUI: migrate individual interaction `render()` methods

Each file below: change signature to `render(self, context, focused=False) ->
list[DrawCommand]`, build and return command list instead of printing.

- [ ] **`panelmark_tui/interactions/menu.py`** — `MenuFunction`, `MenuReturn`,
  `MenuHybrid`
  - Each calls `_render_rows(viewport, region, term, focused)`
  - After: calls `self._build_rows(viewport, context, focused)` and returns it
  - Remove `region` and `term` parameters

- [ ] **`panelmark_tui/interactions/list_view.py`** — `ListView`, `SubList`
  - Same `_render_rows` → `_build_rows` pattern

- [ ] **`panelmark_tui/interactions/checkbox.py`** — `CheckBox`
  - Builds display lines with `[X]`/`[ ]` prefixes, calls `_render_rows`
  - After: `_build_rows`, return commands

- [ ] **`panelmark_tui/interactions/form.py`** — `FormInput`
  - Similar pattern — check for direct `print()` calls and convert

- [ ] **`panelmark_tui/interactions/textbox.py`** — `TextBox`
  - More complex: handles cursor positioning
  - Body builds a list:
    - One `WriteCmd` per visible line (row 0..height-1, col 0, text padded
      to width)
    - One `WriteCmd(row=cursor_row, col=cursor_col, text=char_at_cursor,
      style={'reverse': True})` for the cursor character when focused and
      not readonly
    - One `CursorCmd(row=cursor_row, col=cursor_col)` as a positioning hint
      for TUI terminal cursor
  - `region.width` → `context.width`, `region.height` → `context.height`
  - Remove `region` and `term` parameters

- [ ] **`panelmark_tui/interactions/function.py`** — `Function`
  - This is a user-extensible escape hatch. Review current implementation:
    if it calls `term` directly, it cannot migrate purely. Determine whether
    `Function` should receive `context` and return commands (preferred), or
    whether it needs a special note in docs about the migration.
  - If `Function.render()` is overridden by users, the migration must provide
    a clear upgrade path — document it.

- [ ] **`panelmark_tui/interactions/status_message.py`** — `StatusMessage`
  - Convert print calls to `WriteCmd` commands

---

### Phase 5 — TUI: update `Renderer`

- [ ] **Update `panelmark_tui/renderer.py`**
  - Import `TUICommandExecutor` from `.executor`
  - Import `build_render_context` from `.context`
  - Add `self._executor = TUICommandExecutor(term)` in `__init__`
  - Rewrite `render_region(self, region, interaction, term, focused)`:
    ```python
    def render_region(self, region, interaction, focused):
        context = build_render_context(region, self._term)
        commands = interaction.render(context, focused)
        self._executor.execute(commands, region)
    ```
  - Remove `term` parameter from `render_region` — it uses `self._term`
  - Update all callers of `render_region` inside `full_render()`
  - The `_render_empty_region` method still uses `term` directly (draws
    spaces) — convert it to use the executor with `FillCmd` commands, or
    leave it as-is since it doesn't go through `Interaction.render()`

---

### Phase 6 — TUI: migrate widgets

Widgets create their own internal `Shell` instances and use `run_modal()`.
Their interactions are the same ones updated in Phase 4. The widgets
themselves mostly do not call `render()` directly — they drive via the shell's
event loop. Verify each widget for any direct `render()` calls.

- [ ] **`panelmark_tui/widgets/confirm.py`** — verify no direct `render()` calls
- [ ] **`panelmark_tui/widgets/alert.py`** — verify
- [ ] **`panelmark_tui/widgets/input_prompt.py`** — verify
- [ ] **`panelmark_tui/widgets/list_select.py`** — verify
- [ ] **`panelmark_tui/widgets/file_picker.py`** — verify; `MenuFunction`
  entries are rebuilt dynamically — ensure that rebuild path is compatible
- [ ] **`panelmark_tui/widgets/date_picker.py`** — has a `Function`-based
  calendar interaction; verify `Function` migration from Phase 4 covers this
- [ ] **`panelmark_tui/widgets/progress.py`** — special case: has an internal
  event loop that calls `term.inkey()` directly and manages its own display
  cycle. The `Function`-based bar interaction's `render()` must return
  commands; the progress widget's internal loop must call the executor to
  apply them. Add explicit `executor.execute(commands, region)` call in the
  progress update path.

---

### Phase 7 — Tests

- [ ] **`panelmark-tui/tests/interactions/`** — for each interaction test file:
  - Remove any `MockTerminal` usage from render tests
  - Call `render(RenderContext(width=N, height=M), focused=True/False)`
  - Assert on the returned `list[DrawCommand]` — check types, row/col,
    text content, style dicts
  - Tests that only call `handle_key()` and `get_value()` need no changes
  - `make_key()` and `MockTerminal` remain needed for event loop tests
    (`test_shell.py`, `test_termios_restore.py`, etc.) — do not remove them

- [ ] **`panelmark-tui/tests/test_renderer.py`** (if it exists)
  - Update to use executor pattern; render tests now check that executor
    receives the expected commands

- [ ] **`panelmark/tests/`** — add tests for the draw module itself:
  - `RenderContext.supports()` returns correct booleans
  - `WriteCmd`, `FillCmd`, `CursorCmd` are equal-by-value (dataclass equality)
  - Confirm `DrawCommand` type alias covers all three types

---

### Phase 8 — Documentation

- [ ] **Update `panelmark/RENDER_ABSTRACTION.md`**
  - Add a note at the top: "Option 3 was chosen. See `DRAW_MIGRATION.md` for
    the implementation plan and `panelmark/draw.py` for the API."
  - Update the comparison table to mark Option 3 as selected
  - The rest of the document (options analysis) remains as a design record

- [ ] **Update `panelmark/ECOSYSTEM.md`**
  - Remove the note that "`render()`'s `term` argument is TUI-specific and
    will need revisiting" — replace with a note that interactions return
    `list[DrawCommand]` and each renderer provides an executor
  - Add a brief note that `panelmark.draw` is the shared vocabulary between
    all renderers

- [ ] **Update `panelmark-tui/README.md`** (or equivalent)
  - Update any code examples that show `render(region, term, focused)`
  - Add a section on writing custom interactions using the draw command API

- [ ] **Update `panelmark/README.md`**
  - The `Interaction` ABC documentation: update `render()` description and
    show a minimal example returning `[WriteCmd(0, 0, 'hello')]`

- [ ] **Add module docstring to `panelmark/draw.py`**
  - Explain the coordinate system (region-relative)
  - Explain the style dict keys and valid values
  - Give a minimal example of a custom `render()` implementation

---

## Interaction: before and after

A concrete example of what one `render()` body looks like before and after, to
guide the interaction migrations in Phases 3–4.

**Before (TextBox, simplified):**
```python
def render(self, region, term, focused: bool = False) -> None:
    lines = self._get_display_lines(region.width)
    visible = lines[self._scroll_offset:self._scroll_offset + region.height]
    for i in range(region.height):
        row = region.row + i
        text = visible[i].ljust(region.width) if i < len(visible) else ' ' * region.width
        print(term.move(row, region.col) + text, end='', flush=False)
    if focused:
        cursor_char = term.reverse + char_at + term.normal
        print(term.move(abs_row, abs_col) + cursor_char, end='', flush=False)
```

**After (TextBox, simplified):**
```python
def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
    lines = self._get_display_lines(context.width)
    visible = lines[self._scroll_offset:self._scroll_offset + context.height]
    cmds: list[DrawCommand] = []
    for i in range(context.height):
        text = visible[i].ljust(context.width) if i < len(visible) else ' ' * context.width
        cmds.append(WriteCmd(row=i, col=0, text=text))
    if focused:
        cmds.append(WriteCmd(row=cursor_row, col=cursor_col,
                             text=char_at, style={'reverse': True}))
        cmds.append(CursorCmd(row=cursor_row, col=cursor_col))
    return cmds
```

Key changes:
- `region.width/height` → `context.width/height`
- `term.move(...)` / `print(...)` → `WriteCmd(row=..., col=..., text=...)`
- `term.reverse + text + term.normal` → `WriteCmd(..., style={'reverse': True})`
- `return None` → `return cmds`

---

## Compatibility note for user-written `Function` interactions

The `Function` interaction is currently the escape hatch for interactions that
draw arbitrarily. After this migration, a user who has written a `Function`
subclass with custom `render()` logic will need to update it. The migration
path is the same mechanical substitution shown above. Document this clearly
in the `Function` class docstring and in the changelog.

If backward compatibility is desired, consider a transitional shim:
a `LegacyFunction` base class that wraps the old `(region, term, focused)`
signature, calls the user's old render method against a mock context, and
returns a captured command list. This is non-trivial to implement and may
not be worth the complexity — note it as a possibility rather than a
requirement.

---

---

## Phase 9 — Post-migration: `_Scrollable` / `_ScrollableList` split

Do this as a separate, focused change after the draw command migration is
complete and tests are green. Do not combine with the migration.

**Background:** `_ScrollableList` currently conflates two concerns:
scroll-offset state management, and item-list rendering with selection
highlighting. `ListView` inherits from it despite being display-only and
having no meaningful use for active-index selection. This is a smell that
the draw command model makes more visible.

**The split:**

- **`_Scrollable`** — scroll offset state only. Provides `_scroll_offset`,
  `_last_height`, and `_clamp_scroll()`. No active index, no selection, no
  `_build_rows()`. A display-only scrollable panel (long text, log output,
  read-only list) inherits this and writes its own `render()`.

- **`_ScrollableList(_Scrollable)`** — extends `_Scrollable` with
  `_active_index` and `_build_rows()`. All interactive list interactions
  (`MenuFunction`, `MenuReturn`, `MenuHybrid`, `CheckBox`, `FormInput`)
  continue to use this unchanged.

- **`ListView`** — drops down from `_ScrollableList` to `_Scrollable`.
  Implements its own `render()` returning `WriteCmd` commands, no
  active-index highlighting.

**TODO (Phase 9):**

- [ ] Add `_Scrollable` base class to `scrollable.py` with only:
  `_scroll_offset`, `_last_height`, `_clamp_scroll()`
- [ ] Make `_ScrollableList` extend `_Scrollable` instead of `Interaction`
  directly; remove the scroll state it now duplicates
- [ ] Migrate `ListView` (and `SubList` if applicable) to inherit
  `_Scrollable` instead of `_ScrollableList`; write a direct `render()`
  that does not use `_build_rows()`
- [ ] Update tests for `ListView` to confirm it no longer has active-index
  behaviour
- [ ] Update `scrollable.py` class docstrings

---

## Summary checklist (in order)

```
Phase 1 — panelmark core ✓
  [x] panelmark/draw.py                     (new)
  [x] panelmark/interactions/base.py        (update signature)
  [x] panelmark/interactions/__init__.py    (re-export draw types)
  [x] panelmark/__init__.py                 (no change needed)

Phase 2 — panelmark-tui executor layer
  [ ] panelmark_tui/executor.py             (new)
  [ ] panelmark_tui/context.py              (new)
  [ ] panelmark_tui/__init__.py             (update exports if needed)

Phase 3 — scrollable base
  [ ] panelmark_tui/interactions/scrollable.py

Phase 4 — individual interactions
  [ ] interactions/menu.py                  (MenuFunction, MenuReturn, MenuHybrid)
  [ ] interactions/list_view.py
  [ ] interactions/checkbox.py
  [ ] interactions/form.py
  [ ] interactions/textbox.py
  [ ] interactions/function.py              (see compatibility note)
  [ ] interactions/status_message.py

Phase 5 — renderer
  [ ] panelmark_tui/renderer.py

Phase 6 — widgets
  [ ] widgets/confirm.py                    (verify only)
  [ ] widgets/alert.py                      (verify only)
  [ ] widgets/input_prompt.py               (verify only)
  [ ] widgets/list_select.py                (verify only)
  [ ] widgets/file_picker.py                (verify + dynamic rebuild check)
  [ ] widgets/date_picker.py                (verify + Function migration)
  [ ] widgets/progress.py                   (add executor call to update path)

Phase 7 — tests
  [ ] tests/interactions/* render tests     (assert on DrawCommand list)
  [ ] tests/test_renderer.py               (update if exists)
  [ ] panelmark/tests/ draw module tests   (new)

Phase 8 — documentation
  [ ] RENDER_ABSTRACTION.md                (note Option 3 chosen)
  [ ] ECOSYSTEM.md                         (update term/draw description)
  [ ] panelmark-tui/README.md              (update interaction examples)
  [ ] panelmark/README.md                  (update Interaction ABC docs)
  [ ] panelmark/draw.py module docstring   (coordinate system, style keys)

Phase 9 — post-migration: _Scrollable split (separate PR)
  [ ] Add _Scrollable base class to scrollable.py
  [ ] Make _ScrollableList extend _Scrollable
  [ ] Migrate ListView/SubList to _Scrollable
  [ ] Update ListView tests
  [ ] Update scrollable.py docstrings
```
