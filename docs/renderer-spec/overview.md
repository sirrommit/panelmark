# Renderer Specification: Overview

## Purpose

This specification defines what it means to be a compatible `panelmark` renderer.

It lives in the `panelmark` core repo because it describes the platform contract, not any
single renderer's implementation choices.  The normative rules belong in the place that
owns the shared model.

See also:

- [contract.md](contract.md) — required renderer behavior
- [portable-library.md](portable-library.md) — optional portable widget layer
- [extensions.md](extensions.md) — renderer-specific additions and compatibility labels
- [readiness.md](readiness.md) — checklist for declaring a renderer ready


## Why A Renderer Spec

Without a renderer spec:

- "renderer compatibility" is undefined
- renderer behavior drifts over time
- core-vs-renderer boundaries become informal
- portability claims are hard to verify
- each new renderer is a fresh design exercise

With a renderer spec:

- renderer authors know what must be implemented
- application authors know what they can rely on portably
- renderer-specific features can be added without implying they are portable
- readiness has a concrete definition


## Layered Structure

The spec is organized in layers of increasing optionality.

### Layer 1: Core Renderer Contract

Defines what every renderer must implement to host a `panelmark` shell.  This is the
minimum required for compatibility.

Covers: shell hosting, region rendering, input dispatch, focus handling, dirty/redraw,
shell return semantics, interaction semantics.

See [contract.md](contract.md).


### Layer 2: Portable Standard Library

Defines optional but standardized portable interactions and widgets, if the project
adopts them.

The portable standard library standardizes call signatures, return semantics, and lifecycle
behavior.  It does not standardize visual shape, renderer architecture, or native vs
custom implementation strategy.

See [portable-library.md](portable-library.md).


### Layer 3: Renderer Extensions

Renderer-specific additions are allowed and often desirable.  The spec requires only that
they are clearly marked as renderer-specific and not presented as part of the portable
contract.

See [extensions.md](extensions.md).


### Layer 4: Compatibility and Readiness

Defines what it means for a renderer to be ready for use and what compatibility level it
claims.

See [readiness.md](readiness.md).


## Design Rationale

The spec is layered because there are two distinct portability stories in `panelmark`.

The first story is the shell and runtime model: shell definitions, layout resolution,
interaction semantics, shell state machine behavior.  This is the most fundamental and most
stable layer.  It does not vary much across renderers.

The second story is portable application functionality: alerts, confirms, input prompts,
file selection, progress.  This is useful but more renderer-shaped and more likely to
vary.  Collapsing both into one undifferentiated layer would either bloat the core contract
or leave the portability story too weak for real applications.

The layered structure also avoids forcing renderers to implement everything or nothing.
A renderer can be core-compatible first and portable-library-compatible later.

The spec is intentionally behavioral, not structural.  Renderers should be free to differ
internally as long as they preserve the shared semantics.  Compatibility is not about
copying the first-party renderer's architecture.
