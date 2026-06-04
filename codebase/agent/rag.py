"""RAG thật — vector search trên tài liệu fitness (ChromaDB + Gemini embeddings).

Đây là implementation của contract §5.3 (`search_fitness_knowledge`). Dùng CHUNG
ChromaDB collection `gym_docs` mà `ingest.py` đã build từ PDF nghiên cứu — không
nạp lại, chỉ đọc.

Thiết kế "degrade an toàn": thiếu GEMINI_API_KEY / chromadb / collection thì trả
None để `tools.py` fallback về KB mock => agent vẫn chạy offline (test, CI).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("agent.rag")

# chroma_db nằm ở gốc repo (cạnh codebase/). Cho phép override bằng env.
_REPO_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = os.getenv("CHROMA_PATH", str(_REPO_ROOT / "chroma_db"))
COLLECTION = os.getenv("RAG_COLLECTION", "gym_docs")
EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "models/gemini-embedding-001")
TOP_K = int(os.getenv("RAG_TOP_K", "4"))

_collection = None
_genai = None
_failed = False


def _init() -> None:
    """Lazy init: cấu hình Gemini + mở collection. Lỗi -> đánh dấu _failed."""
    global _collection, _genai, _failed
    if _collection is not None or _failed:
        return
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        _failed = True
        log.info("RAG offline: thiếu GEMINI_API_KEY → fallback KB mock")
        return
    try:
        import warnings

        warnings.filterwarnings("ignore", category=FutureWarning)
        import chromadb
        import google.generativeai as genai

        genai.configure(api_key=key)
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION)
        _genai = genai
        log.info("RAG sẵn sàng: collection=%s (%d đoạn) path=%s",
                 COLLECTION, _collection.count(), CHROMA_PATH)
    except Exception as e:
        _failed = True
        log.warning("RAG init lỗi (%s) → fallback KB mock", e)


def available() -> bool:
    _init()
    return _collection is not None


def search(query: str, k: int = TOP_K) -> list[dict] | None:
    """[{'text','source'}] theo độ liên quan, hoặc None nếu RAG chưa sẵn sàng."""
    _init()
    if _collection is None:
        return None
    try:
        vec = _genai.embed_content(
            model=EMBED_MODEL, content=query, task_type="retrieval_query"
        )["embedding"]
        res = _collection.query(
            query_embeddings=[vec],
            n_results=k,
            include=["documents", "metadatas"],
        )
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        out = [
            {"text": d, "source": f"trang {m.get('page', '?')}"}
            for d, m in zip(docs, metas)
        ]
        return out or None
    except Exception:
        return None
