"""
Styled text parsing utilities for panelmark.

Style tags use a simple XML-like format:
    <attr1[=val1][;attr2[=val2]...]>text</>

Opening tag examples:
    <bold>text</bold>
    <color=red>text</>
    <color=red;bg=blue;bold;underline>text</>

Closing tag: </> or </anything> (the tag name is ignored; all styles reset).

This module handles parsing only.  Terminal rendering (converting attrs to
escape sequences) lives in panelmark_tui.style.
"""

import re

# Matches any <...> tag (content must not contain < or >).
_TAG_RE = re.compile(r'<([^<>]*)>')


# ── tag parsing ─────────────────────────────────────────────────────────────

def _is_close_tag(content: str) -> bool:
    return content.strip().startswith('/')


def _parse_attrs(attr_str: str) -> dict:
    """Parse 'attr1=val1;attr2;attr3=val3' into a dict."""
    attrs: dict = {}
    for part in attr_str.split(';'):
        part = part.strip()
        if not part:
            continue
        if '=' in part:
            k, _, v = part.partition('=')
            attrs[k.strip().lower()] = v.strip().lower()
        else:
            attrs[part.strip().lower()] = True
    return attrs


def parse_styled(text: str) -> list:
    """
    Parse *text* containing style tags into a list of ``(attrs, chunk)`` pairs.

    *attrs* is a ``dict`` (possibly empty — means unstyled).
    *chunk* is a plain-text string with no tags.

    Example::

        parse_styled('<bold>hello</> world')
        # → [({'bold': True}, 'hello'), ({}, ' world')]
    """
    segments: list = []
    current_attrs: dict = {}
    last_end = 0

    for match in _TAG_RE.finditer(text):
        chunk = text[last_end:match.start()]
        if chunk:
            segments.append((dict(current_attrs), chunk))
        last_end = match.end()

        content = match.group(1)
        if _is_close_tag(content):
            current_attrs = {}
        else:
            current_attrs = _parse_attrs(content)

    tail = text[last_end:]
    if tail:
        segments.append((dict(current_attrs), tail))

    return segments


# ── plain-text helpers ──────────────────────────────────────────────────────

def styled_plain_text(text: str) -> str:
    """Return *text* with all style tags stripped."""
    return _TAG_RE.sub('', text)


def styled_visual_len(text: str) -> int:
    """Return the visible character length of *text* (ignoring style tags)."""
    return len(styled_plain_text(text))


# ── C-style comment stripping ───────────────────────────────────────────────

_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)


def strip_comments(text: str) -> str:
    """
    Remove ``/* … */`` comments from a shell definition string.

    Newlines inside a comment are preserved so that the line structure of
    the definition is not disrupted.
    """
    def _replacer(m: re.Match) -> str:
        return '\n' * m.group().count('\n')

    return _COMMENT_RE.sub(_replacer, text)
