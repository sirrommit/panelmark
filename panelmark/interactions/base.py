from abc import ABC, abstractmethod
from panelmark.draw import DrawCommand, RenderContext


class Interaction(ABC):
    _shell = None  # Set by Shell.assign()

    @property
    def is_focusable(self) -> bool:
        """Return True if this interaction can meaningfully receive keyboard focus.
        Display-only interactions override this to return False."""
        return True

    @abstractmethod
    def render(self, context: RenderContext, focused: bool = False) -> list[DrawCommand]:
        """Return draw commands describing the current visual state of this interaction.

        Commands use region-relative coordinates: ``(0, 0)`` is the top-left
        cell of this interaction's assigned region. The renderer maps them to
        screen-absolute positions when executing via its command executor.

        The returned list should be a complete description of the interaction's
        visual state for the given context dimensions. Partial updates are not
        supported — callers may skip calling ``render()`` for regions they
        determine are unchanged, so the list must always be fully self-contained.

        Parameters
        ----------
        context:
            Rendering context carrying region dimensions (``context.width``,
            ``context.height``) and renderer capability flags. Use
            ``context.supports(feature)`` to degrade gracefully on renderers
            that lack a capability.
        focused:
            True if this interaction currently has keyboard focus.
        """
        ...

    @abstractmethod
    def handle_key(self, key) -> tuple:
        """
        Handle a keypress.
        Returns (value_changed, new_value).
        new_value is whatever Shell.get returns.
        """
        ...

    @abstractmethod
    def get_value(self):
        """Return the current value of this interaction."""
        ...

    @abstractmethod
    def set_value(self, value) -> None:
        """Set the current value of this interaction."""
        ...

    def signal_return(self) -> tuple:
        """
        Called after handle_key to check if this interaction wants Shell.run() to return.
        Returns (should_exit, return_value).
        """
        return False, None
