# CLAUDE.md

## Non-Obvious Architecture Notes

- **Two migration systems:** legacy Peewee (`internal/migrations/`) runs first, then Alembic (`migrations/versions/`). `alembic.ini` at `backend/open_webui/alembic.ini` with `prepend_sys_path = ..`.
- **Config:** env vars in `env.py` (static, loaded at import); dynamic config in `config.py` (DB-backed, Redis-cached).
- Python 3.11–3.12. Node 18.13–22.x.

## Fork Customizations

All items below are our changes vs upstream. Preserve them when merging/rebasing.

---

### [1] Builtin tools — notes (`backend/open_webui/tools/builtin.py`)

`replace_note_content` заменён двумя инструментами:
- `append_to_note(note_id, content)` — дописывает в конец
- `find_and_replace(note_id, old, new)` — заменяет первое вхождение

---

### [2] Knowledge / RAG в middleware (`backend/open_webui/utils/middleware.py`)

1. Knowledge tools добавляются в модель **всегда** (upstream — только если нет attached knowledge).
2. Attached knowledge **всегда** попадает в контекст как RAG (upstream — только если `function_calling != "native"`).

---

### [3] Tool calling

`tool_choice` по умолчанию `"auto"` (upstream — `"required"`).

---

### [4] note_id и file_id в RAG-контексте (`backend/open_webui/utils/middleware.py`)

`apply_source_context_to_messages` добавляет атрибуты в `<source>`:
- `note_id="<uuid>"` — для заметок
- `file_id="<uuid>"` — для файлов из knowledge bases

Без этого модель видит содержимое, но не знает ID для вызова инструментов.
**Location:** `context_string` building loop (~line 819).

---

### [5] Chat Controls имеют приоритет над Advanced Params агента (`backend/open_webui/utils/payload.py`)

`apply_model_params_to_body` не перезаписывает ключи, уже присутствующие в `form_data`:
```python
if value is not None and key not in form_data:  # было: if value is not None
```

Advanced Params агента — дефолты; Chat Controls их переопределяют.
**Location:** `apply_model_params_to_body` (~line 53).

---

### [6] `#URL` attach: полный контекст без лишнего embedding

Исправлен сценарий прикрепления URL через `#` в чате:

1. Для web-attach из UI используется `process=false`, чтобы не запускать индексацию/embedding при простом вложении страницы в текущий диалог.
2. `POST /process/web` при `process=false` теперь возвращает нормализованный `file`-payload (`file.data.content` + `file.meta`), а не только сырой `content`.
3. В `get_sources_from_items` для `type="text"` приоритет отдан уже имеющемуся контенту (`file.data.content` / `content`) перед `collection_name`, чтобы контент страницы гарантированно попадал в prompt как full-context.

Эффект: модель получает содержимое сайта в контексте, а embedding-модель не вызывается без необходимости.

**Locations:**
- `src/lib/components/chat/Chat.svelte` (`uploadWeb`)
- `backend/open_webui/routers/retrieval.py` (`/process/web`, ветка `process=false`)
- `backend/open_webui/retrieval/utils.py` (`get_sources_from_items`, `type=="text"`)

---

## Docker Build & Run

```bash
# Build (from /home/gedomada/open-webui)
docker build --network=host -t open-webui-custom .

# Run
docker run -d -e HF_HUB_OFFLINE=1 --network host --name open-webui -v open-webui:/app/backend/data open-webui-custom
```
