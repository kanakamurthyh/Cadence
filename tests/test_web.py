"""The coach web app's API (no audio analysis: that is covered by the pipeline tests)."""
import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from cadence import web  # noqa: E402

client = TestClient(web.app)


def test_index_and_assets_served():
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/app.css").status_code == 200


def test_texts_only_analyzable_speeches_first():
    rows = client.get("/api/texts").json()
    ids = [r["id"] for r in rows]
    assert "T5" not in ids  # no envelope yet
    groups = [r["group"] for r in rows]
    assert groups == sorted(groups, key=lambda g: g != "speech")
    assert all(r["display"] and r["typical_s"] > 0 for r in rows)


def test_unknown_text_and_missing_clip_are_errors():
    r = client.post("/api/analyze", files={"file": ("a.wav", b"RIFF", "audio/wav")}, data={"text_id": "T99"})
    assert r.status_code == 404
    assert client.get("/api/clip/nope/0/you").status_code == 404


def test_figures_cannot_escape_the_folder():
    assert client.get("/figures/..%2Fpyproject.toml").status_code == 404
