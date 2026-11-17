"""El único HTML que genera la UI (chips de fuentes) debe escapar todo dato externo."""

from src.ui.message import meta_html, sources_from_docs


def test_meta_html_escapes_untrusted_values():
    out = meta_html(
        "high", [{"source": "<img src=x onerror=alert(1)>", "page": "1"}], 1500
    )
    assert "<img" not in out
    assert "&lt;img" in out
    assert "Nivel alto" in out and "1.5 s" in out


def test_sources_dedupe_and_order():
    docs = [
        {"metadata": {"source": "GRE 2024", "page_label": "190"}, "score": 0.5},
        {"metadata": {"source": "GRE 2024", "page_label": "190"}, "score": 0.9},
        {"metadata": {"source": "Manual ABC-V", "page_label": "12"}, "score": 0.7},
        {"metadata": {"source": "GRE 2024"}, "score": 1.0},  # sin página → se omite
    ]
    out = sources_from_docs(docs)
    assert [(s["source"], s["page"], s["score"]) for s in out] == [
        ("GRE 2024", "190", 0.9),
        ("Manual ABC-V", "12", 0.7),
    ]
