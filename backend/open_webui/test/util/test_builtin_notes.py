import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from open_webui.tools import builtin


@pytest.mark.asyncio
async def test_append_to_note_adds_separator_newline(monkeypatch):
    note = SimpleNamespace(
        id="note-1",
        user_id="user-1",
        data={"content": {"md": "Existing line"}},
    )
    captured = {}

    def fake_update_note_by_id(note_id, form):
        captured["note_id"] = note_id
        captured["content"] = form.data["content"]["md"]
        return SimpleNamespace(id=note_id)

    monkeypatch.setattr(builtin.Notes, "get_note_by_id", lambda note_id: note)
    monkeypatch.setattr(
        builtin.Groups, "get_groups_by_member_id", lambda user_id: []
    )
    monkeypatch.setattr(builtin.Notes, "update_note_by_id", fake_update_note_by_id)

    result = await builtin.append_to_note(
        "note-1",
        "Appended line",
        __request__=Mock(),
        __user__={"id": "user-1"},
    )

    assert json.loads(result) == {"status": "success"}
    assert captured["note_id"] == "note-1"
    assert captured["content"] == "Existing line\nAppended line"
