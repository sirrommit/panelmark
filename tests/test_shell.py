import pytest
from panelmark import Shell
from panelmark.interactions import Interaction
from panelmark.exceptions import RegionNotFoundError, CircularUpdateError


SIMPLE_SHELL = """
|=====|
|{12R $menu$ }|
|=====|
"""

TWO_REGION_SHELL = """
|=====|
|{12R $left$ }|{12R $right$ }|
|=====|
"""


class FakeInteraction(Interaction):
    """Minimal stub interaction for unit testing Shell logic."""
    def __init__(self, value=None, focusable=True):
        self._value = value
        self._focusable = focusable
        self._signal = False
        self._signal_value = None

    @property
    def is_focusable(self):
        return self._focusable

    def render(self, region, term, focused=False):
        pass

    def handle_key(self, key):
        return False, self._value

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def signal_return(self):
        return self._signal, self._signal_value

    def arm_return(self, value):
        self._signal = True
        self._signal_value = value


@pytest.fixture
def shell():
    return Shell(SIMPLE_SHELL)


@pytest.fixture
def two_region_shell():
    return Shell(TWO_REGION_SHELL)


class TestShellAssign:
    def test_assign_interaction(self, shell):
        shell.assign('menu', FakeInteraction())

    def test_assign_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.assign('nonexistent', FakeInteraction())

    def test_assign_twice_raises(self, shell):
        shell.assign('menu', FakeInteraction())
        with pytest.raises(ValueError):
            shell.assign('menu', FakeInteraction())

    def test_assign_sets_shell_reference(self, shell):
        m = FakeInteraction()
        shell.assign('menu', m)
        assert m._shell is shell


class TestShellUnassign:
    def test_unassign_returns_interaction(self, shell):
        m = FakeInteraction()
        shell.assign('menu', m)
        assert shell.unassign('menu') is m

    def test_unassign_nonexistent_returns_none(self, shell):
        assert shell.unassign('menu') is None

    def test_unassign_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.unassign('ghost')

    def test_unassign_allows_reassign(self, shell):
        shell.assign('menu', FakeInteraction())
        shell.unassign('menu')
        shell.assign('menu', FakeInteraction())


class TestShellGet:
    def test_get_value_after_assign(self, shell):
        shell.assign('menu', FakeInteraction(value='hello'))
        assert shell.get('menu') == 'hello'

    def test_get_unassigned_region_returns_none(self, shell):
        assert shell.get('menu') is None

    def test_get_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.get('ghost')


class TestShellUpdate:
    def test_update_changes_value(self, shell):
        shell.assign('menu', FakeInteraction(value='A'))
        shell.update('menu', 'B')
        assert shell.get('menu') == 'B'

    def test_update_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.update('ghost', 'value')

    def test_update_unassigned_region_silent(self, shell):
        shell.update('menu', 'value')

    def test_update_marks_dirty(self, shell):
        shell.assign('menu', FakeInteraction())
        shell.mark_all_clean()
        shell.update('menu', 'x')
        assert 'menu' in shell.dirty_regions


class TestShellOnChange:
    def test_on_change_fires_callback(self, shell):
        shell.assign('menu', FakeInteraction())
        received = []
        shell.on_change('menu', lambda v: received.append(v))
        shell.update('menu', 'hello')
        assert received == ['hello']

    def test_on_change_returns_handle(self, shell):
        shell.assign('menu', FakeInteraction())
        handle = shell.on_change('menu', lambda v: None)
        assert hasattr(handle, 'remove')

    def test_on_change_handle_remove(self, shell):
        shell.assign('menu', FakeInteraction())
        received = []
        handle = shell.on_change('menu', lambda v: received.append(v))
        handle.remove()
        shell.update('menu', 'test')
        assert received == []

    def test_on_change_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.on_change('ghost', lambda v: None)


class TestShellBind:
    def test_bind_propagates_value(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.bind('left', 'right')
        sh.update('left', 'hello')
        assert sh.get('right') == 'hello'

    def test_bind_with_transform(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.bind('left', 'right', transform=lambda v: v.upper())
        sh.update('left', 'hello')
        assert sh.get('right') == 'HELLO'

    def test_bind_nonexistent_source_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.bind('ghost', 'left')

    def test_bind_nonexistent_target_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.bind('left', 'ghost')

    def test_circular_bind_raises(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.bind('left', 'right')
        sh.bind('right', 'left')
        with pytest.raises(CircularUpdateError):
            sh.update('left', 'test')


class TestShellFocus:
    def test_set_focus(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.set_focus('right')
        assert sh.focus == 'right'

    def test_set_focus_nonexistent_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.set_focus('ghost')

    def test_set_focus_unassigned_raises(self, two_region_shell):
        with pytest.raises(ValueError):
            two_region_shell.set_focus('left')

    def test_focus_property_initially_none(self, shell):
        assert shell.focus is None


class TestShellHandleKey:
    def test_ctrl_q_returns_exit(self, shell):
        shell.assign('menu', FakeInteraction())
        status, value = shell.handle_key('\x11')
        assert status == 'exit'
        assert value is None

    def test_escape_returns_exit(self, shell):
        shell.assign('menu', FakeInteraction())
        status, value = shell.handle_key('\x1b')
        assert status == 'exit'
        assert value is None

    def test_tab_moves_focus(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.set_focus('left')
        status, _ = sh.handle_key('\t')
        assert status == 'continue'
        assert sh.focus == 'right'

    def test_shift_tab_moves_focus_back(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.set_focus('right')
        sh.handle_key('KEY_BTAB')
        assert sh.focus == 'left'

    def test_interaction_signal_return_exits(self, shell):
        m = FakeInteraction()
        m.arm_return('result_value')
        shell.assign('menu', m)
        shell.set_focus('menu')
        status, value = shell.handle_key('KEY_ENTER')
        assert status == 'exit'
        assert value == 'result_value'

    def test_key_dispatch_marks_dirty(self, shell):
        shell.assign('menu', FakeInteraction())
        shell.set_focus('menu')
        shell.mark_all_clean()
        shell.handle_key('KEY_DOWN')
        assert 'menu' in shell.dirty_regions

    def test_no_focus_key_is_noop(self, shell):
        shell.assign('menu', FakeInteraction())
        # focus is None — should not crash
        status, _ = shell.handle_key('KEY_DOWN')
        assert status == 'continue'


class TestShellDirty:
    def test_assign_marks_dirty(self, shell):
        shell.mark_all_clean()
        shell.assign('menu', FakeInteraction())
        assert 'menu' in shell.dirty_regions

    def test_mark_all_clean_clears(self, shell):
        shell.assign('menu', FakeInteraction())
        shell.mark_all_clean()
        assert shell.dirty_regions == set()

    def test_tab_marks_both_regions_dirty(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', FakeInteraction())
        sh.assign('right', FakeInteraction())
        sh.set_focus('left')
        sh.mark_all_clean()
        sh.handle_key('\t')
        assert 'left' in sh.dirty_regions
        assert 'right' in sh.dirty_regions


class TestShellRegionNotFound:
    def test_all_methods_raise_on_bad_name(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.assign('bad', FakeInteraction())
        with pytest.raises(RegionNotFoundError):
            shell.unassign('bad')
        with pytest.raises(RegionNotFoundError):
            shell.get('bad')
        with pytest.raises(RegionNotFoundError):
            shell.update('bad', 'val')
        with pytest.raises(RegionNotFoundError):
            shell.on_change('bad', lambda v: None)
        with pytest.raises(RegionNotFoundError):
            shell.set_focus('bad')
