# Draw Commands

panelmark interactions produce renderer output by returning a `list[DrawCommand]` from their
`render()` method. This keeps interaction logic pure and side-effect-free — no terminal
escapes, no `print()` calls, no direct cursor movement.

The renderer (e.g. `panelmark-tui`'s `TUICommandExecutor`) translates the command list into
actual output for its target surface.

---

## Coordinate System

All row and column values in draw commands are **region-relative**:

- `(0, 0)` is the top-left cell of the interaction's assigned region
- `row` increases downward (0 = top row of region)
- `col` increases rightward (0 = left column of region)

The executor maps these to screen-absolute or document-absolute coordinates internally.
An interaction never needs to know where on the screen it lives.

---

## DrawCommand Types

### `WriteCmd` — write styled text

```python
from panelmark.draw import WriteCmd

WriteCmd(
    row: int,          # region-relative row (0-based)
    col: int,          # region-relative column (0-based)
    text: str,         # text to write; should not contain newlines
    style: dict | None = None,  # optional styling (see Style Dict below)
)
```

Writes `text` at the given position. No automatic clipping — callers should ensure `text`
fits within `context.width - col` characters.

**Example:**
```python
# Write "Hello" in bold at the top-left of the region
WriteCmd(row=0, col=0, text="Hello", style={"bold": True})
```

---

### `FillCmd` — fill a rectangle

```python
from panelmark.draw import FillCmd

FillCmd(
    row: int,           # top-left corner row
    col: int,           # top-left corner column
    width: int,         # number of columns to fill
    height: int,        # number of rows to fill
    char: str = ' ',    # fill character (default: space)
    style: dict | None = None,
)
```

Fills a rectangular area with repeated `char`. The default `char=' '` clears the area.

**Example:**
```python
# Clear the entire region
FillCmd(row=0, col=0, width=context.width, height=context.height)

# Draw a red background block over 3 rows
FillCmd(row=2, col=0, width=context.width, height=3,
        style={"bg": "red"})
```

---

### `CursorCmd` — position the text cursor

```python
from panelmark.draw import CursorCmd

CursorCmd(
    row: int,   # region-relative row
    col: int,   # region-relative column
)
```

This is a **hint**, not a draw operation. Renderers that support a visible text cursor
(checked via `context.supports('cursor')`) move the cursor here after executing all other
commands. Renderers that do not support a cursor ignore it entirely.

At most one `CursorCmd` should appear in a command list. If multiple are present, the
executor uses the last one.

**Example:**
```python
# Position the cursor at the current input position
cmds.append(WriteCmd(row=cursor_row, col=cursor_col,
                     text=char_at_cursor, style={"reverse": True}))
cmds.append(CursorCmd(row=cursor_row, col=cursor_col))
```

---

## RenderContext

`RenderContext` is passed to every `render()` call. It carries the region's dimensions and
the set of capabilities the renderer supports.

```python
from panelmark.draw import RenderContext

@dataclass(frozen=True)
class RenderContext:
    width: int                           # region width in columns
    height: int                          # region height in rows
    capabilities: frozenset[str]         # renderer feature flags

    def supports(self, feature: str) -> bool: ...
```

### Capability flags

Use `context.supports(feature)` to write portable interactions that degrade gracefully on
limited renderers.

| Feature | Meaning |
|---------|---------|
| `'color'` | At least 8 foreground/background colours |
| `'256color'` | 256-colour palette |
| `'truecolor'` | 24-bit (16 million) colours |
| `'unicode'` | Unicode characters render correctly |
| `'cursor'` | A text cursor can be positioned (TUI / interactive web) |
| `'italic'` | Italic text is visually distinct from normal |

```python
def render(self, context, focused=False):
    if context.supports('color'):
        style = {"color": "red"}
    else:
        style = {"bold": True}   # fallback for mono renderers
    return [WriteCmd(row=0, col=0, text="Error", style=style)]
```

---

## Style Dict

The optional `style` argument on `WriteCmd` and `FillCmd` is a plain Python `dict`. All
keys are optional. Renderers apply the keys they support and silently ignore the rest —
unknown keys are not an error.

| Key | Type | Description |
|-----|------|-------------|
| `bold` | `bool` | Bold / heavy weight |
| `italic` | `bool` | Italic (renderers without italic use normal) |
| `underline` | `bool` | Underline |
| `reverse` | `bool` | Swap foreground and background colours |
| `color` | `str` | Foreground colour name |
| `bg` | `str` | Background colour name |

**Colour names:** `'black'`, `'red'`, `'green'`, `'yellow'`, `'blue'`, `'magenta'`,
`'cyan'`, `'white'`

**Example:**
```python
# Active / selected row style
style = {"reverse": True}

# Error text
style = {"color": "red", "bold": True}

# Highlighted date in a calendar
style = {"reverse": True, "bold": True}

# No style
style = None
```

---

## Type Alias

```python
from panelmark.draw import DrawCommand

# DrawCommand = WriteCmd | FillCmd | CursorCmd
# A render() method returns list[DrawCommand]
```

---

## Putting It Together

A typical `render()` implementation follows this pattern:

```python
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd, CursorCmd

def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
    cmds: list[DrawCommand] = []

    # 1. Clear the region
    cmds.append(FillCmd(row=0, col=0, width=context.width, height=context.height))

    # 2. Write content
    for i, item in enumerate(self._visible_items(context.height)):
        text = item[:context.width].ljust(context.width)
        is_active = (i == self._active_index) and focused
        cmds.append(WriteCmd(
            row=i, col=0, text=text,
            style={"reverse": True} if is_active else None,
        ))

    # 3. Position cursor (if this interaction uses one)
    if focused and self._cursor_visible:
        cmds.append(WriteCmd(
            row=self._cursor_row, col=self._cursor_col,
            text=self._char_at_cursor or " ",
            style={"reverse": True},
        ))
        cmds.append(CursorCmd(row=self._cursor_row, col=self._cursor_col))

    return cmds
```
