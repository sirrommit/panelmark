# Panelmark Ecosystem

Panelmark is a layout language and rendering framework for Python user interfaces.
The core idea is that a developer sketches a UI as an ASCII art shell definition,
and that same definition renders correctly through any supported renderer. The shell
is written once; the renderer is chosen at deployment time.

This document describes the intended package ecosystem, the rationale behind its
structure, and the planned evolution of each package.

---

## Package map

```
panelmark                 # core: layout language, parser, shell state machine
├── panelmark-tui         # terminal renderer (blessed)
├── panelmark-html        # static HTML/CSS renderer
│   └── panelmark-web     # live web renderer (depends on panelmark-html)
├── panelmark-tk          # Tkinter renderer
└── panelmark-qt          # Qt/PySide6 renderer
```

---

## panelmark (core)

The core package contains everything that is not renderer-specific:

- The shell definition parser
- The layout model (HSplit, VSplit, Panel, Region resolution)
- The `Shell` state machine (`assign`, `update`, `bind`, `on_change`, `handle_key`,
  `dirty_regions`)
- The `Interaction` abstract base class
- Style tag parsing (`parse_styled`, `styled_plain_text`)
- Exceptions (`RegionNotFoundError`, `CircularUpdateError`)

**Dependencies:** none.

The zero-dependency constraint is intentional. Any renderer can depend on `panelmark`
without pulling in `blessed`, a web framework, or a GUI toolkit. The core is also the
natural target for future tooling — a layout linter, a shell file previewer, or a
headless test harness — none of which should require a rendering backend.

---

## panelmark-tui

The terminal renderer. Extends `panelmark.Shell` with a `blessed`-powered event loop.

**Adds:**
- `Shell.run()` — fullscreen terminal event loop
- `Shell.run_modal()` — modal popup loop inside an existing terminal context
- `Renderer` — draws box-drawing characters, borders, and region content to a terminal
- All concrete `Interaction` implementations (MenuFunction, MenuReturn, TextBox,
  ListView, CheckBox, Function, FormInput, StatusMessage)
- Prebuilt modal widgets (Confirm, Alert, InputPrompt, ListSelect, FilePicker,
  DatePicker, Progress)
- `MockTerminal` and `make_key` testing utilities

**Dependencies:** `panelmark`, `blessed >= 1.20`.

**Naming note:** `panelmark-tui` uses the established Python community term for
terminal text interfaces. When additional renderers ship, the ecosystem uses
technology/format names throughout (`html`, `tk`, `qt`), making `tui` the
natural anchor of the set rather than an anomaly.

---

## panelmark-html

The static HTML/CSS renderer. Given a layout model and assigned interactions, produces
an HTML document or fragment representing the current state of the shell.

**Scope:** pure rendering — layout model in, HTML string out. No network layer, no
server, no JavaScript beyond what is needed to represent the static state. Useful for:

- Server-side rendering of a panelmark shell into a Flask/Django template
- Generating static dashboards or reports
- Automated visual testing (render to HTML, diff against a snapshot)
- The foundation layer for `panelmark-web`

**Dependencies:** `panelmark`. No web framework dependency.

**Relationship to panelmark-web:** `panelmark-html` is a standalone package with its
own defined scope. Users who want a live, interactive web application should install
`panelmark-web` instead. The `panelmark-html` README should make this explicit to
avoid confusion.

---

## panelmark-web

The live web renderer. Adds a server-side session layer and a JavaScript client on top
of `panelmark-html`.

**Adds over panelmark-html:**
- A server integration (Flask, FastAPI, or both) that hosts a panelmark shell as a
  live session
- A channel between the server and the browser — WebSockets, server-sent events, or
  HTMX-style request/response — carrying key events from the client and shell state
  updates back
- A JavaScript client that applies incremental updates to the rendered HTML without
  full page reloads
- Session management, reconnection handling, and multiplexing for concurrent users

**Why the split from panelmark-html exists:**

`panelmark-html` has a natural, bounded scope: render a layout model to HTML. That
scope is useful on its own and carries no server or network dependency. `panelmark-web`
adds a full interactive stack on top. Separating them means:

1. The rendering layer can be developed, tested, and used independently of the live
   session layer.
2. The dependency graph is honest: `panelmark-web` depends on `panelmark-html` for
   rendering, just as `panelmark-tui` depends on `panelmark` for layout. The shape is
   consistent.
3. Users doing server-side rendering without a live connection do not pull in WebSocket
   or HTMX dependencies.

**When to build:** after `panelmark-html` exists and has been used in at least one real
server-rendered context. The live layer should be designed around actual usage patterns,
not anticipated ones.

**Dependencies:** `panelmark-html`, a web framework (Flask or FastAPI, likely optional),
a JavaScript build step or a CDN-delivered client bundle.

---

## panelmark-tk

A Tkinter renderer. Maps the panelmark layout model to Tkinter widgets using the
`grid` geometry manager. Zero additional install friction — Tkinter ships with CPython.

**Priority:** after `panelmark-html`. Tkinter is the lowest-friction desktop renderer
and a good stress-test of the renderer abstraction across a genuinely different layout
paradigm (retained-mode widget tree vs terminal cell grid vs HTML DOM).

**Dependencies:** `panelmark`. Tkinter is part of the standard library.

---

## panelmark-qt

A Qt renderer using PySide6. The professional desktop surface — native widgets,
high-DPI, platform look-and-feel.

**Priority:** after `panelmark-tk`. Qt adds significant install weight and is the right
choice for applications that need it specifically, not as a first renderer target.

**Dependencies:** `panelmark`, `PySide6`.

---

## Intended build order

1. **panelmark** — done
2. **panelmark-tui** — done
3. **panelmark-html** — static HTML/CSS rendering, no server
4. **panelmark-web** — live session layer on top of panelmark-html
5. **panelmark-tk** — Tkinter desktop renderer
6. **panelmark-qt** — Qt desktop renderer

The ordering reflects: reach (terminal users exist now), install friction (html and web
have none beyond pip), and the value of stressing the renderer abstraction across
genuinely different layout paradigms before committing to API decisions.

---

## What the core API must not do

As renderers are added, pressure will build to add renderer-specific concepts to the
core. The following constraints should hold regardless:

- `panelmark.Shell` must not import or reference any renderer. The terminal, HTML, and
  desktop renderers are equal peers from the core's perspective.
- The shell definition language must render correctly through every renderer without
  modification. Renderer-specific annotations, if ever needed, belong in the renderer's
  own configuration layer, not in the shell string.
- The `Interaction` base class must not assume a terminal. Its `render()` signature will
  need revisiting as non-terminal renderers are added — the `term` argument is
  TUI-specific and will not translate to HTML or Qt.
