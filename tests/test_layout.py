import pytest
from panelmark.layout import (
    LayoutModel, Region, HSplit, VSplit, Panel, BorderRow,
    _declared_width, _declared_height, _is_all_fill,
)
from panelmark.parser import Parser


def make_panel(row_count=None, row_count_is_pct=False, row_pct=None,
               name=None, heading=None, num_rows_def=1,
               width=None, is_pct=False, pct=None):
    return Panel(name=name, heading=heading,
                 width=width, is_pct=is_pct, pct=pct,
                 row_count=row_count, row_count_is_pct=row_count_is_pct,
                 row_pct=row_pct, num_rows_def=num_rows_def)


class TestDeclaredWidth:
    """Tests for _declared_width via Panel nodes."""

    def test_single_fill_column(self):
        p = make_panel(width=None, is_pct=False)
        assert _declared_width(p, 78, 77) == 78

    def test_two_equal_pct_columns(self):
        # pct_base for term_width=80, 2 cols: 78 - 1 = 77
        p = make_panel(is_pct=True, pct=50.0)
        assert _declared_width(p, 77, 77) == 38

    def test_fixed_width(self):
        p = make_panel(width=25)
        assert _declared_width(p, 78, 77) == 25

    def test_percentage_width(self):
        # pct_base=77, 25% → int(77 * 25 / 100) = 19
        p = make_panel(is_pct=True, pct=25.0)
        assert _declared_width(p, 77, 77) == 19

    def test_hsplit_delegates_to_child(self):
        panel = make_panel(width=25)
        node = HSplit(top=panel, bottom=None, border=None)
        assert _declared_width(node, 78, 77) == 25

    def test_vsplit_takes_all_available(self):
        node = VSplit(left=make_panel(), right=make_panel(), divider='single')
        assert _declared_width(node, 78, 77) == 78


class TestDeclaredHeight:
    """Tests for _declared_height via Panel and composite nodes."""

    def test_explicit_row_count(self):
        p = make_panel(row_count=12)
        assert _declared_height(p, 24) == 12

    def test_percentage_row_count(self):
        p = make_panel(row_count=50, row_count_is_pct=True, row_pct=50.0)
        assert _declared_height(p, 24) == 12

    def test_fallback_to_num_rows_def(self):
        p = make_panel(num_rows_def=5)
        assert _declared_height(p, 24) == 5

    def test_fallback_minimum_one(self):
        p = make_panel(num_rows_def=0)
        assert _declared_height(p, 24) == 1

    def test_hsplit_sums_children(self):
        top = make_panel(row_count=10)
        bot = make_panel(row_count=5)
        node = HSplit(top=top, bottom=bot, border=BorderRow('single', None))
        # 10 + 1 (border) + 5 = 16
        assert _declared_height(node, 24) == 16

    def test_vsplit_takes_max_child(self):
        left = make_panel(row_count=10)
        right = make_panel(row_count=5)
        node = VSplit(left=left, right=right, divider='single')
        assert _declared_height(node, 24) == 10


class TestLayoutModelResolve:
    def test_resolve_simple_shell(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert len(regions) == 1
        assert regions[0].name == 'menu'
        assert regions[0].height == 12

    def test_resolve_two_columns(self):
        shell = """
|=====|
|{50% 12R $left$ }|{12R $right$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name for r in regions}
        assert 'left' in names
        assert 'right' in names

    def test_resolve_border_advances_row(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert regions[0].row == 1

    def test_resolve_region_col_position(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert regions[0].col == 1

    def test_resolve_percentage_width(self):
        shell = """
|=====|
|{25% 12R $side$ }|{ 12R $main$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        side = next(r for r in regions if r.name == 'side')
        assert side.width == 19

    def test_resolve_fill_left_fixed_right(self):
        # fill | fixed-14: right must get exactly 14, left gets the rest
        shell = """
|=====|
|{12R $path$ }|{14 12R $filter$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        by_name = {r.name: r for r in regions}
        assert by_name['filter'].width == 14
        # left border(1) + path_width + divider(1) + 14 + right border(1) = 80
        # => path_width = 80 - 1 - 1 - 14 - 1 = 63
        assert by_name['path'].width == 63

    def test_resolve_fixed_left_fill_right(self):
        # fixed-14 | fill: left gets 14, right gets the rest (existing behaviour)
        shell = """
|=====|
|{14 12R $filter$ }|{12R $path$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        by_name = {r.name: r for r in regions}
        assert by_name['filter'].width == 14
        assert by_name['path'].width == 63

    def test_resolve_unnamed_columns_excluded(self):
        shell = """
|=====|
|{12R unnamed_col }|{12R $named$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert all(r.name == 'named' for r in regions)
        assert len(regions) == 1

    def test_region_is_frozen(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        with pytest.raises((AttributeError, TypeError)):
            regions[0].name = 'changed'

    def test_resolve_partial_border_split(self):
        """Columns with a partial border produce two separate regions."""
        shell = """\
|=====|
|{25% 12R $top$ }|{12R $right$ }|
|-----           |{             }|
|{25% 12R $bot$ }|{             }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name: r for r in regions}
        assert 'top' in names
        assert 'bot' in names
        assert 'right' in names
        # top and bot should be at different rows
        assert names['top'].row != names['bot'].row
        # right should span from where top is to below bot (height = top + pb + bot)
        assert names['right'].height == names['top'].height + 1 + names['bot'].height

    def test_resolve_two_fill_columns_equal(self):
        """Two fill columns must share available width equally."""
        shell = """
|=====|
|{12R $left$ }|{12R $right$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        by_name = {r.name: r for r in regions}
        # Inner width = 78, 1 divider → 77 content chars → 38 + 39 = 77
        assert by_name['left'].width == 38
        assert by_name['right'].width == 39

    def test_resolve_two_fill_columns_even_width(self):
        """Two fill columns on an even inner width each get exactly half."""
        # Inner width = 79 (term_width=81), 1 divider → 78 content → 39 each
        shell = """
|=====|
|{12R $a$ }|{12R $b$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(81, 24)
        by_name = {r.name: r for r in regions}
        assert by_name['a'].width == 39
        assert by_name['b'].width == 39

    def test_resolve_three_fill_columns_equal(self):
        """Three fill columns must share available width as equally as possible."""
        shell = """
|=====|
|{12R $a$ }|{12R $b$ }|{12R $c$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        by_name = {r.name: r for r in regions}
        widths = [by_name['a'].width, by_name['b'].width, by_name['c'].width]
        # Total content = 78 - 2 dividers = 76; 76 // 3 = 25 each, remainder 1 falls right
        assert widths[0] == 25
        assert widths[1] == 25
        assert widths[2] == 26

    def test_resolve_fill_columns_differ_by_at_most_one(self):
        """With any terminal width, fill columns must differ in width by at most 1."""
        shell = """
|=====|
|{12R $a$ }|{12R $b$ }|{12R $c$ }|
|=====|
"""
        model = Parser().parse(shell)
        for term_width in range(20, 120):
            regions = model.resolve(term_width, 24)
            by_name = {r.name: r for r in regions}
            widths = [by_name[n].width for n in ('a', 'b', 'c')]
            assert max(widths) - min(widths) <= 1, (
                f"term_width={term_width}: widths={widths} differ by more than 1"
            )

    def test_resolve_fill_columns_sum_to_available(self):
        """Fill column widths plus dividers must equal the inner terminal width."""
        shell = """
|=====|
|{12R $a$ }|{12R $b$ }|{12R $c$ }|
|=====|
"""
        model = Parser().parse(shell)
        for term_width in range(20, 120):
            regions = model.resolve(term_width, 24)
            by_name = {r.name: r for r in regions}
            total = by_name['a'].width + by_name['b'].width + by_name['c'].width
            # inner width = term_width - 2 outer borders; minus 2 dividers = content
            expected_content = term_width - 2 - 2
            assert total == expected_content, (
                f"term_width={term_width}: content={total} != {expected_content}"
            )

    def test_resolve_fixed_fill_unchanged_by_fix(self):
        """Fixed-left + fill-right behaviour must be unchanged after the fill fix."""
        shell = """
|=====|
|{14 12R $filter$ }|{12R $path$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        by_name = {r.name: r for r in regions}
        assert by_name['filter'].width == 14
        assert by_name['path'].width == 63

    def test_is_all_fill_panel_fill(self):
        assert _is_all_fill(make_panel(width=None, is_pct=False)) is True

    def test_is_all_fill_panel_fixed(self):
        assert _is_all_fill(make_panel(width=25)) is False

    def test_is_all_fill_panel_pct(self):
        assert _is_all_fill(make_panel(is_pct=True, pct=50.0)) is False

    def test_is_all_fill_vsplit_all_fill(self):
        node = VSplit(left=make_panel(), right=make_panel(), divider='single')
        assert _is_all_fill(node) is True

    def test_is_all_fill_vsplit_one_fixed(self):
        node = VSplit(left=make_panel(width=25), right=make_panel(), divider='single')
        assert _is_all_fill(node) is False

    def test_partial_border_col_height_stretch(self):
        """A column without a partial border stretches to match split column."""
        shell = """\
|=====|
|{25%  8R $a$ }|{ 6R $b$ }|
|---           |{         }|
|{25%  8R $c$ }|{         }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name: r for r in regions}
        # Col 0: 8 + pb + 8 = 17 total height; col 1 stretches to 17
        assert names['b'].height == 17
