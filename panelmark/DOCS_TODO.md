# Docs TODO

This file tracks documentation corrections needed in the `panelmark` core repo.

The goal is to make the core docs:

- accurate with respect to the current `panelmark` implementation
- accurate with respect to the current documentation layout in this repo
- appropriately scoped so that renderer-specific details live in renderer docs


## High-Level Direction

Apply these documentation principles while making the fixes below:

- `panelmark` core docs should describe:
  - the core shell/layout/draw/interaction model
  - the renderer contract and ecosystem boundaries
  - broad descriptions of renderer packages
- `panelmark` core docs should not try to maintain detailed inventories of
  `panelmark-tui` interactions or widgets
- concrete `panelmark-tui` API details should live in `panelmark-tui` docs
- dead links to removed documents must be replaced with current paths


## Files To Update

- [README.md](/home/sirrommit/claude_play/panelmark/README.md)
- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)
- [docs/custom-interactions.md](/home/sirrommit/claude_play/panelmark/docs/custom-interactions.md)
- [panelmark/interactions/base.py](/home/sirrommit/claude_play/panelmark/panelmark/interactions/base.py)

Potentially also review:

- [docs/renderer-spec/overview.md](/home/sirrommit/claude_play/panelmark/docs/renderer-spec/overview.md)
- [docs/renderer-spec/contract.md](/home/sirrommit/claude_play/panelmark/docs/renderer-spec/contract.md)

Those two looked broadly consistent during review, but should be re-checked after the
main fixes so the cross-links and phrasing remain coherent.


## Required Corrections

## 1. Fix dead `renderer-boundary` links

**Status: DONE**

### Problem

The core docs still link to `docs/renderer-boundary.md`, but that file no longer
exists in `panelmark/docs/`.

The current renderer-spec docs live under:

- `docs/renderer-spec/overview.md`
- `docs/renderer-spec/contract.md`
- `docs/renderer-spec/portable-library.md`
- `docs/renderer-spec/extensions.md`
- `docs/renderer-spec/readiness.md`

### Files affected

- [README.md](/home/sirrommit/claude_play/panelmark/README.md)
- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)

### Required changes

- In `README.md`, replace the documentation table entry currently labeled
  “Renderer Boundary” with something that points to the new renderer-spec docs.
- Preferred replacement:
  - label: `Renderer Spec`
  - link target: `docs/renderer-spec/overview.md`
  - description: broad wording such as “Renderer compatibility contract,
    portable library layer, and extension policy”
- In `ECOSYSTEM.md`, replace the stale inline reference to
  `docs/renderer-boundary.md` with the new renderer-spec location.
- Preferred target in `ECOSYSTEM.md`:
  - `docs/renderer-spec/contract.md` if the sentence is specifically about the
    runtime contract
  - `docs/renderer-spec/overview.md` if the sentence is more general


## 2. Remove stale `panelmark-tui` inventory counts and class lists from core docs

**Status: DONE**

### Problem

`panelmark` core docs currently try to list exact `panelmark-tui` interaction/widget
inventory and counts. Those details are stale and should not be maintained in the
core repo.

Examples of stale details:

- “13 interaction types”
- “9 modal widgets”
- named classes such as `MenuHybrid` and `SubList`, which do not exist in the
  current `panelmark-tui` surface

### Files affected

- [README.md](/home/sirrommit/claude_play/panelmark/README.md)
- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)

### Required changes in `README.md`

- In the short `panelmark-tui` mention near the top, replace detailed claims like:
  - “built-in interaction types”
  - “ready-made modal widgets”
  with a concise broad description only
- Example acceptable wording:
  - “provides a terminal event loop, built-in interactions, and renderer-specific convenience widgets”
- In the ecosystem table, replace:
  - “blessed-powered terminal renderer, 13 interaction types, 9 modal widgets”
  with:
  - “blessed-powered terminal renderer with concrete interactions and widget conveniences”

### Required changes in `ECOSYSTEM.md`

- Rewrite the `panelmark-tui` section so it describes the package in broad terms only
- Remove exact interaction/widget counts
- Remove exact interaction/widget class inventories from the core repo
- Replace with wording like:
  - `Shell.run()` / `Shell.run_modal()`
  - terminal renderer
  - concrete interaction library
  - renderer-specific widget/convenience layer
  - testing utilities
- Add a sentence that `panelmark-tui` documentation is the source of truth for
  its concrete interactions and widgets


## 3. Remove or rewrite stale references to `MenuHybrid` and `SubList`

**Status: DONE** — Named class lists removed from `ECOSYSTEM.md`; `is_focusable` docstring
fixed in `base.py`. The `_ScrollableList` reference in `docs/custom-interactions.md` is
addressed by item 5.

### Problem

The core docs and comments still reference `MenuHybrid` and `SubList`, but those
are not part of the current visible `panelmark-tui` API surface.

### Files affected

- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)
- [docs/custom-interactions.md](/home/sirrommit/claude_play/panelmark/docs/custom-interactions.md)
- [panelmark/interactions/base.py](/home/sirrommit/claude_play/panelmark/panelmark/interactions/base.py)

### Required changes

- In `ECOSYSTEM.md`, remove the named interaction list entirely rather than
  trying to update it
- In `docs/custom-interactions.md`, remove references to `panelmark_tui`
  helper classes that mention `SubList`
- In `panelmark/interactions/base.py`, change the `is_focusable` docstring:
  - current wording mentions “ListView, SubList”
  - replace with a general phrase like:
    - “Display-only interactions override this to return False.”
  - do not mention specific renderer package classes in the core ABC docstring


## 4. Fix stale architecture wording in `ECOSYSTEM.md`

**Status: DONE**

### Problem

`ECOSYSTEM.md` still contains wording from an older design state:

- it says the current draw-command model keeps interactions renderer-agnostic
  “at the cost of losing per-render capability queries”

That statement is now false because `RenderContext.supports(feature)` exists.

### Files affected

- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)

### Required changes

- Rewrite the paragraph under “What the core API must not do” that currently
  discusses `Interaction.render()`
- Keep the intended architectural point:
  - interactions must not assume a terminal
  - renderers are equal peers
- Remove the false statement about capability queries being lost
- Replace it with wording consistent with the current API:
  - `render()` uses `RenderContext`
  - interactions return `list[DrawCommand]`
  - capability queries are available via `context.supports(feature)`
- Link to:
  - `panelmark/draw.py`
  - `docs/draw-commands.md`
  - `docs/renderer-spec/contract.md`


## 5. Tighten `docs/custom-interactions.md` so it stays core-focused

**Status: DONE**

### Problem

This file is mostly good, but one section reaches too far into `panelmark-tui`
private helper classes.

The current “Scrollable Interactions” section tells users to inherit from:

- `panelmark_tui.interactions.scrollable._ScrollableList`

That is:

- renderer-specific
- private (leading underscore)
- not appropriate as a recommendation in core docs

### Files affected

- [docs/custom-interactions.md](/home/sirrommit/claude_play/panelmark/docs/custom-interactions.md)

### Required changes

- Rewrite the “Scrollable Interactions” section
- Do not recommend inheriting from `_ScrollableList`
- Do not recommend private TUI helper APIs from core docs
- Replace with one of these approaches:

Option A, preferred:
- keep the section short
- say that renderer packages may provide helper mixins or base classes for
  scrollable interactions
- direct readers to the relevant renderer docs for those helpers

Example acceptable wording:
- “If you are writing a renderer-specific interaction library, that renderer may
  provide helper mixins for scroll state and row rendering. See that renderer’s
  own documentation for those convenience APIs.”

Option B:
- remove the section entirely if it cannot be stated cleanly without reaching
  into renderer-private APIs


## 6. Keep `README.md` focused on core and current docs layout

**Status: DONE**

### Problem

The README is mostly accurate, but it should better reflect the current
documentation organization and avoid becoming the maintenance point for
renderer-specific details.

### Files affected

- [README.md](/home/sirrommit/claude_play/panelmark/README.md)

### Required changes

- Keep the “What is real today” table if desired; it looked broadly accurate
- Keep the quick-start example if desired; it looked consistent with the core API
- Update the docs table to match current files and terminology
- Recommended docs table entries:
  - `Shell Language` → `docs/shell-language.md`
  - `Draw Commands` → `docs/draw-commands.md`
  - `Custom Interactions` → `docs/custom-interactions.md`
  - `Renderer Spec` → `docs/renderer-spec/overview.md`
- Make the `panelmark-tui` reference broad and link-oriented rather than
  inventory-oriented


## 7. Keep `ECOSYSTEM.md` architectural, not catalog-style

**Status: DONE**

### Problem

`ECOSYSTEM.md` currently mixes good architecture discussion with stale catalog
details from `panelmark-tui`.

### Files affected

- [ECOSYSTEM.md](/home/sirrommit/claude_play/panelmark/ECOSYSTEM.md)

### Required changes

- Preserve:
  - the overall package-map discussion
  - the rationale for core vs renderers
  - future renderer planning
  - the architectural guardrails for core
- Remove or generalize:
  - exact renderer inventories
  - exact counts
  - stale named class lists
- Add a sentence in the `panelmark-tui` section along these lines:
  - “The `panelmark-tui` repository/docs are the source of truth for its concrete
    interaction and widget APIs.”


## 8. Ensure no remaining references to removed `renderer-boundary` doc

**Status: DONE**

### Problem

At least two files still referenced `docs/renderer-boundary.md` during review.
There may be more.

### Required changes

- Search all docs under `panelmark/` for:
  - `renderer-boundary`
- Replace each occurrence with the appropriate renderer-spec doc path
- After edits, confirm that no remaining `renderer-boundary` references exist
  in the `panelmark` repo


## 9. Document the key string format for renderer implementors

**Status: DONE**

### Problem

`Shell.handle_key(key)` accepts three distinct kinds of key strings:

- Printable characters passed as-is: `'a'`, `' '`, `'\t'`
- Named keys using a `KEY_*` prefix convention: `'KEY_UP'`, `'KEY_DOWN'`,
  `'KEY_ENTER'`, `'KEY_BTAB'`, etc.
- Control characters as literal escape values: `'\x11'` (Ctrl+Q),
  `'\x1b'` (Escape)

The current source docstring says "Named keys use the blessed convention" — but
`panelmark` core has no blessed dependency.  A non-terminal renderer (such as
`panelmark-web`) needs to know the canonical `KEY_*` names without reference to
the `blessed` library.

There is no dedicated doc page for this.  The only reference is the class
docstring on `Shell` and incidental examples in `docs/custom-interactions.md`.

### Files affected

- `panelmark/shell.py` — docstring wording
- A new or existing doc page (see below)

### Required changes

Option A (preferred): Add a section to `docs/renderer-spec/contract.md` titled
**"Key string format"** that:

- Lists the three categories (printable, `KEY_*` named, control characters)
- Lists the canonical `KEY_*` names that `panelmark` recognises (at minimum:
  `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`, `KEY_ENTER`, `KEY_TAB`,
  `KEY_BTAB`, `KEY_BACKSPACE`, `KEY_DELETE`, `KEY_F1`–`KEY_F12`,
  `KEY_HOME`, `KEY_END`, `KEY_PGUP`, `KEY_PGDN`)
- States that these names are the canonical contract — not blessed-specific
- States that `'\x1b'` (Escape) and `'\x11'` (Ctrl+Q) trigger shell exit
  by default in the base `Shell`, and that renderers should pass them through

Option B: Add a new `docs/key-strings.md` if the section would be too long for
`contract.md`.

Also update the `Shell.handle_key` docstring in `panelmark/shell.py` to remove
the phrase "blessed convention" and replace it with "panelmark's canonical
`KEY_*` names (see `docs/renderer-spec/contract.md`)" or the equivalent path.


## 10. Document the dirty-region and render-loop APIs

**Status: PARTIAL** — `docs/renderer-spec/contract.md` section 6 ("Dirty / Redraw
Behavior") mentions dirty regions and names `shell.mark_all_clean()`, but does not: name
the `shell.dirty_regions` property explicitly, mention `shell.update()` as a dirty
trigger, show the expected render loop pattern, or note that focus changes add both old and
new focused regions to the dirty set.

### Problem

`Shell.dirty_regions` and `Shell.mark_all_clean()` are mentioned only in the
`Shell` class docstring.  No doc page describes the expected render loop:

```python
result = shell.handle_key(key)
dirty = shell.dirty_regions
shell.mark_all_clean()
for region in dirty:
    re_render(region)
```

A renderer implementor reading only the docs (not source) would not know this
pattern exists.

### Files affected

- `docs/renderer-spec/contract.md`

### Required changes

Add a section titled **"Dirty-region tracking"** (or similar) to
`docs/renderer-spec/contract.md` that describes:

- `shell.dirty_regions` — a `set[str]` of region names that need re-rendering
  after the most recent `handle_key` or `update` call
- `shell.mark_all_clean()` — call this after the renderer has updated all dirty
  regions to clear the set
- `shell.update(name, value)` — also marks a region dirty
- The expected render loop: call `handle_key`, read dirty set, re-render dirty
  regions, call `mark_all_clean`
- Note that focus changes also add the old and new focused regions to the dirty
  set, so a renderer that only re-renders `dirty_regions` will automatically
  repaint focus transitions


## 11. Document `handle_key` return value in docs (not just source)

**Status: PARTIAL** — `docs/renderer-spec/contract.md` sections 4 and 7 already state
`Shell.handle_key(key)` returns `('exit', value)` or `('continue', None)` and describe
what to do on each. However, this is spread across two sections rather than collected in a
dedicated subsection. No new required-changes work remains here beyond grouping, which can
be done as part of the section-10 edit pass.

### Problem

`Shell.handle_key` returns a `tuple[str, Any]`:

- `('exit', value)` — the shell should stop; `value` is the return value
- `('continue', None)` — the shell should keep running

This is documented in the `Shell.handle_key` source docstring but nowhere in
the renderer-spec docs.  Renderer implementors reading only the docs will not
know what to do with the return value.

### Files affected

- `docs/renderer-spec/contract.md`

### Required changes

Add a brief subsection to `docs/renderer-spec/contract.md` (e.g. under the
dirty-region section or the key dispatch section) that documents:

- The two possible return values of `handle_key`
- That `('exit', value)` means the renderer should stop its event loop and
  return `value` to the caller
- That `('continue', None)` means the renderer should keep running


## Verification Checklist

After making all edits, verify the following:

- `README.md` contains no link to `docs/renderer-boundary.md`
- `ECOSYSTEM.md` contains no link to `docs/renderer-boundary.md`
- no file under `panelmark/` contains the string `renderer-boundary`
- `README.md` no longer claims exact `panelmark-tui` interaction/widget counts
- `ECOSYSTEM.md` no longer claims exact `panelmark-tui` interaction/widget counts
- `ECOSYSTEM.md` no longer mentions `MenuHybrid` or `SubList`
- `docs/custom-interactions.md` no longer recommends private
  `panelmark_tui` helper classes like `_ScrollableList`
- `panelmark/interactions/base.py` no longer mentions `SubList`
- `ECOSYSTEM.md` wording around `RenderContext` / capability queries is consistent
  with the current implementation in `panelmark/draw.py`
- `docs/renderer-spec/contract.md` (or `docs/key-strings.md`) contains a "Key
  string format" section listing canonical `KEY_*` names and the three key
  categories
- `Shell.handle_key` docstring no longer says "blessed convention"
- `docs/renderer-spec/contract.md` contains a "Dirty-region tracking" section
  documenting `dirty_regions`, `mark_all_clean()`, and the render loop pattern
- `docs/renderer-spec/contract.md` documents the `('exit', value)` /
  `('continue', None)` return values of `handle_key`


## Implementation Guidance For An AI Agent

If another AI agent is asked to do this work, it should:

1. Read the following files first:
   - `panelmark/README.md`
   - `panelmark/ECOSYSTEM.md`
   - `panelmark/docs/custom-interactions.md`
   - `panelmark/panelmark/interactions/base.py`
   - `panelmark/docs/renderer-spec/overview.md`
   - `panelmark/docs/renderer-spec/contract.md`
   - `panelmark/panelmark/draw.py`
   - `panelmark/panelmark/shell.py` (for items 9–11)

2. Make only documentation/comment changes unless a tiny docstring correction
   in `panelmark/interactions/base.py` is needed

3. Do not introduce new architecture or feature claims that are not already
   supported by the current repo contents

4. Prefer broad renderer descriptions over detailed renderer inventories in
   `panelmark` core docs

5. After editing, run a repo-wide search in `panelmark/` for:
   - `renderer-boundary`
   - `MenuHybrid`
   - `SubList`
   - `13 interaction`
   - `9 prebuilt`
   - `blessed convention`

6. Confirm that any remaining occurrences are intentional


## Not Identified As Broken During This Review

The following looked broadly aligned during this review and do not need
automatic rewrites unless further checking reveals issues:

- `docs/shell-language.md`
- `docs/draw-commands.md`
- `docs/renderer-spec/overview.md`
- `docs/renderer-spec/contract.md`
- `panelmark/style.py`
- `panelmark/draw.py`
- `panelmark/parser.py`
- `panelmark/layout.py`

That said, if an agent sees an obvious contradiction while making the required
changes above, it should fix it in the same pass.
