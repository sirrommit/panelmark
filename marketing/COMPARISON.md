# Description vs Reality: Panelmark Project Comparison

This document compares the handoff description produced by a parallel AI conversation with
the current state of the implementation. Each section names a claim in the description,
states what actually exists, and argues both for and against alignment.

---

## 1. Package name: `panelmark-term` vs `panelmark-tui`

### What the description says
Renderer packages follow `panelmark-{surface}` where the surface names the *rendering target*
not the underlying technology. Therefore: `panelmark-term`, not `panelmark-tui`.

### What exists
The package at `/home/sirrommit/claude_play/panelmark-tui/` is named `panelmark-tui` in
`pyproject.toml`. It is already pushed to GitHub as `sirrommit/panelmark-tui`.

### Argument for renaming to `panelmark-term`
- **Consistency rule pays forward.** The naming convention (`-term`, `-web`, `-tk`, `-qt`) is
  genuinely better than mixing surface names and technology names. `panelmark-tui` implicitly
  asserts that "TUI" is the surface, but TUI is the technology category, not the surface.
  The surface is a terminal. If you later ship a Qt terminal emulator renderer, `panelmark-tui`
  is ambiguous; `panelmark-term` is not.
- **Avoids the `tui` acronym problem.** "TUI" is a technology badge, not a user-facing surface
  name. Compare: `panelmark-web` is obvious to a non-technical stakeholder; `panelmark-tui` is
  only obvious to developers who know the acronym.
- **Low cost now, higher cost later.** The repo is brand new with zero downstream installs. A
  rename now costs one GitHub repository rename and a `sed` on `pyproject.toml`. In six months
  with real users it costs a deprecation cycle.

### Argument for keeping `panelmark-tui`
- **"TUI" is widely understood.** In the Python ecosystem (Textual, Urwid, Prompt Toolkit),
  "TUI" is the established vocabulary. Developers looking for a terminal UI library search
  "Python TUI library", not "Python terminal renderer". PyPI discoverability favors `tui`.
- **`-term` is ambiguous in a different way.** "Term" can mean "terminal emulator" (Kitty,
  Alacritty) or "terminal-as-in-shell" (term.exe, gnome-terminal). It does not unambiguously
  mean "terminal-mode text UI". A user might wonder: does `panelmark-term` render inside a
  terminal emulator, or does it *launch* a terminal?
- **The naming convention assumes all future renderer names are obvious.** `panelmark-web` is
  clear; but what about a curses backend vs a blessed backend vs a textual backend? If those
  diverge, `-term` starts looking like `panelmark-term-curses`, at which point the convention
  breaks down anyway.

**Verdict:** The naming argument in the description is philosophically correct but practically
contestable. A rename is low-risk now and never gets easier. Recommend renaming unless you have
a specific reason `tui` will serve discovery better.

---

## 2. Shell syntax

### What the description says
The example shell uses:
- `=100%=` in the top border row — percentage-width declaration at the border level
- `__Heading__` inside `{...}` cells — inline headings
- `$name$` — named widget placeholders
- `{25%}`, `{12R}` — width/height specifiers
- `|` and `=` borders, `-` interior dividers

### What exists
`example.shell` in the repository is **byte-for-byte identical** to the description's example.
The parser handles `__Heading__`, `$name$`, `{N%}`, `{NR}`, `{N%R}`, single/double borders.
The `=100%=` in the outer border is visual convention — the parser reads it as a border row
title — not a semantic width declaration. The outer shell always expands to the full terminal
width.

### Differences
**None.** The shell syntax in the description matches the current implementation exactly.
The one non-obvious point is that `=100%=` in the outer border title has no special parser
meaning — it is purely cosmetic — but the description does not claim otherwise.

---

## 3. Artifact format: multi-shell `[section]` files

### What the description says
A panelmark *artifact* is a Python file containing:
1. A triple-quoted string at the top with multiple `[section_name]` headers, each introducing
   a separate shell definition.
2. Python interaction declarations below using a `ui.on_*()` API.

Example:
```python
"""
[main]
|=100%====== My Application ==========================|
...

[confirm_delete]
|=30%====== Are you sure? ===|
...
"""
ui.on_select(navmenu, update(content))
ui.on_click(delete_btn, modal(confirm_delete, returns=action))
```

### What exists
No artifact format or multi-shell concept exists. Shells are constructed as single Python
strings passed to `Shell(definition)`. There is no `[section]` parser, no artifact file format,
no `ui` module or object.

### Argument for implementing the artifact format
- **Co-location is genuinely valuable.** Keeping layout and behaviour in one file reduces
  context switching and makes a screen's full structure visible at once. This is the same
  reason CSS-in-JS was controversial but eventually won in many React projects.
- **Multi-shell in one file solves a real problem.** An application with 12 screens currently
  needs 12 `Shell()` calls scattered across its codebase. The `[section]` format gives them a
  natural home and makes the `modal(confirm_delete)` reference syntactically obvious: it refers
  to a section in the same file.
- **The `ui.on_*()` API is more readable for non-experts.** Compare:
  ```python
  # current
  shell.assign('navmenu', MenuFunction({...}))
  shell.on_change('content', lambda v: ...)

  # described
  ui.on_select(navmenu, update(content))
  ```
  The declarative form reads closer to a UI design spec. It is the style used by SwiftUI,
  Flutter, and Jetpack Compose — the direction modern UI frameworks are converging on.
- **The artifact is the natural unit for future tooling.** A linter, a layout previewer, or a
  headless test runner all want a single file that describes a complete screen. The current
  approach requires running Python to collect the `Shell` instances.

### Argument for keeping the current approach
- **The current API is already complete and tested.** `shell.assign()`, `shell.on_change()`,
  `shell.bind()` are working, tested (116 + 198 tests), and cover all real use cases. The
  artifact format is a substantial new surface area with no tests and unclear semantics at the
  edge cases.
- **The `ui` object raises hard questions.** What is `ui`? A module-level singleton? A context
  object? An import? The description doesn't resolve this. If `ui` is a singleton, multi-window
  apps are impossible. If it's instantiated per-screen, why is it simpler than `shell = Shell(...)`?
- **`[section]` parsing is non-trivial and fragile.** A multi-section parser must deal with
  section ordering, forward references (`modal(confirm_delete)` before `confirm_delete` is
  defined), circular references, and the boundary between the string literal and the Python code
  below it. None of this exists in the description beyond a sketch.
- **`modal(confirm_delete, returns=action)` conflates declaration and invocation.** In the
  current implementation, `run_modal()` is called imperatively when the user triggers it. The
  declarative form needs a runtime to manage when modals fire — essentially a mini event system
  on top of the existing observer pattern.
- **You have zero users.** The existing API can be iterated without a deprecation cycle. The
  artifact format is a large upfront investment in a design whose ergonomics are untested.

**Verdict:** The artifact format idea is directionally interesting, especially multi-shell
co-location. But the `ui.on_*()` declarative API needs a concrete semantics before
implementation. Suggest: implement `[section]` multi-shell parsing (low risk, high value) as
a separate concern from the interaction API redesign. Keep the current OO API for now; revisit
after real usage shows which patterns are verbose.

---

## 4. Interaction/binding API

### What the description says
```python
ui.on_select(navmenu, update(content))
ui.on_click(delete_btn, modal(confirm_delete, returns=action))
result = await ui.show_modal(confirm_large_order)
```
A declarative, verb-oriented API where `update(content)` and `modal(...)` are action
descriptors rather than callbacks.

### What exists
```python
shell.assign('navmenu', MenuFunction({...}))
shell.on_change('navmenu', lambda v: shell.update('content', v))
shell.bind('source', 'target', transform=str.upper)
```
An OO, instance-method API. No `update()` or `modal()` action descriptors. No async modals.

### Argument for the declarative API
- **Less boilerplate for the common case.** `shell.bind('source', 'target')` is already a step
  in this direction; `update(content)` just makes it a noun instead of a method call.
- **Async modals are the right model for application-layer modals.** `await ui.show_modal()`
  is idiomatically correct in a modern async Python application. The current `run_modal()` is
  synchronous and blocks the entire thread — fine for a terminal TUI, but not portable to a
  web renderer where you need `async/await`.
- **The distinction between UI-layer and application-layer modals is a genuine insight.** It
  is not just naming: UI-layer modals (date picker, confirm dialog) belong in the shell
  artifact because they need no application knowledge. Application-layer modals (confirm large
  order) need domain data and belong in program code. The current implementation doesn't
  distinguish them.

### Argument for keeping the current API
- **The current API is explicit and predictable.** Every connection between regions is
  visible as a Python method call. There is no magic: `shell.bind('a', 'b')` is obviously
  "when 'a' changes, set 'b' to the same value."
- **Async is a large API surface change.** Async support requires restructuring the event loop
  in `panelmark_tui.Shell` and designing the async abstraction for the core `panelmark.Shell`.
  This is not trivial — blessed's `inkey()` is synchronous, and wrapping it correctly for
  `asyncio` requires a thread executor or a polling loop.
- **`update(content)` as an action descriptor hides too much.** What does `update(content)` do
  if `content` is not yet assigned an interaction? The current API raises `RegionNotFoundError`
  immediately; the declarative form would need to defer until render time, making errors harder
  to trace.

**Verdict:** The async modal idea deserves a design spike, particularly as the web renderer
comes closer. For now the current sync API is correct for the terminal use case. The
`update()`/`modal()` action descriptors are a nice-to-have; the core `bind()` method already
covers most of those cases.

---

## 5. Modal philosophy: UI-layer vs application-layer

### What the description says
Two kinds of modal: UI-layer (belongs in shell artifact, called declaratively) vs
application-layer (belongs in program, called with `await`).

### What exists
`run_modal()` is a single mechanism. The `panelmark_tui/widgets/` directory contains
prebuilt UI-layer modals (`Confirm`, `Alert`, `FilePicker`, etc.) but there is no formal
distinction between UI-layer and application-layer in the API.

### Differences
The *conceptual* distinction in the description maps well onto what exists: the prebuilt
widgets are UI-layer modals; any user-built `Shell` used via `run_modal()` is application-layer.
The distinction is implicit rather than enforced by the API.

**This is not a blocking gap** — the distinction is a documentation and API design question,
not a missing implementation. Adding a short doc note to the README or a `Widget` base class
for UI-layer modals would close most of this gap without an API change.

---

## 6. Renderer roadmap and naming

### What the description says
Planned order: `panelmark-term`, `panelmark-web`, `panelmark-tk`, `panelmark-qt`.

### What exists
Current package: `panelmark-tui`. No other renderer packages exist. The informal plan
noted in conversation was: web/HTML first, then Tkinter, then Toga, then PySide6.

### Differences
- **Name:** `panelmark-term` vs `panelmark-tui` (covered in §1).
- **Order:** Description says Tkinter before Qt. Conversation history had Tkinter before Toga
  before Qt. These are consistent — description just omits Toga, which is a minor gap.
- **Web renderer strategy:** Description defers reactive layer to "after real usage data,"
  which aligns with the prior conversation's advice.

---

## 7. Open questions: already answered

The description lists several open questions that are already resolved:

| Open question | Current answer |
|---|---|
| What does `panelmark-term` use under the hood? | `blessed` library, version ≥ 1.20 |
| Does the blessed/curses choice need hiding from the user? | Yes — it's an implementation detail of `panelmark-tui`; core has no dependency |
| What is the `[section]` syntax? | Not implemented |
| How does the web renderer translate `update()` to client/server wiring? | Open; no web renderer yet |
| How are widget types declared beyond `$name$`? | `$name$` is always generic; the renderer assigns an interaction via `assign()` |
| Responsive layout for web renderer? | Open; no web renderer yet |

---

## Summary table

| Topic | Description | Current state | Gap |
|---|---|---|---|
| Shell syntax | `__H__`, `$name$`, `{N%}`, `{NR}` | Identical | None |
| Package name | `panelmark-term` | `panelmark-tui` | Rename |
| Core/renderer split | `panelmark` + `panelmark-{surface}` | `panelmark` + `panelmark-tui` | Name only |
| Interaction API | `ui.on_select()`, declarative | `shell.assign()`, OO | Significant |
| Multi-shell artifact | `[section]` in one file | Not implemented | Missing feature |
| Async modals | `await ui.show_modal()` | Synchronous `run_modal()` | Missing, not blocking |
| UI-layer vs app-layer modals | Explicit distinction | Implicit (widgets vs custom) | Docs gap |
| Renderer roadmap order | term → web → tk → qt | tui → web → tk → qt | Name only |
| Prebuilt widgets | Described as library | 7 implemented, tested | None |

---

## Recommended actions

**Do now (low effort, high alignment):**
1. Rename `panelmark-tui` → `panelmark-term` on GitHub and in `pyproject.toml`. One commit.

**Do soon (medium effort, high value):**
2. Implement `[section]` multi-shell parsing in `panelmark.Parser`. Keeps shell definitions
   co-located, enables forward references to modals, and makes the artifact concept real —
   without touching the interaction API.

**Defer (high effort, needs design):**
3. Redesign the interaction API around `ui.on_*()` declarative style. Requires resolving
   what `ui` is, how action descriptors work, and what the failure modes look like. Best
   done after multi-shell is implemented and you have real usage data on which bindings are
   verbose.

**Defer (await web renderer work):**
4. Async modal API. Design it when the web renderer makes synchronous blocking genuinely
   impossible. Don't add async to the terminal renderer as a preview.
