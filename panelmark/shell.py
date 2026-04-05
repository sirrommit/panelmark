from .parser import Parser
from .layout import _fixed_width, _fixed_height
from .observer import Observer, ChangeHandle
from .exceptions import RegionNotFoundError


class Shell:
    """Core shell state machine — layout, interactions, focus, and key dispatch.

    This class is renderer-agnostic.  It has no terminal dependency.
    To run in a terminal, use ``panelmark_tui.Shell`` which extends this class
    with ``run()`` and ``run_modal()`` methods, or drive it directly via
    ``panelmark_tui.TUIRenderer``.

    Key dispatch
    ------------
    Call ``handle_key(key)`` with a plain string key name:
    - Printable characters:  ``'a'``, ``'B'``, ``' '``, ``'\\t'``, etc.
    - Named keys:            ``'KEY_UP'``, ``'KEY_DOWN'``, ``'KEY_ENTER'``, etc.
    - Control characters:    ``'\\x11'`` (Ctrl+Q), ``'\\x1b'`` (Escape), etc.

    Returns ``('exit', value)`` when the shell should stop, or
    ``('continue', None)`` otherwise.

    Dirty tracking
    --------------
    After each ``handle_key()`` call, read ``shell.dirty_regions`` to find
    regions that need re-rendering, then call ``shell.mark_all_clean()``.
    ``shell.update()`` also marks regions dirty.
    """

    def __init__(self, definition: str):
        self._layout = Parser().parse(definition)
        self._regions = {}       # name -> Region (resolved geometry)
        self._borders = []       # list[BorderSpec] (resolved border lines)
        self._interactions = {}  # name -> Interaction
        self._observer = Observer()
        self._focus_order = []   # list of region names in tab order
        self._focused = None
        self._dirty = set()      # region names needing redraw
        self._resolve_layout()

    def _resolve_layout(self, width: int = 80, height: int = 24,
                        offset_row: int = 0, offset_col: int = 0):
        regions, borders = self._layout.resolve(width, height,
                                                offset_row=offset_row,
                                                offset_col=offset_col)
        self._regions = {r.name: r for r in regions}
        self._borders = borders
        self._focus_order = [
            r.name for r in sorted(regions, key=lambda r: (r.row, r.col))
        ]

    # ------------------------------------------------------------------
    # Public API — region management
    # ------------------------------------------------------------------

    def assign(self, name: str, interaction) -> None:
        """Assign an interaction to a named region."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")
        if name in self._interactions:
            raise ValueError(
                f"region '{name}' already has an assigned interaction; "
                "call unassign() first")
        interaction._shell = self
        self._interactions[name] = interaction
        self._dirty.add(name)

    def unassign(self, name: str):
        """Remove the interaction assigned to a region."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")
        interaction = self._interactions.pop(name, None)
        if self._focused == name:
            self._focused = None
        return interaction

    def get(self, name: str):
        """Get the current value of a named region."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")
        interaction = self._interactions.get(name)
        if interaction is None:
            return None
        return interaction.get_value()

    def update(self, name: str, value, _updating: set | None = None) -> None:
        """Programmatically set a region's value and mark it dirty."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")
        interaction = self._interactions.get(name)
        if interaction is None:
            return
        interaction.set_value(value)
        self._dirty.add(name)
        self._observer.notify(name, value, updating=_updating)

    def on_change(self, name: str, callback) -> ChangeHandle:
        """Register a callback to fire when a region's value changes."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")

        def _cb(value, updating=None):
            callback(value)

        return self._observer.register(name, _cb)

    def bind(self, source: str, target: str, transform=None) -> ChangeHandle:
        """When source changes, update target with the (optionally transformed) value."""
        if source not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{source}' in this shell")
        if target not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{target}' in this shell")

        def _cb(value, updating=None):
            if transform is not None:
                value = transform(value)
            self.update(target, value, _updating=updating)

        return self._observer.register(source, _cb)

    def set_focus(self, name: str) -> None:
        """Move focus to a named region programmatically."""
        if name not in self._regions:
            raise RegionNotFoundError(
                f"no region named '{name}' in this shell")
        if name not in self._interactions:
            raise ValueError(
                f"region '{name}' has no assigned interaction and cannot "
                "receive focus")
        self._focused = name

    @property
    def focus(self):
        return self._focused

    # ------------------------------------------------------------------
    # Dirty tracking — used by renderers
    # ------------------------------------------------------------------

    @property
    def dirty_regions(self) -> set:
        """Set of region names that need re-rendering."""
        return set(self._dirty)

    def mark_all_clean(self) -> None:
        """Clear the dirty set after the renderer has redrawn all regions."""
        self._dirty.clear()

    # ------------------------------------------------------------------
    # Layout / interaction access — used by renderers
    # ------------------------------------------------------------------

    @property
    def layout(self):
        return self._layout

    @property
    def regions(self) -> dict:
        return self._regions

    @property
    def borders(self) -> list:
        """List of BorderSpec objects for every HSplit border line in the layout."""
        return list(self._borders)

    @property
    def interactions(self) -> dict:
        return self._interactions

    # ------------------------------------------------------------------
    # Key dispatch — the state machine
    # ------------------------------------------------------------------

    def handle_key(self, key: str) -> tuple:
        """Process a key event.

        Parameters
        ----------
        key : str
            A plain string key name.  Printable characters are passed as-is
            (e.g. ``'a'``, ``' '``).  Named keys use panelmark's canonical
            ``KEY_*`` names (e.g. ``'KEY_UP'``, ``'KEY_ENTER'``, ``'KEY_BTAB'``);
            see ``docs/renderer-spec/contract.md`` for the full list.
            Control characters are their literal values (e.g. ``'\\x11'`` for
            Ctrl+Q, ``'\\x1b'`` for Escape).

        Returns
        -------
        tuple
            ``('exit', value)`` — renderer should stop and return *value*.
            ``('continue', None)`` — renderer should keep running.
        """
        # Exit signals
        if key in ('\x11', '\x1b'):   # Ctrl+Q or Escape
            return ('exit', None)

        # Focus movement
        if key in ('\t', 'KEY_TAB'):
            self._move_focus(1)
            return ('continue', None)
        if key == 'KEY_BTAB':
            self._move_focus(-1)
            return ('continue', None)

        # Dispatch to focused interaction
        if self._focused and self._focused in self._interactions:
            interaction = self._interactions[self._focused]
            changed, value = interaction.handle_key(key)
            self._dirty.add(self._focused)
            if changed:
                self._observer.notify(self._focused, value)
            should_exit, rv = interaction.signal_return()
            if should_exit:
                return ('exit', rv)

        return ('continue', None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _move_focus(self, direction: int) -> None:
        """Move focus by direction (+1 or -1) in tab order."""
        interactive = [
            n for n in self._focus_order
            if n in self._interactions and self._interactions[n].is_focusable
        ]
        if len(interactive) < 2:
            return
        if self._focused not in interactive:
            self._focused = interactive[0]
            return
        idx = interactive.index(self._focused)
        old_focus = self._focused
        self._focused = interactive[(idx + direction) % len(interactive)]
        self._dirty.add(old_focus)
        self._dirty.add(self._focused)
