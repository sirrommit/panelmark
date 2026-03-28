# Portable Standard Library

## Purpose

This layer sits above the core shell/runtime contract and below renderer-specific
libraries.  It defines interactions and widgets that a renderer may implement portably —
meaning application code can call the same API and receive the same semantic result
regardless of which renderer is in use.

A renderer that implements this layer fully claims `portable-library-compatible` status.
See [extensions.md](extensions.md).


## Design Constraints

The portable standard library standardizes:

- constructor signatures and parameter names
- `get_value()` / `set_value()` / `signal_return()` semantics
- widget call signatures and return values
- cancellation semantics

It does not standardize:

- visual shape, layout dimensions, or color scheme
- whether a widget is native or custom-drawn
- internal field navigation mechanics
- renderer-specific layout parameters such as `width`

Renderers are free to accept additional parameters (e.g. `width`, `row`, `col`) beyond
those specified here, as renderer extensions.


---

## Required Interactions

These interactions must be provided by any `portable-library-compatible` renderer.  Their
`get_value()` / `set_value()` / `signal_return()` semantics are normative.


### `MenuReturn`

A scrollable single-select list that returns a mapped value when the user accepts an item.

```python
MenuReturn(items: dict)
```

`items` maps display labels to return values.

```python
menu = MenuReturn({
    "New file": "new",
    "Open...":  "open",
    "Save":     "save",
    "Quit":     "quit",
})
sh.assign("menu", menu)
result = sh.run()   # returns "new", "open", "save", or "quit"
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | currently highlighted label (`str \| None`) |
| `set_value(label)` | highlight the item with the given label |
| `signal_return()` | `(True, mapped_value)` when the user accepts; `(False, None)` otherwise |


### `RadioList`

A single-select list with radio-button visuals.  The cursor position is the selection.

```python
RadioList(items: dict)
```

`items` maps display labels to return values.

```python
sh.assign("size", RadioList({"Small": "s", "Medium": "m", "Large": "l"}))
result = sh.run()   # returns "s", "m", or "l"
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | currently selected mapped value |
| `set_value(value)` | move cursor to the item with the given mapped value |
| `signal_return()` | `(True, value)` on accept; `(False, None)` otherwise |


### `CheckBox`

A scrollable checkbox list supporting multi-select and single-select modes.

```python
CheckBox(items: dict[str, bool], mode: str = "multi")
```

`items` maps labels to initial checked states.  `mode` is `"multi"` (default) or
`"single"`.

```python
options = CheckBox({
    "Enable logging": True,
    "Dark mode":      False,
    "Auto-save":      True,
})
sh.assign("options", options)
result = sh.get("options")   # dict[str, bool]
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | `dict[str, bool]` — label → checked state for all items |
| `set_value(mapping)` | replace the full checked-state dict |
| `signal_return()` | `(False, None)` — `CheckBox` does not signal return by default |

> Prefer `RadioList` for single-select when items map to distinct return values.
> `CheckBox(mode="single")` is appropriate when the input and output are both
> checked-state dicts.


### `TextBox`

A text-input area with configurable wrap and Enter behaviour.

```python
TextBox(
    initial: str = "",
    wrap: Literal["word", "anywhere", "extend"] = "word",
    readonly: bool = False,
    enter_mode: Literal["newline", "submit", "ignore"] = "newline",
)
```

**Wrap modes:** `"word"` — wrap at word boundaries; `"anywhere"` — wrap mid-word;
`"extend"` — no wrap, newline only on Enter (use for single-line inputs).

**Enter modes:** `"newline"` — Enter inserts a newline (default); `"submit"` — Enter
fires `signal_return()` without inserting a newline; `"ignore"` — Enter is discarded.

```python
entry = TextBox(wrap="extend", enter_mode="submit")
sh.assign("entry", entry)
result = sh.run()   # returns the typed text when Enter is pressed
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | current text content (`str`) including any newlines |
| `set_value(text)` | replace the full text content |
| `signal_return()` | `(True, text)` when Enter is pressed in `enter_mode="submit"`; `(False, None)` otherwise |


### `FormInput`

A structured data-entry form with typed fields, validation, and a Submit action.

```python
FormInput(fields: dict)
```

Each key in `fields` is a variable name; each value is a field definition dict.

**Portable field types:** `"str"`, `"int"`, `"float"`, `"bool"`, `"choices"`.

```python
form = FormInput({
    "name": {
        "type":       "str",
        "descriptor": "Your name",
        "required":   True,
        "validator":  lambda v: True if len(v) >= 2 else "Too short",
    },
    "age": {
        "type":       "int",
        "descriptor": "Age",
        "required":   True,
    },
    "role": {
        "type":       "choices",
        "descriptor": "Role",
        "options":    ["Admin", "User", "Guest"],
        "default":    "User",
    },
    "active": {
        "type":       "bool",
        "descriptor": "Active",
        "default":    True,
    },
})
sh.assign("form", form)
result = sh.run()   # dict of field values, or None on cancel
```

**Field definition keys:**

| Key | Required | Description |
|-----|----------|-------------|
| `"type"` | yes | one of the portable field types above |
| `"descriptor"` | yes | label shown to the user |
| `"default"` | no | initial value |
| `"placeholder"` | no | hint shown when empty (`str` fields) |
| `"required"` | no | validation fails if empty |
| `"validator"` | no | `callable(coerced_value) -> True \| error_str` |
| `"options"` | yes for `"choices"` | list of option strings |

| Method | Semantics |
|--------|-----------|
| `get_value()` | current field-state dict (values coerced to declared types) |
| `set_value(mapping)` | replace field-state dict |
| `signal_return()` | `(True, field_dict)` on successful submit; `(False, None)` otherwise |


### `DataclassFormInteraction`

A structured form interaction driven by a Python dataclass instance.  Field types and
labels are derived from the dataclass's field annotations and names.  This is the primary
portable form interaction for structured data collection.

```python
DataclassFormInteraction(
    dc_instance,
    actions: list | None = None,
    on_change: callable | None = None,
)
```

`dc_instance` is an instance of a `@dataclasses.dataclass` class.  The interaction
introspects the instance's fields to generate form rows.

`actions` is an optional list of action dicts, each with `"label"`, `"shortcut"`, and
`"action"` keys.  `"action"` is a callable that receives the current field-value dict
and returns the shell exit value.

```python
@dataclasses.dataclass
class Config:
    host:  str  = "localhost"
    port:  int  = 8080
    debug: bool = False

interaction = DataclassFormInteraction(
    Config(),
    actions=[
        {"label": "Save",   "shortcut": "s", "action": lambda vals: vals},
        {"label": "Cancel", "shortcut": "q", "action": lambda vals: None},
    ],
)
sh.assign("config", interaction)
result = sh.run()   # dict of field values, or None on cancel
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | current field-state dict |
| `set_value(mapping)` | replace field-state dict |
| `signal_return()` | `(True, action_result)` when an action fires; `(False, None)` otherwise |

> Use `DataclassFormInteraction` when embedding a form in a larger shell alongside other
> regions.  Use the `DataclassForm` widget when a standalone modal popup is preferred.


### `StatusMessage`

A display-only single-line status and feedback area.  Not focusable.

```python
StatusMessage()
```

Updated programmatically via `shell.update(name, value)`.

**Accepted value forms:**

| Value | Display |
|-------|---------|
| `None` or `""` | blank |
| `("error", "message")` | error-styled message |
| `("success", "message")` | success-styled message |
| `("info", "message")` | info-styled message |
| `str` | treated as `("info", str)` |

```python
sh.assign("status", StatusMessage())
sh.update("status", ("error",   "File not found"))
sh.update("status", ("success", "Saved successfully"))
sh.update("status", None)   # clear
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | `(style, message)` tuple, or `None` if blank |
| `set_value(value)` | replace status payload (same forms as above) |
| `signal_return()` | always `(False, None)` |


---

## Required Widgets

These modal widgets must be provided by any `portable-library-compatible` renderer.

All modal widgets share the following semantics:

- invoked via `.show(parent_shell=sh)` or equivalent renderer call
- block until the user makes a choice
- return `None` on cancel, Escape, or close without a selection


### `Alert`

Informational popup that blocks until dismissed.

```python
Alert(
    title: str = "Alert",
    message_lines: list[str] = [],
)
```

**Returns:** `True` when dismissed; `None` on cancel/close.


### `Confirm`

Asks the user to confirm or deny.  Buttons are caller-defined.

```python
Confirm(
    title: str = "Confirm",
    message_lines: list[str] = [],
    buttons: dict = {"OK": True, "Cancel": False},
)
```

`buttons` maps display labels to return values.

**Returns:** the mapped value for the selected button; `None` on cancel/close.


### `InputPrompt`

Asks the user to type a single line of text.

```python
InputPrompt(
    title: str = "Input",
    prompt_lines: list[str] = [],
    initial: str = "",
)
```

**Returns:** the entered text (`str`, may be `""`) on OK or Enter; `None` on cancel/close.


### `ListSelect`

Lets the user pick one item (single mode) or multiple items (multi mode) from a list.

```python
ListSelect(
    title: str = "Select",
    prompt_lines: list[str] = [],
    items: list | dict = [],
    multi: bool = False,
)
```

Pass a `list` to return the selected label; pass a `dict` to return the mapped value.
In multi mode, pass a `dict[str, bool]` to set initial checked states (or a `list` to
start all unchecked).

**Single mode returns:** selected item or mapped value; `None` on cancel/close.

**Multi mode returns:** `dict[str, bool]` of all items and their final checked states on
OK; `None` on cancel/close.


### `FilePicker`

Browse the filesystem and select a file or directory.

```python
FilePicker(
    start_dir: str | None = None,
    title: str = "Select File",
    dirs_only: bool = False,
    filter: str = "*",
)
```

`start_dir` defaults to the current working directory.  `filter` is a glob pattern
applied to the file list.  `dirs_only=True` hides files and shows only directories.

**Returns:** absolute path string on OK; `None` on cancel/close.


### `DataclassForm`

Modal form driven by a dataclass instance.  A thin wrapper around
`DataclassFormInteraction` for use as a standalone popup.

```python
DataclassForm(
    dc_instance,
    title: str = "Edit",
    actions: list | None = None,
    on_change: callable | None = None,
)
```

`actions` follows the same format as `DataclassFormInteraction`.

**Returns:** the value returned by the triggered action callable (typically a field-value
dict or `None`); `None` if cancelled without an action.


---

## Frequently Implemented

The following interactions and widgets are not required for `portable-library-compatible`
status, but renderers that provide them should follow the API contracts below.

Application code that uses these APIs will be portable across any renderer that
implements them, but should not assume their availability without checking renderer
documentation.


### `MenuFunction` (interaction)

A scrollable menu that invokes a callback when the user selects an item.  Does not exit
the shell automatically.

```python
MenuFunction(items: dict)
```

`items` maps display labels to callables.  Each callable receives the shell as its first
argument: `callback(shell)`.

| Method | Semantics |
|--------|-----------|
| `get_value()` | currently highlighted label (`str \| None`) |
| `set_value(label)` | highlight the item with the given label |
| `last_activated` | read-only property — label most recently invoked, or `None` |
| `signal_return()` | `(False, None)` — does not signal return |


### `ListView` (interaction)

A display-only scrollable list.  Not focusable by default.

```python
ListView(items: list[str])
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | current items list (`list[str]`) |
| `set_value(items)` | replace the full items list |
| `signal_return()` | `(False, None)` |


### `TreeView` (interaction)

An interactive tree with expand/collapse support.

```python
TreeView(tree: dict, *, initially_expanded: bool = False)
```

`tree` is a nested dict where `None` values are leaves and dict values are branches.

```python
result = sh.run()   # returns path tuple, e.g. ('Documents', 'report.pdf')
```

| Method | Semantics |
|--------|-----------|
| `get_value()` | current highlighted path tuple (`tuple[str, ...]`), or `None` if empty |
| `set_value(path)` | highlight the item at the given path; expand ancestors |
| `signal_return()` | `(True, path_tuple)` when a leaf is accepted; `(False, None)` otherwise |


### `TableView` (interaction)

A multi-column read-only display table with a sticky header.

```python
TableView(columns: list, rows: list)
```

`columns` is `[(header_label, width_in_chars), ...]`.  `rows` is a list of rows, each
a list of values.

| Method | Semantics |
|--------|-----------|
| `get_value()` | 0-based active row index (`int`) |
| `set_value(index)` | move cursor to the given row index |
| `signal_return()` | `(False, None)` by default |


### `DatePicker` (widget)

Presents a calendar for date selection.

```python
DatePicker(
    initial: datetime.date | None = None,
    title: str = "Select Date",
)
```

`initial` defaults to today.

**Returns:** `datetime.date` on OK; `None` on cancel/close.


### `Progress` (widget)

Displays a progress bar during a long operation.  Uses a context-manager pattern.

```python
Progress(
    title: str = "Progress",
    total: int = 100,
    cancellable: bool = True,
)
```

```python
with Progress(title="Importing", total=len(records)).show(sh) as prog:
    for i, record in enumerate(records, 1):
        process(record)
        prog.set_progress(i, f"Record {i}/{len(records)}")
        if prog.cancelled:
            break
```

**Handle API:** `prog.set_progress(n, message="")` — advance to step `n`;
`prog.cancelled` — `True` if the user cancelled.

**Returns:** `None` always; check `prog.cancelled` for cancellation.


### `Spinner` (widget)

Indeterminate-progress popup for operations without a known total.

```python
Spinner(
    title: str = "Working…",
    cancellable: bool = True,
)
```

```python
with Spinner(title="Scanning…").show(parent_shell=sh) as spin:
    for path in paths:
        scan(path)
        spin.tick(f"Scanning {path}")
        if spin.cancelled:
            break
```

**Handle API:** `spin.tick(message="")` — advance animation frame;
`spin.cancelled` — `True` if the user cancelled.

**Returns:** `None` always.


### `Toast` (widget)

Transient overlay notification that auto-dismisses.

```python
Toast(
    message: str,
    title: str = "Notice",
    duration: float = 2.0,
)
```

**Returns:** `None` always.  Dismisses after `duration` seconds or on the first keypress.
