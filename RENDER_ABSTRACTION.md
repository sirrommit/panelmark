# Render Abstraction: Options for Replacing `term`

> **Internal working note.** See [ecosystem overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/ecosystem.md)
> for the authoritative design rationale.

> **Status:** **Option 3 (Draw Commands) was chosen and implemented** in the
> `draw-commands` branch. See `DRAW_MIGRATION.md` for the implementation plan and
> `panelmark/draw.py` for the resulting API.
>
> This document is retained as a record of the design decision process.

## The Problem

`Interaction.render(region, term, focused)` passes a blessed `Terminal` object as its
second argument. Every built-in interaction uses `term` directly:

```python
# typical interaction render() body today
print(term.move(region.row, region.col) + term.bold + text + term.normal)
```

This works for `panelmark-tui` and nowhere else. An HTML renderer has no `Terminal`.
A Tkinter renderer has a frame, not a terminal. As additional renderers are built, the
`term` argument either needs to be replaced with something portable, or `render()` needs
to be removed from the shared `Interaction` interface entirely.

The design chosen here will determine whether interactions written by users are portable
across renderers, or whether users must rewrite their interactions for each renderer.

---

## Constraints

Before evaluating options, the constraints that any solution must satisfy:

1. **Core has no renderer dependency.** `panelmark` must not import `blessed`, a web
   framework, or a GUI toolkit. The abstraction lives in core; implementations live in
   renderer packages.
2. **Built-in interactions work across renderers.** `MenuReturn`, `TextBox`, `ListView`,
   etc. should render correctly in every renderer without being rewritten.
3. **User-written interactions should be portable.** A custom interaction written for
   `panelmark-tui` should render (possibly with degraded fidelity) in `panelmark-html`
   without code changes, unless the user deliberately uses renderer-specific features.
4. **The existing `panelmark-tui` behaviour must be fully preserved.** The solution
   cannot require rewriting all existing interaction render logic from scratch.

---

## Option 1: Remove `render()` from core — renderers own rendering entirely

Remove `render()` from the `Interaction` abstract base class. Core interactions carry
only state logic (`handle_key`, `get_value`, `set_value`, `signal_return`). Each
renderer package is responsible for knowing how to draw each interaction type.

```python
# panelmark core — no render() method
class Interaction(ABC):
    @abstractmethod
    def handle_key(self, key: str) -> tuple: ...
    @abstractmethod
    def get_value(self): ...
    @abstractmethod
    def set_value(self, value) -> None: ...
    def signal_return(self) -> tuple: ...

# panelmark-tui — renderer knows how to draw each type
class TUIRenderer:
    def render_interaction(self, interaction, region, term, focused):
        if isinstance(interaction, MenuReturn):
            self._render_menu_return(interaction, region, term, focused)
        elif isinstance(interaction, TextBox):
            self._render_textbox(interaction, region, term, focused)
        ...
```

### Pros
- Core is truly pure. No rendering concept bleeds into the state machine layer.
- Each renderer has complete freedom to draw interactions however it wants.
- No need to design a shared drawing API.

### Cons
- **The renderer must know about every interaction type.** Adding a new interaction
  type anywhere requires updating every renderer. This is the classic visitor pattern
  problem: the type list is open but the renderer treats it as closed.
- **User-written interactions are not portable.** A user who writes a custom interaction
  for `panelmark-tui` gets no rendering in `panelmark-html` unless they also add a
  branch to the HTML renderer — which they cannot do without forking it.
- **The built-in interactions fragment across packages.** `MenuReturn`'s rendering logic
  currently lives alongside its state logic in one file. Under this option, rendering
  lives in each renderer package, spread across four or five separate codebases.
- Breaks the ergonomic pattern that makes `panelmark-tui` pleasant today.

---

## Option 2: `Canvas` abstraction in core

Define an abstract `Canvas` class in `panelmark` core. Replace `term` with `canvas` in
the `render()` signature. Each renderer provides its own `Canvas` implementation.

```python
# panelmark core
from abc import ABC, abstractmethod

class Canvas(ABC):
    @abstractmethod
    def write(self, row: int, col: int, text: str,
              style: dict | None = None) -> None:
        """Write styled text at region-relative (row, col)."""
        ...

    @abstractmethod
    def fill(self, row: int, col: int, width: int,
             height: int, char: str = ' ') -> None:
        """Fill a rectangle with a character."""
        ...

    def cursor_at(self, row: int, col: int) -> None:
        """Hint that a text cursor should appear here. Renderers may ignore."""
        pass

class Interaction(ABC):
    @abstractmethod
    def render(self, region: Region, canvas: Canvas,
               focused: bool = False) -> None: ...
```

`panelmark-tui` provides:

```python
class TerminalCanvas(Canvas):
    def __init__(self, term, offset_row: int, offset_col: int):
        self._term = term
        self._row = offset_row
        self._col = offset_col

    def write(self, row, col, text, style=None):
        seq = _apply_style(style, self._term) if style else ''
        reset = str(self._term.normal) if style else ''
        print(self._term.move(self._row + row, self._col + col)
              + seq + text + reset, end='', flush=False)

    def fill(self, row, col, width, height, char=' '):
        for r in range(height):
            print(self._term.move(self._row + row + r, self._col + col)
                  + char * width, end='', flush=False)
```

Coordinates passed to `canvas.write()` are **region-relative** (row 0 = top of region).
The `Canvas` implementation maps them to screen-absolute coordinates or DOM positions
internally, so interactions never need to know their absolute position.

### Pros
- Interactions are portable. Write `render()` once against the `Canvas` API and it
  works in every renderer that provides a `Canvas`.
- The `Canvas` API is small and maps cleanly to all rendering targets: terminal cells,
  HTML positioned elements, Tkinter canvas items, Qt painter calls.
- Region-relative coordinates remove a source of bugs in current interactions, which
  must add `region.row` and `region.col` manually to every `term.move()` call.
- Fully backward-compatible migration path: wrap `term` in a `TerminalCanvas` and the
  existing interactions work without changes to their logic.
- Core defines the contract; renderers compete on quality of implementation.

### Cons
- The `Canvas` API must be designed carefully. Too minimal and complex interactions
  cannot express what they need; too rich and some renderers cannot implement it.
- Some interactions use terminal-specific features (cursor blink, reverse video as a
  selection indicator) that have no direct HTML equivalent. These degrade gracefully
  but require thought.
- Adds a new abstraction layer that users writing simple interactions must learn.

---

## Option 3: Render to data — interactions return draw commands

`render()` returns a list of draw commands rather than performing side effects. The
renderer executes those commands against the actual surface.

```python
# panelmark core
@dataclass
class WriteCmd:
    row: int; col: int; text: str; style: dict | None = None

@dataclass
class FillCmd:
    row: int; col: int; width: int; height: int; char: str = ' '

DrawCommand = WriteCmd | FillCmd

class Interaction(ABC):
    @abstractmethod
    def render(self, region: Region,
               focused: bool = False) -> list[DrawCommand]: ...
```

The renderer collects commands and applies them:

```python
# panelmark-tui
for cmd in interaction.render(region, focused):
    if isinstance(cmd, WriteCmd):
        term.move(region.row + cmd.row, region.col + cmd.col)
        print(apply_style(cmd.style, term) + cmd.text + term.normal, ...)
    elif isinstance(cmd, FillCmd):
        ...
```

### Pros
- Interactions are pure functions of state — no side effects in `render()`. Highly
  testable: assert on the returned command list, no stdout capture needed.
- Renderers can optimise: diff against previous output, batch writes, skip unchanged
  regions without calling `render()` at all.
- The command list is serialisable — useful for debugging, snapshots, and automated
  visual regression tests.

### Cons
- **`render()` can no longer branch on renderer capability.** If a terminal supports
  256-colour and an interaction wants to use it, the interaction currently checks
  `term.number_of_colors`. With draw commands, it cannot — the command list is produced
  before the renderer's capabilities are known.
- **Complex interactions accumulate large command lists.** A scrollable list with 20
  items and a highlight row generates many commands per frame. This is not necessarily
  a performance problem but adds memory pressure.
- **Significant rewrite of all existing interactions.** Every `render()` method today
  calls `print()` directly. Converting to returning command lists touches every
  interaction file.
- The command vocabulary (`WriteCmd`, `FillCmd`, ...) is still an API that must be
  designed and versioned — essentially a reimplementation of the Canvas API as data
  rather than methods.

---

## Option 4: Context injection — canvas stored on the interaction

The renderer injects a canvas into each interaction at assignment time. `render()` takes
only `(self, region, focused)` — no extra parameter.

```python
# panelmark core
class Interaction(ABC):
    _canvas: 'Canvas | None' = None  # injected by renderer

    @abstractmethod
    def render(self, region: Region, focused: bool = False) -> None: ...
```

The renderer's `assign()` method sets `_canvas`:

```python
# panelmark-tui
def assign(self, name, interaction):
    super().assign(name, interaction)
    interaction._canvas = TerminalCanvas(self._term, ...)
```

Interactions then call `self._canvas.write(...)` rather than using `term` directly.

### Pros
- The cleanest call site: `interaction.render(region, focused)` — no extra argument.
- Canvas is set once at assignment, not passed on every render call.

### Cons
- **Fragile with reassignment and sharing.** If a canvas depends on the region's
  absolute position (which it must for terminal rendering), and `_resolve_layout()` is
  called to reposition regions, the injected canvas is stale. The renderer must
  re-inject on every layout resolve.
- **An interaction cannot be assigned to two shells simultaneously.** The `_canvas`
  attribute is singular. This is a real constraint in the widget layer, where a single
  interaction instance might be reused.
- **Implicit coupling.** Like `self._shell`, magic attributes injected by the framework
  are hard to reason about and hard to mock in tests.
- Testing requires injecting a mock canvas before calling `render()` — more setup than
  passing a canvas argument directly.

---

## Option 5: Visitor pattern — renderer visits interactions

Interactions expose themselves as visitable objects. The renderer implements a visitor
that knows how to draw each type.

```python
# panelmark core
class Interaction(ABC):
    @abstractmethod
    def accept(self, visitor: 'RenderVisitor', region: Region,
               focused: bool) -> None: ...

class RenderVisitor(ABC):
    @abstractmethod
    def visit_menu_return(self, interaction, region, focused): ...
    @abstractmethod
    def visit_textbox(self, interaction, region, focused): ...
    ...
```

### Pros
- Renderer fully controls drawing. No shared Canvas API to design.
- Double dispatch: both the interaction type and the renderer type are known at the call
  site.

### Cons
- **The most verbose option by a wide margin.** Every interaction type requires a method
  in every renderer visitor, a dispatch method on the interaction, and a visitor ABC.
- **The visitor list is closed.** Adding a new interaction type means adding an abstract
  method to `RenderVisitor`, which breaks every renderer that does not implement it.
  This is the visitor antipattern for open type hierarchies.
- **User-written interactions require updating the visitor interface**, which users
  cannot do without modifying the core `RenderVisitor` ABC. In practice this means
  user interactions cannot be visited — they need a fallback `visit_unknown()` method
  that degrades to nothing.
- Idiomatic Python prefers duck typing and protocols over visitor hierarchies. This
  option fights the language.

---

## Comparison summary

| | Option 1 | Option 2 | Option 3 | Option 4 | Option 5 |
|---|---|---|---|---|---|
| Core stays dependency-free | ✓ | ✓ | ✓ | ✓ | ✓ |
| Built-in interactions portable | ✗ | ✓ | ✓ | ✓ | ✓ |
| User interactions portable | ✗ | ✓ | ✓ | ✓ | ✗ |
| Existing render() logic preserved | ✗ | ✓ (wrap term) | ✗ (rewrite) | ✓ (wrap term) | ✗ |
| Clean call site | — | medium | cleanest | cleanest | verbose |
| Testable without stdout capture | no | yes (mock Canvas) | yes (assert list) | yes (inject Canvas) | yes |
| Handles renderer capability differences | n/a | yes (Canvas can query) | no | yes | yes |
| Risk of stale state | low | low | none | high | low |
| Implementation effort | low | medium | high | medium | very high |

---

## Recommendation: Option 2 — Canvas abstraction

**Option 2 is the right choice.** It is the only option that satisfies all four
constraints — core stays clean, built-in interactions are portable, user interactions
are portable, and the existing render logic is preserved with a mechanical wrapper
rather than a rewrite.

### Minimal Canvas API

The `Canvas` interface should be defined conservatively, containing only what
interactions actually need today, and extended as real requirements emerge:

```python
class Canvas(ABC):
    """Abstract drawing surface. Coordinates are region-relative:
    (0, 0) is the top-left cell of the assigned region."""

    @abstractmethod
    def write(self, row: int, col: int, text: str,
              style: dict | None = None) -> None:
        """Write text at (row, col) with optional style attributes.
        Style dict uses the same keys as panelmark style tags:
        {'bold': True, 'color': 'red', 'bg': 'blue', 'reverse': True}
        """
        ...

    @abstractmethod
    def fill(self, row: int, col: int, width: int,
             height: int, char: str = ' ',
             style: dict | None = None) -> None:
        """Fill a rectangle with char, optionally styled."""
        ...

    @property
    @abstractmethod
    def width(self) -> int:
        """Width of the region in renderer-appropriate units."""
        ...

    @property
    @abstractmethod
    def height(self) -> int:
        """Height of the region in renderer-appropriate units."""
        ...

    def cursor_at(self, row: int, col: int) -> None:
        """Hint: place a text cursor here. Renderers may ignore."""
        pass

    def supports(self, feature: str) -> bool:
        """Query renderer capability. Known features: 'color', '256color',
        'unicode', 'cursor'. Returns False if unknown."""
        return False
```

The `supports()` method allows interactions to degrade gracefully:
```python
if canvas.supports('color'):
    canvas.write(0, 0, text, style={'color': 'red'})
else:
    canvas.write(0, 0, text)
```

### Migration path for panelmark-tui

The existing `render(region, term, focused)` methods are migrated in one pass:

1. `TerminalCanvas` is written in `panelmark-tui`, wrapping `term`. It translates
   region-relative `(row, col)` to `(region.row + row, region.col + col)` internally.
2. The `render()` signature in `Interaction` changes to
   `render(region, canvas, focused)`.
3. Each existing `render()` body is updated: replace `term.move(region.row + r, ...)`
   with `canvas.write(r, ...)`, replace `term.bold + text + term.normal` with
   `canvas.write(..., style={'bold': True})`.

This is mechanical work, not a redesign. The logic of each interaction is unchanged;
only the drawing calls change form.

### What this does not solve

The `render()` signature itself (`region, canvas, focused`) assumes a 2D cell grid
model — rows and columns. This maps naturally to terminals and HTML (CSS grid), but
Tkinter and Qt think in pixels or logical units, not rows and columns. A deeper
question — whether `Region` should express dimensions in cells, pixels, or an
abstract unit — is deferred until a desktop renderer is actively being built, at which
point there is real implementation data to reason from.
