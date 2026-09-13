import html
import re


def format_response(text):
    if not text:
        return ""
    text = _render_tables(text)
    text = _render_warnings(text)
    text = _render_lists(text)
    text = _render_page_refs(text)
    text = _render_shortcodes(text)
    return text


def _render_tables(text):
    pattern = r"(\|.+\|)\n(\|[-:| ]+\|)\n((?:\|.+\|\n?)+)"
    def replace_table(m):
        header_row = m.group(1)
        rows = m.group(3).strip().split("\n")
        headers = [c.strip() for c in header_row.split("|")[1:-1]]
        th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
        body = ""
        for row in rows:
            cells = [c.strip() for c in row.split("|")[1:-1]]
            body += "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>"
        return (
            '<table class="hazmat-table">'
            f"<thead><tr>{th}</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        )
    return re.sub(pattern, replace_table, text)


def _render_warnings(text):
    if text.startswith("ADVERTENCIA"):
        text = text.replace("ADVERTENCIA:", "", 1).strip()
        return (
            '<div class="hazmat-toast error" '
            'style="position:relative;margin-bottom:1rem;">'
            '<span class="text-emergency font-semibold">'
            ":material/warning: ADVERTENCIA</span>"
            f"<p>{html.escape(text)}</p></div>"
        )
    return text


def _render_lists(text):
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{html.escape(stripped[2:])}</li>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(line)
    if in_list:
        result.append("</ul>")
    return "\n".join(result)


def _render_page_refs(text):
    pattern = r"\[P(?:ágina|agina):\s*(\d+)\]"
    return re.sub(
        pattern,
        r'<span class="hazmat-badge">Pág. \1</span>',
        text,
    )


def _render_shortcodes(text):
    replacements = {
        ":danger:": '<span class="hazmat-badge hazard">'
                    ":material/warning: PELIGRO</span>",
        ":caution:": '<span class="hazmat-badge warning">'
                     ":material/info: PRECAUCION</span>",
        ":safe:": '<span class="hazmat-badge success">'
                  ":material/check_circle: SEGURO</span>",
    }
    for code, html in replacements.items():
        text = text.replace(code, html)
    return text
