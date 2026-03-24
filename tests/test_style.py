"""Tests for panelmark.style — parsing functions only."""
import pytest
from panelmark.style import (
    strip_comments,
    parse_styled,
    styled_plain_text,
    styled_visual_len,
)


class TestStripComments:
    def test_no_comments(self):
        text = '|=====|\n|{$x$}|\n|=====|'
        assert strip_comments(text) == text

    def test_inline_comment_removed(self):
        text = '|=== Title ===| /* a comment */\n|{$x$}|'
        result = strip_comments(text)
        assert '/*' not in result and '*/' not in result and 'a comment' not in result

    def test_inline_comment_preserves_other_content(self):
        text = '|=== Title ===| /* comment */\n|{$x$}|'
        result = strip_comments(text)
        assert '|=== Title ===|' in result and '|{$x$}|' in result

    def test_multiline_comment_preserves_line_count(self):
        text = '|=====|\n/* line1\nline2\nline3 */\n|{$x$}|\n|=====|'
        result = strip_comments(text)
        assert result.count('\n') == text.count('\n')

    def test_comment_only_line_becomes_empty(self):
        text = '/* just a comment */\n|=====|'
        result = strip_comments(text)
        lines = [l for l in result.split('\n') if l.strip()]
        assert lines == ['|=====|']

    def test_multiple_comments(self):
        text = '/* A */|=====|/* B */\n|{$x$ /* C */ }|'
        result = strip_comments(text)
        assert 'A' not in result and 'B' not in result and 'C' not in result

    def test_comment_inside_shell_def_parsed_correctly(self):
        from panelmark.parser import Parser
        definition = """
/* main layout */
|=== My App ===|
|{12R $menu$ }| /* menu panel */
|==============|
"""
        model = Parser().parse(definition)
        assert model.root is not None


class TestParseStyled:
    def test_plain_text_no_tags(self):
        assert parse_styled('hello world') == [({}, 'hello world')]

    def test_bold_tag(self):
        segments = parse_styled('<bold>text</bold>')
        attrs, chunk = segments[0]
        assert attrs.get('bold') is True and chunk == 'text'

    def test_close_slash_resets(self):
        segments = parse_styled('<bold>A</>B')
        assert segments[0] == ({'bold': True}, 'A')
        assert segments[1] == ({}, 'B')

    def test_color_attr(self):
        attrs, chunk = parse_styled('<color=red>text</>')[0]
        assert attrs.get('color') == 'red' and chunk == 'text'

    def test_multiple_attrs(self):
        attrs, _ = parse_styled('<color=red;bg=blue;bold>text</>')[0]
        assert attrs.get('color') == 'red'
        assert attrs.get('bg') == 'blue'
        assert attrs.get('bold') is True

    def test_mixed_styled_and_plain(self):
        segments = parse_styled('before <bold>middle</> after')
        assert segments[0] == ({}, 'before ')
        assert segments[1][0].get('bold') is True
        assert segments[2] == ({}, ' after')

    def test_adjacent_styled_spans(self):
        segments = parse_styled('<bold>A</><italic>B</>')
        assert len(segments) == 2
        assert segments[0][0].get('bold') is True
        assert segments[1][0].get('italic') is True

    def test_hyphenated_key(self):
        attrs, _ = parse_styled('<bg-color=green>text</>')[0]
        assert attrs.get('bg-color') == 'green'

    def test_empty_string(self):
        assert parse_styled('') == []

    def test_unclosed_tag_content_still_styled(self):
        segments = parse_styled('<bold>text')
        assert segments[0][0].get('bold') is True and segments[0][1] == 'text'


class TestStyledPlainText:
    def test_plain(self):
        assert styled_plain_text('hello') == 'hello'

    def test_strips_tags(self):
        assert styled_plain_text('<bold>hello</bold>') == 'hello'

    def test_strips_multiple_tags(self):
        assert styled_plain_text('<color=red>A</><bold>B</>C') == 'ABC'

    def test_visual_len(self):
        assert styled_visual_len('<bold>hello</bold>') == 5

    def test_visual_len_plain(self):
        assert styled_visual_len('hello world') == 11
