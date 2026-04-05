# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] — 2026-04-05

### Added

- `BorderSpec` dataclass in `panelmark.layout` — carries `row`, `col`, `width`,
  `style`, and optional `title` for each internal HSplit separator line.
- `Shell.borders` read-only property — exposes the list of `BorderSpec` objects
  for the current layout.
- `Region.heading` field — stores the `__text__` heading string parsed from a
  panel definition block.

### Changed

- `LayoutModel.resolve()` now returns `(regions, borders)` instead of just
  `regions`. `regions` is a `list[Region]`; `borders` is a `list[BorderSpec]`
  for all internal separator lines. Outer frame lines (`|=====|`) are excluded.

### Fixed

- VSplit equal-distribution: two or more fill-width columns now share available
  width as equally as possible, differing by at most one character.

---

## [0.1.0] — 2026-03-24

Initial release.

### Added

- Shell definition language — ASCII-art DSL for declaring panel layouts.
- `Shell` class — state machine driving layout, focus, and dirty-region
  tracking.
- `Interaction` abstract base class — defines the `render()` / `handle_key()` /
  `get_value()` contract.
- Draw-command API:
  - `RenderContext(width, height, capabilities)` — passed to `render()` in place
    of `region` and `term`.
  - `WriteCmd(row, col, text, style)` — write styled text at region-relative
    coordinates.
  - `FillCmd(row, col, width, height, char, style)` — fill a rectangle.
  - `CursorCmd(row, col)` — hint to position the terminal cursor.
  - `DrawCommand` type alias covering all three command types.
  - All types importable from `panelmark.interactions` and `panelmark.draw`.
- Shell syntax features:
  - `$name$` region names.
  - `NR` and `N%R` row-count specs.
  - Fixed-width (`N`) and percentage-width (`N%`) column specs.
  - `||` double-line vertical divider; `|` single-line divider.
  - `|=== Title ===|` and `|--- title ---|` horizontal border lines with
    optional centred titles.
  - `__text__` heading annotation on panel blocks (stored in `Region.heading`).
  - `<bold>text</>` inline style markup in border titles and the shell title
    line.
  - `#` line comments and `/* */` block comments.
- `Shell` state-machine methods: `assign()`, `unassign()`, `get()`, `update()`,
  `handle_key()`, `set_focus()`, `on_change()`, `bind()`.
- Dirty-region tracking: `dirty_regions`, `mark_clean()`, `mark_all_clean()`.
- `Shell.regions` and `Shell.interactions` read-only properties.
- `run_modal()` / `run_at()` layout helpers for modal shells.
- Renderer contract documentation (`docs/renderer-spec/`).
- Custom interaction guide (`docs/custom-interactions.md`).
- Draw-command reference (`docs/draw-commands.md`).
- Shell language reference (`docs/shell-language.md`).
- PyPI packaging: `pyproject.toml`, `LICENSE`, `CHANGELOG.md`, `AUTHORS`.

[Unreleased]: https://github.com/sirrommit/panelmark/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/sirrommit/panelmark/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sirrommit/panelmark/releases/tag/v0.1.0
