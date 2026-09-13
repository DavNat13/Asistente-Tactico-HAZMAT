import re


def enhance_markdown(text):
    if not text:
        return ""
    text = _highlight_bold(text)
    text = _highlight_inline_code(text)
    return text


def _highlight_bold(text):
    return re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong class="text-primary">\1</strong>',
        text,
    )


def _highlight_inline_code(text):
    return re.sub(
        r"`([^`]+)`",
        r'<code>\1</code>',
        text,
    )
