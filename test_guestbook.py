"""방명록의 주요 사용자 흐름을 임시 데이터베이스로 확인한다."""

from fastapi.testclient import TestClient

import main


def test_create_edit_delete_and_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.db")
    main.init_db()
    client = TestClient(main.app)

    created = client.post("/entries", data={"name": "민지", "message": "<script>alert(1)</script>", "password": "pass1234"}, follow_redirects=True)
    assert created.status_code == 200
    assert "&lt;script&gt;" in created.text
    assert "<script>" not in created.text
    assert "민지" in client.get("/?q=민지").text

    denied = client.post("/entries/1/edit", data={"name": "민지", "message": "고친 글", "password": "wrong"})
    assert denied.status_code == 403
    assert "고친 글" not in client.get("/").text

    changed = client.post("/entries/1/edit", data={"name": "민지", "message": "고친 글", "password": "pass1234"}, follow_redirects=True)
    assert changed.status_code == 200
    assert "고친 글" in changed.text

    deleted = client.post("/entries/1/delete", data={"password": "pass1234"}, follow_redirects=True)
    assert deleted.status_code == 200
    assert "고친 글" not in deleted.text
