# Shell Language Reference

panelmark layouts are defined using an ASCII-art shell definition string. The parser converts
this string into a tree of `HSplit`, `VSplit`, and `Panel` nodes, which are then resolved into
flat `Region` objects (row, col, width, height) at a given terminal size.

---

## Overview

Every shell definition is a block of lines. Each line must be enclosed in outer pipe
characters `|...|`. Blank lines are ignored.

Two comment forms are supported:

- `# line comment` — everything from `#` to the end of the line is removed before parsing.
- `/* block comment */` — C-style block comments may span multiple lines and can appear
  inline inside a shell row, which is useful for annotating individual panels.

```
|=== Title ===|        ← horizontal border (double-line style, with title)
|{$left$  }|{$right$}| ← content rows with a vertical split
|-------------|        ← horizontal border (single-line style, no title)
|{$footer$   }|        ← content row spanning full width
|=============|        ← closing border
```

The parser reads the inner content of each line (everything between the outer `|` walls)
and builds a layout tree recursively.

---

## Horizontal Splits

A **horizontal split** (top/bottom) is produced by a **border row** — a line whose content
starts with `=` or `-` and contains no `{` blocks.

```
|================|     ← double-line style  (= characters)
|----------------|     ← single-line style  (- characters)
```

The first such row found splits the definition into a `top` block (all lines above it)
and a `bottom` block (all lines below it). The border is rendered as a full-width
horizontal rule.

**Optional title** — text anywhere in the border row (between the fill characters) becomes
the border's title, rendered centred:

```
|=== My Section ===|   ← "My Section" displayed centred in the border
|--- Details ------|   ← "Details" displayed centred in a single-line border
```

**Style markup in titles** — titles support a limited inline style syntax:

```
|=== <bold>Important</> ===|
```

Supported tags: `<bold>`, `<italic>`, `<underline>`, `<reverse>`, `<red>`, `<green>`,
`<yellow>`, `<blue>`, `<magenta>`, `<cyan>`. Close with `</>`.

---

## Vertical Splits

A **vertical split** (left/right) is produced by a structural column divider that appears
**outside** any `{...}` block and is consistent across **all** content rows.

```
|{$left$  }|{$right$}|
```

The inner `|` between the two `{...}` blocks is the structural divider. It must appear in
exactly the same structural position in every content row of the block.

- `|` produces a **single-line** vertical divider (`│`)
- `||` produces a **double-line** vertical divider (`║`)

Splits can be nested to any depth. The parser resolves them recursively:

```
|{$a$}|{$b$}|{$c$}|    ← two structural | chars → two vertical splits
```

---

## Content Blocks

A **content row** is a line whose inner content is a single `{...}` block (after the outer
border pipes are removed). Everything inside `{...}` is the panel specification.

```
|{specifiers $name$ }|
```

A panel can span multiple definition rows — each additional row adds another `1R` to its
implicit height. Specifiers are only read from the **first** definition row of a panel.

### Region Name

A **region name** identifies the panel for interaction assignment. Use `$name$` syntax.
Names must match `[a-z0-9_]+` and must be unique across the shell.

```
|{$my_region$  }|
```

If omitted, the panel exists in the layout but cannot have an interaction assigned.

### Fixed Width

A leading integer sets a fixed character width for the panel:

```
|{20 $sidebar$}|{$main$   }|
```

`$sidebar$` is always 20 characters wide. `$main$` takes the remaining space.

### Percentage Width

A leading integer followed by `%` sets a proportional width:

```
|{30% $sidebar$}|{70% $main$}|
```

Percentages are computed relative to the available content width (terminal width minus the
two outer border walls and any internal dividers).

> **Note:** at least one panel in a VSplit must be either fixed or percentage; the other
> may be fill (no width spec). If all panels in a split are fill, they share equally.

### Fixed Row Count

`NR` inside the block sets the panel to exactly N rows tall:

```
|{10R $list$  }|
|{3R  $status$}|
```

### Percentage Row Count

`N%R` sets a proportional height:

```
|{50%R $top$   }|
|{50%R $bottom$}|
```

### Heading

`__text__` inside the block attaches a heading string to the panel. The heading is passed
to the renderer and may be displayed (e.g. in a sub-border).

```
|{__Navigation__ $sidebar$}|
```

### Implicit Height

If no row count specifier is given, the panel's height equals the number of definition
lines that make up its slot in the layout. Additional blank lines in a multi-row panel
expand its height by one row each.

```
|{$panel$   }|   ← 1 definition row → height 1
|{          }|   ← 2nd definition row for same panel → height 2
|{          }|   ← 3rd → height 3
```

---

## Complete Example

```python
SHELL = """
|=== <bold>File Manager</> ===|
|{30% 20R $tree$  }|{20R $files$       }|
|--- <bold>Filter</> ----------|
|{2R $filter$                 }|
|--- <bold>Filename</> --------|
|{2R $filename$               }|
|-----------------------------|
|{1R  $buttons$               }|
|=============================|
"""
```

This produces:
- A top double-line border titled "File Manager"
- A 20-row VSplit: `$tree$` gets 30% width, `$files$` takes the rest
- A single-line border titled "Filter"
- A 2-row `$filter$` region
- A single-line border titled "Filename"
- A 2-row `$filename$` region
- A plain single-line divider
- A 1-row `$buttons$` region
- A closing double-line border

---

## Parser Rules Summary

| Syntax | Effect |
|--------|--------|
| `|...|` | Outer border — required on every line |
| `=...=` or `---` | Horizontal split border (no `{` on that line) |
| `=== Title ===` | Horizontal border with centred title |
| `<bold>text</>` | Style markup in border titles |
| `\|` between blocks | Single-line vertical split divider |
| `\|\|` between blocks | Double-line vertical split divider |
| `{...}` | Content block specifying a panel |
| `$name$` | Region name (inside `{...}`) |
| `20` at start | Fixed 20-char width (inside `{...}`) |
| `30%` at start | Percentage width (inside `{...}`) |
| `5R` | Fixed 5-row height (inside `{...}`) |
| `50%R` | Percentage height (inside `{...}`) |
| `__text__` | Panel heading (inside `{...}`) |
| Blank lines | Ignored |
| `# comment` | Line comment — stripped to end of line before parsing |
| `/* comment */` | Block comment — may span lines; newlines preserved |

---

## Shell State Machine

Once parsed, a `Shell` instance manages:

| Method | Description |
|--------|-------------|
| `shell.assign(name, interaction)` | Attach an `Interaction` to a named region |
| `shell.unassign(name)` | Remove the interaction from a region |
| `shell.get(name)` | Get the current value of a region |
| `shell.update(name, value)` | Programmatically set a region's value (marks dirty) |
| `shell.on_change(name, cb)` | Register a callback fired when a region's value changes |
| `shell.bind(source, target)` | Mirror source value → target (with optional transform) |
| `shell.set_focus(name)` | Move focus to a named region |
| `shell.handle_key(key)` | Dispatch a key event; returns `('exit', value)` or `('continue', None)` |
| `shell.dirty_regions` | Set of region names that need re-rendering |
| `shell.mark_all_clean()` | Clear the dirty set after rendering |

### Built-in key bindings

| Key | Action |
|-----|--------|
| `Tab` | Move focus to next focusable region |
| `Shift+Tab` (`KEY_BTAB`) | Move focus to previous focusable region |
| `Escape` or `Ctrl+Q` | Exit — `handle_key` returns `('exit', None)` |

All other keys are dispatched to the currently focused interaction's `handle_key()` method.
Focus order follows reading order (top-to-bottom, left-to-right) by region position.
