# panelmark

**panelmark** is a zero-dependency Python library for defining terminal UI layouts using a readable
ASCII-art shell language, and for implementing the interaction logic that runs inside them.

panelmark is the **core library** in the panelmark ecosystem. It has no runtime dependencies on
any terminal library. It defines:

---

## What is real today

| Feature | Status |
|---------|--------|
| Shell definition language (ASCII-art DSL) | ✅ Fully working |
| `#` line comments and `/* */` block comments | ✅ Fully working |
| Horizontal splits (`=` / `-` border rows) | ✅ Fully working |
| Vertical splits — single-line divider (`\|`) | ✅ Fully working |
| Vertical splits — double-line divider (`\|\|`) | ✅ Fully working |
| Equal-width fill splits (all columns fill-width) | ✅ Columns share space equally (differ by at most 1 char) |
| Panel headings (`__text__` syntax) | ⚠️ Parsed and stored; renderers must implement display |
| `Shell` state machine (focus, dirty tracking, key dispatch, `on_change`, `bind`) | ✅ Fully working |
| Draw command abstraction (`DrawCommand`, `RenderContext`, `WriteCmd`, `FillCmd`, `CursorCmd`) | ✅ Fully working |
| `Interaction` base class | ✅ Fully working |

See [panelmark-tui limitations](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md) for the combined limitations list.

---

- The **shell definition language** — an ASCII-art syntax for describing layouts
- The **layout model** — resolved geometry (row, col, width, height) for each named region
- The **draw command abstraction** — renderer-agnostic `DrawCommand` types returned by interactions
- The **`Interaction` base class** — the protocol all interactive widgets implement
- The **`Shell` state machine** — focus, dirty tracking, key dispatch, and value observation

To actually display a shell in a terminal, pair panelmark with
[**panelmark-tui**](https://github.com/sirrommit/panelmark-tui), which wraps
[blessed](https://github.com/jquast/blessed) and provides a full event loop, built-in
interactions, and renderer-specific convenience widgets.

---

## Installation

```
pip install panelmark
```

---

## Quick start

```python
from panelmark import Shell, Interaction
from panelmark.draw import DrawCommand, RenderContext, WriteCmd, FillCmd

# 1. Define a layout
LAYOUT = """
|=== <bold>My App</> ===|
|{10R $sidebar$  }|{$main$        }|
|==================|
|{2R  $status$              }|
|==================|
"""

# 2. Implement an interaction
class Label(Interaction):
    def __init__(self, text: str):
        self._text = text

    @property
    def is_focusable(self) -> bool:
        return False

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        line = self._text[:context.width].ljust(context.width)
        return [WriteCmd(row=0, col=0, text=line)]

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self):
        return self._text

    def set_value(self, value) -> None:
        self._text = str(value)

# 3. Assign interactions to regions
shell = Shell(LAYOUT)
shell.assign("sidebar", Label("Navigation"))
shell.assign("main", Label("Content area"))
shell.assign("status", Label("Ready"))

# 4. Drive with a renderer (e.g. panelmark-tui)
# result = shell.run()   ← panelmark_tui.Shell adds run()
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Shell Language](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/overview.md) | Shell, region, and panel concepts; state machine methods |
| [Shell Language Syntax](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/syntax.md) | Full grammar reference for the ASCII-art layout DSL |
| [Shell Language Examples](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/examples.md) | Annotated examples; custom interactions; portable rendering patterns |
| [Draw Commands](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/contract.md) | `DrawCommand` types, `RenderContext`, and the style dict |
| [Custom Interactions](https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/examples.md) | Implementing the `Interaction` ABC |
| [Renderer Spec](https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/overview.md) | Renderer compatibility contract, portable library layer, and extension policy |
| [Ecosystem Overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/ecosystem.md) | Layered design; package responsibilities; dependency direction |
| [Choosing a Renderer](https://github.com/sirrommit/panelmark-docs/blob/main/docs/getting-started.md) | Decision tree for selecting the right package |

---

## Ecosystem

panelmark follows a layered design. The core library is renderer-agnostic;
renderer-specific packages extend it.

| Package | Role |
|---------|------|
| **panelmark** (this package) | Zero-dependency core: shell language, layout, draw commands, interaction protocol |
| [**panelmark-tui**](https://github.com/sirrommit/panelmark-tui) | Terminal renderer (blessed); portable-library-compatible |
| [**panelmark-html**](https://github.com/sirrommit/panelmark-html) | Static HTML/CSS renderer; pre-alpha; foundation for panelmark-web |
| [**panelmark-web**](https://github.com/sirrommit/panelmark-web) | Live web runtime via WebSockets; portable-library-compatible |

See [ecosystem overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/ecosystem.md)
for the full design rationale and dependency diagram.

---

## License

MIT
