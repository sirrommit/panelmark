# Custom Interactions

Any object that implements the `Interaction` protocol can be assigned to a panelmark region.
The protocol is defined in `panelmark.interactions.base.Interaction`.

---

## The Interaction Protocol

```python
from abc import ABC, abstractmethod
from panelmark.draw import DrawCommand, RenderContext


class Interaction(ABC):

    @property
    def is_focusable(self) -> bool:
        """Return True if this interaction can receive keyboard focus.

        Display-only interactions (labels, status areas, progress bars)
        should override this to return False.  The shell skips non-focusable
        regions when cycling focus with Tab.
        """
        return True

    @abstractmethod
    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        """Return draw commands for the current visual state."""
        ...

    @abstractmethod
    def handle_key(self, key: str) -> tuple[bool, object]:
        """Handle a keypress.  Returns (value_changed, new_value)."""
        ...

    @abstractmethod
    def get_value(self) -> object:
        """Return the current value."""
        ...

    @abstractmethod
    def set_value(self, value) -> None:
        """Set the current value programmatically."""
        ...

    def signal_return(self) -> tuple[bool, object]:
        """Signal that the shell should exit.

        Called by the shell after every handle_key().  Return
        (True, return_value) when this interaction is done and the shell
        should stop.  Default returns (False, None) — keep running.
        """
        return False, None
```

---

## Minimal Example: Display Label

A display-only label shows a single line of text. It is not focusable and ignores all keys.

```python
from panelmark import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd


class Label(Interaction):
    """Display-only single-line text label."""

    def __init__(self, text: str = ""):
        self._text = text

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        line = self._text[:context.width].ljust(context.width)
        cmds = [WriteCmd(row=0, col=0, text=line)]
        if context.height > 1:
            cmds.append(FillCmd(row=1, col=0,
                                width=context.width, height=context.height - 1))
        return cmds

    def handle_key(self, key: str) -> tuple:
        return False, self.get_value()

    def get_value(self) -> str:
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)
```

---

## Focusable Example: Toggle Button

A toggle button cycles between on/off states and signals exit when confirmed.

```python
from panelmark import Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd


class Toggle(Interaction):
    """Simple on/off toggle. Press Enter to confirm and exit."""

    def __init__(self, initial: bool = False):
        self._value = initial
        self._confirmed = False

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        indicator = "[ON ]" if self._value else "[OFF]"
        text = indicator.ljust(context.width)
        style = {"reverse": True} if focused else None
        return [WriteCmd(row=0, col=0, text=text, style=style)]

    def handle_key(self, key: str) -> tuple:
        if key in (' ', 'KEY_ENTER', 'KEY_LEFT', 'KEY_RIGHT'):
            self._value = not self._value
            if key == 'KEY_ENTER':
                self._confirmed = True
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self) -> bool:
        return self._value

    def set_value(self, value) -> None:
        self._value = bool(value)

    def signal_return(self) -> tuple:
        if self._confirmed:
            return True, self._value
        return False, None
```

---

## Accessing the Shell

When an interaction is assigned to a shell via `shell.assign()`, the shell sets
`interaction._shell = self`. You can call any public shell method from inside an
interaction — for example to update another region or read its value:

```python
def handle_key(self, key: str) -> tuple:
    if key == 'KEY_ENTER':
        # Read a value from another region and update a third
        entry = self._shell.get('entry')
        self._shell.update('status', ('success', f'Saved: {entry}'))
        return True, self.get_value()
    return False, self.get_value()
```

---

## Using Capabilities

Use `context.supports()` to provide fallbacks on renderers that lack a feature:

```python
def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
    cmds = []
    for i, item in enumerate(self._items):
        text = item[:context.width].ljust(context.width)
        if i == self._active and focused:
            if context.supports('color'):
                style = {"bg": "blue", "color": "white"}
            else:
                style = {"reverse": True}   # mono fallback
        else:
            style = None
        cmds.append(WriteCmd(row=i, col=0, text=text, style=style))
    return cmds
```

---

## Scrollable Interactions

If your interaction displays a scrollable list, you can inherit from
`panelmark_tui.interactions.scrollable._ScrollableList` (in the `panelmark-tui` package),
which provides:

- `_active_index` and `_scroll_offset` state
- `_clamp_scroll()` to keep the active item visible
- `_build_rows(display_lines, context, focused, active_marker)` to produce `WriteCmd` and `FillCmd` commands for the visible viewport

See [panelmark-tui interactions](../../panelmark-tui/docs/interactions.md) for details.

---

## Testing Interactions

Because `render()` returns a plain list of data objects, interactions are easy to unit test
without any terminal dependency:

```python
from panelmark.draw import RenderContext, WriteCmd, FillCmd

def test_label_renders_text():
    label = Label("Hello, world")
    ctx = RenderContext(width=20, height=1)
    cmds = label.render(ctx, focused=False)
    assert isinstance(cmds[0], WriteCmd)
    assert "Hello, world" in cmds[0].text

def test_label_clips_long_text():
    label = Label("A" * 100)
    ctx = RenderContext(width=10, height=1)
    cmds = label.render(ctx, focused=False)
    assert len(cmds[0].text) == 10
```
