from datetime import datetime, timedelta
from pathlib import Path

from nanobot.session.manager import Session, SessionManager


def _patch_home(monkeypatch, home: Path) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))


def test_session_add_message_get_history_and_clear() -> None:
    session = Session(key="cli:123")
    session.add_message("user", "hello", tool_call="ls")
    session.add_message("assistant", "hi")

    assert len(session.messages) == 2
    assert session.messages[0]["tool_call"] == "ls"
    assert session.get_history() == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assert session.get_history(max_messages=1) == [{"role": "assistant", "content": "hi"}]

    session.clear()
    assert session.messages == []


def test_get_or_create_caches_and_loads_saved_session(tmp_path: Path, monkeypatch) -> None:
    _patch_home(monkeypatch, tmp_path)
    manager = SessionManager(workspace=tmp_path)

    key = "email:chat-1"
    session = manager.get_or_create(key)
    session.add_message("user", "persist me")
    session.metadata = {"ticket": 42}
    manager.save(session)

    manager2 = SessionManager(workspace=tmp_path)
    loaded = manager2.get_or_create(key)

    assert loaded.key == key
    assert loaded.metadata == {"ticket": 42}
    assert loaded.get_history() == [{"role": "user", "content": "persist me"}]
    assert manager2.get_or_create(key) is loaded


def test_get_session_path_sanitizes_key(tmp_path: Path, monkeypatch) -> None:
    _patch_home(monkeypatch, tmp_path)
    manager = SessionManager(workspace=tmp_path)

    path = manager._get_session_path('email:abc<>:"/\\|?*')
    assert path.name == "email_abc_________.jsonl"


def test_load_returns_none_for_invalid_jsonl(tmp_path: Path, monkeypatch) -> None:
    _patch_home(monkeypatch, tmp_path)
    manager = SessionManager(workspace=tmp_path)

    path = manager._get_session_path("broken:1")
    path.write_text("{not-json}\n", encoding="utf-8")

    assert manager._load("broken:1") is None


def test_delete_removes_cache_and_file(tmp_path: Path, monkeypatch) -> None:
    _patch_home(monkeypatch, tmp_path)
    manager = SessionManager(workspace=tmp_path)

    key = "slack:42"
    session = manager.get_or_create(key)
    session.add_message("user", "x")
    manager.save(session)

    assert key in manager._cache
    assert manager.delete(key) is True
    assert key not in manager._cache
    assert manager.delete(key) is False


def test_list_sessions_reads_metadata_and_sorts_desc(tmp_path: Path, monkeypatch) -> None:
    _patch_home(monkeypatch, tmp_path)
    manager = SessionManager(workspace=tmp_path)

    old = Session(
        key="discord:old",
        created_at=datetime.now() - timedelta(days=2),
        updated_at=datetime.now() - timedelta(days=1),
    )
    old.add_message("user", "older")
    manager.save(old)

    new = Session(
        key="discord:new",
        created_at=datetime.now() - timedelta(hours=2),
        updated_at=datetime.now() - timedelta(hours=1),
    )
    new.add_message("user", "newer")
    manager.save(new)

    # Corrupt file should be skipped.
    (manager.sessions_dir / "bad.jsonl").write_text("not-json\n", encoding="utf-8")

    listed = manager.list_sessions()
    keys = [item["key"] for item in listed]

    assert "discord:new" in keys
    assert "discord:old" in keys
    assert "bad" not in keys
    assert keys.index("discord:new") < keys.index("discord:old")
