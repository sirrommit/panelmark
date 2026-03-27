# Renderer Readiness Checklist

## Purpose

This checklist defines what it means for a renderer to be ready.  It is the operational
form of the renderer contract: if the spec defines the rules, this checklist defines
when a renderer passes them.

It is useful even if no third-party renderer is ever built, as an internal definition of
"ready" for first-party renderers.


## Core Readiness

A renderer is not ready until all of the following are true.

### Shell hosting

- [ ] can create and run a shell successfully
- [ ] can render all assigned regions
- [ ] can return shell result values correctly

### Interaction hosting

- [ ] passes correct render context to interactions
- [ ] executes draw commands correctly
- [ ] respects focus state when calling `render(context, focused)`
- [ ] supports shell dirty/redraw semantics correctly

### Input handling

- [ ] collects input events reliably
- [ ] maps events into the expected `Shell.handle_key()` form
- [ ] supports focus movement and submit behavior correctly

### Layout behavior

- [ ] respects resolved region geometry
- [ ] handles resize or viewport changes correctly if supported
- [ ] clips output correctly when interactions emit commands at the boundary

### Exit semantics

- [ ] shell exits when `handle_key()` returns `('exit', value)`
- [ ] interaction submit/accept behavior is preserved through the shell
- [ ] cancellation and close behavior is consistent


## Documentation Readiness

A renderer is not ready until its documentation states:

- [ ] which compatibility level it claims
- [ ] which portable APIs it supports (if claiming portable-library compatibility)
- [ ] which additions are renderer-specific
- [ ] any important known limitations


## Portable Library Readiness

If the renderer claims `portable-library-compatible`, verify:

- [ ] portable widgets use standardized call syntax
- [ ] return values match the portable contract
- [ ] cancellation semantics are consistent
- [ ] any deviations from the portable contract are documented explicitly


## Extension Hygiene

Before calling a renderer ready, verify:

- [ ] renderer-specific APIs are namespaced under the renderer package
- [ ] nonstandard additions are marked as renderer-specific in docs
- [ ] portable and renderer-specific features are not mixed ambiguously


## Regression Checklist

Before a release, verify:

- [ ] existing portable APIs still use the same call syntax
- [ ] return semantics did not drift
- [ ] compatibility claims remain accurate
- [ ] renderer-specific additions did not accidentally become undocumented


## Future Additions

A later version of this checklist may add:

- conformance tests
- capability matrices
- required example applications
