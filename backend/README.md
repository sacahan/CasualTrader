# CasualTrader Backend

## 技術棧

- Python 3.12+
- FastAPI 0.115+
- SQLAlchemy 2.0+ (Async)
- OpenAI Agent SDK
- UV 包管理器

## 開發

```bash
cd backend
uv sync
uv run uvicorn src.api.app:create_app --factory --reload
```

## 測試

```bash
cd backend
uv run pytest tests/ -v
```

詳見 `docs/API_IMPLEMENTATION.md` 和 `docs/AGENTS_ARCHITECTURE.md`
