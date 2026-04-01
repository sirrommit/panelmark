# Documentation TODO: panelmark

All panelmark-docs links in this file use the base:
`https://github.com/sirrommit/panelmark-docs/blob/main/docs`

---

## README.md

### Fix stale content

- [x] On line 26, replace the broken cross-repo link
  `[panelmark-tui/KNOWN_LIMITATIONS.md](../panelmark-tui/KNOWN_LIMITATIONS.md)`
  with a link to panelmark-docs:
  `[panelmark-tui limitations](https://github.com/sirrommit/panelmark-docs/blob/main/docs/panelmark-tui/limitations.md)`

### Replace local docs/ links with panelmark-docs links

The Documentation table on lines 100–107 currently links to local files that
duplicate content now living in panelmark-docs. Replace that entire table with
the following:

```markdown
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
```

### Fix stale Ecosystem table

The Ecosystem section (lines 117–122) currently lists panelmark-web as
`*(planned)*` and omits panelmark-html. Replace the entire Ecosystem section
with:

```markdown
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
```

Remove the line `See [ECOSYSTEM.md](ECOSYSTEM.md) for the full planned ecosystem design.`
(the new link above replaces it).

### Verify feature status table

- [x] Read the current feature status table (lines 12–25) and verify each entry
  is accurate against the current codebase. No content changes are expected, but
  confirm before finishing.

---

## Local docs/ folder

The local `docs/` tree duplicates content that is now canonical in panelmark-docs.
Process each file as follows:

- [x] `docs/shell-language.md` — content is now at
  `https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/syntax.md`
  and related pages. Delete `docs/shell-language.md` and confirm README no longer
  links to it (the new Documentation table above already removes the link).

- [x] `docs/draw-commands.md` — content is covered by
  `https://github.com/sirrommit/panelmark-docs/blob/main/docs/renderer-spec/contract.md`.
  Delete `docs/draw-commands.md`.

- [x] `docs/custom-interactions.md` — content is covered by
  `https://github.com/sirrommit/panelmark-docs/blob/main/docs/shell-language/examples.md`.
  Delete `docs/custom-interactions.md`.

- [x] `docs/renderer-spec/overview.md`, `docs/renderer-spec/contract.md`,
  `docs/renderer-spec/portable-library.md`, `docs/renderer-spec/extensions.md`,
  `docs/renderer-spec/readiness.md` — all mirrored in panelmark-docs under
  `docs/renderer-spec/`. Delete the entire `docs/renderer-spec/` directory.

- [x] After deleting the above, confirm that no other file in this repo links to
  any of the deleted paths. Run:
  `grep -r "docs/shell-language\|docs/draw-commands\|docs/custom-interactions\|docs/renderer-spec" . --include="*.md" -l`
  and resolve any remaining references.

### Housekeeping files to retain

- [x] `ECOSYSTEM.md` — superseded by the panelmark-docs ecosystem page. Delete
  it only after confirming the Ecosystem table in README has been updated (above).
  The file can be deleted once README no longer references it.

- [x] `RENDER_ABSTRACTION.md` and `DRAW_MIGRATION.md` — internal working notes.
  Check whether they contain content not in panelmark-docs:
  - If yes: keep them; add a note at the top: "Internal working note. See
    [ecosystem overview](https://github.com/sirrommit/panelmark-docs/blob/main/docs/ecosystem.md)
    for the authoritative design rationale."
  - If no: delete them.

- [x] `panelmark/DOCS_TODO.md` (inside the Python package directory, not the repo
  root) — read it, then delete it. Any open items should be transferred to this
  file or to panelmark-docs issues before deletion.

---

## Validation

- [x] Grep for any remaining relative cross-repo links:
  `grep -n "\.\./panelmark-tui\|\.\./panelmark-html\|\.\./panelmark-web" README.md`
  Result must be empty.

- [x] Grep for any remaining links to deleted local docs:
  `grep -n "docs/shell-language\|docs/draw-commands\|docs/custom-interactions\|docs/renderer-spec\|ECOSYSTEM\.md" README.md`
  Result must be empty.

- [x] Confirm panelmark-web is listed in the Ecosystem table (not "(planned)").

- [x] Confirm panelmark-html is listed in the Ecosystem table.

- [x] Run tests (doc-only change — no automated check exists for README content;
  state this explicitly in the commit message):
  `cd /home/sirrommit/claude_play/panelmark && .venv/bin/pytest -q`
  Tests should pass unchanged.

- [x] Review `git diff` and confirm only `README.md`, deleted docs files, and
  housekeeping files are changed. No Python source changes.

- [ ] Commit:
  ```
  docs: replace local docs/ with panelmark-docs links; fix stale ecosystem table
  ```

- [ ] Push to `origin main`.
