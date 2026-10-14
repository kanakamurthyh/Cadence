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


def test_ghost_pause_cues_are_inside_the_passage():
    for r in client.get("/api/texts").json():
        g, n = r["ghost"], len(r["ghost"]["median"])
        assert g["pause_after"] == sorted(set(g["pause_after"]))
        assert all(0 <= i < n - 1 for i in g["pause_after"])
        assert g["pause_after"], r["id"]  # every good reading has some phrase breaks


def test_listen_first_model_reading():
    rows = client.get("/api/texts").json()
    for r in rows:
        m = r["model"]
        assert m["reader"] and len(m["starts"]) == len(r["ghost"]["median"])
        assert m["starts"] == sorted(m["starts"])
    r = client.get(f"/api/model/{rows[0]['id']}")
    assert r.status_code == 200 and r.content[:4] == b"RIFF"
    assert client.get("/api/model/T99").status_code == 404


def test_unknown_text_and_missing_clip_are_errors():
    r = client.post("/api/analyze", files={"file": ("a.wav", b"RIFF", "audio/wav")}, data={"text_id": "T99"})
    assert r.status_code == 404
    assert client.get("/api/clip/nope/0/you").status_code == 404


def test_figures_cannot_escape_the_folder():
    assert client.get("/figures/..%2Fpyproject.toml").status_code == 404
