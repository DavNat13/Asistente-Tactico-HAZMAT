"""Reglas de alertas, regresiones, reporte semanal y correo (SMTP simulado)."""

from src.automation.health import eval_regressions, health_alerts, weekly_rows
from src.notify import mailer
from src.notify.templates import layout, table


def _run(status="ok", latency=2000, blocked=False, **kw):
    return {"status": status, "latency_ms": latency, "blocked": blocked, **kw}


def test_health_alerts_thresholds():
    assert health_alerts([]) == []
    assert health_alerts([_run() for _ in range(10)]) == []
    slow = [_run(latency=40000) for _ in range(5)]
    assert [a[0] for a in health_alerts(slow)] == ["latency"]
    errors = [_run(status="error") for _ in range(2)] + [_run() for _ in range(3)]
    assert "errors" in [a[0] for a in health_alerts(errors)]
    attacks = [_run(blocked=True, status="blocked") for _ in range(4)] + [
        _run() for _ in range(4)
    ]
    assert "security" in [a[0] for a in health_alerts(attacks)]


def test_eval_regressions():
    prev = {"keyword_score": 1.0, "citation_ok": 1.0, "error_rate": 0}
    assert eval_regressions(prev, prev) == []
    bad = {"keyword_score": 0.8, "citation_ok": 0.85, "error_rate": 0.2}
    assert len(eval_regressions(bad, prev)) == 3


def test_weekly_rows_counts_materials():
    runs = [
        _run(un_numbers=["1203"], user="a", feedback=1, grounded=1.0),
        _run(un_numbers=["1203", "1017"], user="b", feedback=-1, grounded=0.5),
    ]
    rows = dict(weekly_rows(runs))
    assert rows["Consultas"] == "2" and rows["Usuarios activos"] == "2"
    assert rows["Materiales más consultados"].startswith("UN 1203 (2)")
    assert rows["Feedback positivo"] == "50% de 2"


def test_templates_escape_values():
    html = layout("<b>t</b>", table([("<script>", "x")]))
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_mailer_noop_without_config(monkeypatch):
    logged = []
    monkeypatch.setattr(mailer, "features", type("F", (), {"mail_enabled": False})())
    monkeypatch.setattr(mailer, "_log", lambda *a, **k: logged.append(a))
    assert mailer.send(["a@b.cl"], "s", "<p>h</p>", "t", kind="test") is False
    assert logged and logged[0][3] == "smtp_no_configurado"


def test_mailer_sends_with_attachment(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, context=None, timeout=None):
            sent["host"] = host

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, pwd):
            sent["login"] = user

        def send_message(self, msg):
            sent["msg"] = msg

    cfg = type(
        "F",
        (),
        {
            "mail_enabled": True,
            "SMTP_HOST": "smtp.test",
            "SMTP_PORT": 465,
            "SMTP_USER": "bot@test.cl",
            "SMTP_PASSWORD": "x",
            "MAIL_FROM": "bot@test.cl",
        },
    )()
    monkeypatch.setattr(mailer, "features", cfg)
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(mailer, "_log", lambda *a, **k: None)
    ok = mailer.send(
        ["a@b.cl"],
        "Asunto",
        "<p>h</p>",
        "t",
        kind="incident",
        attachments=[("ficha.pdf", b"%PDF-1.4", "application/pdf")],
    )
    assert ok and sent["host"] == "smtp.test" and sent["login"] == "bot@test.cl"
    parts = [p.get_filename() for p in sent["msg"].iter_attachments()]
    assert parts == ["ficha.pdf"]
