"""Draw commands and render context for the panelmark renderer abstraction.

Interactions return a ``list[DrawCommand]`` from their ``render()`` method
rather than performing side effects directly. Each renderer provides an
executor that translates the command list to its output surface (terminal,
HTML, etc.).

Coordinate system
-----------------
All row and column values in draw commands are **region-relative**:
``(0, 0)`` is the top-left cell of the interaction's assigned region.
The executor maps these to screen-absolute or document-absolute coordinates
internally. Interactions never need to know their absolute position.

Style dict
----------
The optional ``style`` argument on ``WriteCmd`` and ``FillCmd`` is a plain
dict. All keys are optional. Renderers apply the keys they support and ignore
the rest — unknown keys are not an error.

Valid keys and values::

    bold       bool   — bold / heavy weight
    italic     bool   — italic (renderers that lack italic use normal)
    underline  bool   — underline
    reverse    bool   — swap foreground and background colours
    color      str    — foreground colour name: 'red', 'green', 'yellow',
                        'blue', 'magenta', 'cyan', 'white', 'black'
    bg         str    — background colour name (same values as color)

Example — a minimal custom render() implementation::

    from panelmark.draw import WriteCmd, FillCmd, RenderContext, DrawCommand

    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        text = self._value[:context.width].ljust(context.width)
        style = {'reverse': True} if focused else None
        return [
            FillCmd(row=0, col=0, width=context.width, height=context.height),
            WriteCmd(row=0, col=0, text=text, style=style),
        ]
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RenderContext:
    """Read-only rendering context passed to ``Interaction.render()``.

    Carries the dimensions of the interaction's assigned region and a set
    of capability flags describing what the current renderer supports.
    Interactions use ``supports()`` to degrade gracefully on renderers that
    lack a capability rather than failing or producing garbled output.

    Attributes
    ----------
    width:
        Width of the region in character columns.
    height:
        Height of the region in character rows.
    capabilities:
        Frozenset of feature strings supported by the renderer. Do not
        inspect this directly — use ``supports(feature)`` instead.
    """

    width: int
    height: int
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def supports(self, feature: str) -> bool:
        """Return True if the renderer supports *feature*.

        Known feature strings (renderers may support any subset):

        ``'color'``
            At least 8 foreground/background colours are available.
        ``'256color'``
            256-colour palette is available.
        ``'truecolor'``
            24-bit (16 million colour) palette is available.
        ``'unicode'``
            Unicode characters (box-drawing, block elements, etc.) render
            correctly. ASCII-only renderers do not set this.
        ``'cursor'``
            A text cursor can be positioned within the region. Set by TUI
            renderers and interactive web renderers; not set by static HTML.
        ``'italic'``
            Italic text is visually distinct from normal weight text.

        Returns False for unknown or unsupported feature strings.
        """
        return feature in self.capabilities


@dataclass
class WriteCmd:
    """Write styled text at region-relative (row, col).

    The text is written left-to-right starting at the given position.
    No automatic clipping is performed — the executor clips to the region
    boundary. Callers should ensure text does not exceed ``context.width``
    columns from ``col``.

    Parameters
    ----------
    row:
        Zero-based row offset from the top of the region.
    col:
        Zero-based column offset from the left of the region.
    text:
        The string to write. Should not contain newlines.
    style:
        Optional style dict. See module docstring for valid keys.
    """

    row: int
    col: int
    text: str
    style: dict | None = None


@dataclass
class FillCmd:
    """Fill a rectangle with a repeated character, optionally styled.

    Useful for clearing a region before writing content, or for drawing
    a styled background block.

    Parameters
    ----------
    row:
        Zero-based row offset of the top-left corner.
    col:
        Zero-based column offset of the top-left corner.
    width:
        Number of columns to fill.
    height:
        Number of rows to fill.
    char:
        The character to fill with. Defaults to a space (blank/clear).
    style:
        Optional style dict. See module docstring for valid keys.
    """

    row: int
    col: int
    width: int
    height: int
    char: str = ' '
    style: dict | None = None


@dataclass
class CursorCmd:
    """Hint: place the text cursor at region-relative (row, col).

    This is a positioning hint, not a draw operation. Renderers that
    support a visible text cursor (``context.supports('cursor')``) move
    the cursor here after executing all other commands in the list.
    Renderers that do not support a cursor ignore this command entirely.

    There should be at most one ``CursorCmd`` per command list. If multiple
    are present, the executor uses the last one.

    Parameters
    ----------
    row:
        Zero-based row offset from the top of the region.
    col:
        Zero-based column offset from the left of the region.
    """

    row: int
    col: int


#: Union type alias for the three command types.
#: A ``render()`` method returns ``list[DrawCommand]``.
DrawCommand = WriteCmd | FillCmd | CursorCmd
