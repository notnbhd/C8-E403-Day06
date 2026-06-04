"""
app.py - FastAPI backend cho RAG Chatbot
Pipeline: embed query → ChromaDB search → Gemini generate
"""

import os
import warnings
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Dùng google-generativeai (cũ nhưng stable) cho cả embed + generate
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("❌ Chưa set GEMINI_API_KEY trong file .env")

CUSTOM_LLM_KEY = os.getenv("CUSTOM_LLM_KEY")
CUSTOM_LLM_URL = os.getenv("CUSTOM_LLM_URL")
CUSTOM_LLM_MODEL = os.getenv("CUSTOM_LLM_MODEL", "mistral-small-latest")

if not CUSTOM_LLM_KEY:
    raise RuntimeError("❌ Chưa set CUSTOM_LLM_KEY trong file .env")

genai.configure(api_key=GEMINI_API_KEY)

# Khởi tạo OpenAI client cho LLM custom
llm_client = openai.AsyncOpenAI(
    api_key=CUSTOM_LLM_KEY,
    base_url=CUSTOM_LLM_URL,
)

CHROMA_PATH = "./chroma_db"
COLLECTION  = "gym_docs"
TOP_K       = 5
MAX_HISTORY = 6  # số lượt chat giữ lại

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên về thể thao và tập gym, dựa trên tài liệu nghiên cứu khoa học.

Quy tắc:
1. Chỉ trả lời dựa trên TÀI LIỆU THAM KHẢO được cung cấp
2. Nếu tài liệu không có thông tin, nói rõ: "Tài liệu không đề cập đến điều này"
3. Trả lời bằng tiếng Việt, ngắn gọn và thực tế
4. Giọng điệu như một HLV thể hình thân thiện, chuyên nghiệp"""


# ── State ─────────────────────────────────────────────────────────────────────
_collection = None
_gen_model = None


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _collection, _gen_model
    try:
        chroma = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = chroma.get_collection(COLLECTION)
        print(f"✅ ChromaDB: {_collection.count()} chunks sẵn sàng")
    except Exception as e:
        print(f"⚠️  ChromaDB chưa sẵn sàng ({e}). Chạy 'python ingest.py' trước!")

    print(f"✅ Custom LLM ({CUSTOM_LLM_MODEL}) sẵn sàng")
    yield


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gym RAG Chatbot",
    description="Hỏi đáp tài liệu tập gym với Gemini + ChromaDB",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Schemas ───────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str       # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[Message] = []

class SourceItem(BaseModel):
    page: int | str
    excerpt: str
    similarity: float

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


# ── RAG Helpers ───────────────────────────────────────────────────────────────
def embed_query(text: str) -> list[float]:
    res = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
    )
    return res["embedding"]


def retrieve(question: str) -> tuple[list[str], list[SourceItem]]:
    """Semantic search → trả về (context_texts, sources)"""
    if _collection is None:
        raise RuntimeError("ChromaDB chưa được khởi tạo")

    vec = embed_query(question)
    results = _collection.query(
        query_embeddings=[vec],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    docs   = results["documents"][0]
    metas  = results["metadatas"][0]
    dists  = results["distances"][0]

    sources = [
        SourceItem(
            page       = m.get("page", "?"),
            excerpt    = d[:250] + "..." if len(d) > 250 else d,
            similarity = round((1 - dist) * 100, 1),
        )
        for d, m, dist in zip(docs, metas, dists)
    ]
    return docs, sources


def build_prompt(question: str, context_texts: list[str], history: list[Message]) -> str:
    context = "\n\n".join(
        f"[Đoạn {i+1}]\n{t}" for i, t in enumerate(context_texts)
    )
    recent = history[-(MAX_HISTORY * 2):]
    hist_str = "\n".join(
        f"{'Người dùng' if m.role == 'user' else 'Trợ lý'}: {m.content}"
        for m in recent
    )

    return f"""TÀI LIỆU THAM KHẢO:
{context}

LỊCH SỬ HỘI THOẠI:
{hist_str if hist_str else "(Câu hỏi đầu tiên)"}

CÂU HỎI: {question}

Hãy trả lời dựa trên tài liệu tham khảo."""


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "db_ready": _collection is not None,
        "chunk_count": _collection.count() if _collection else 0,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Câu hỏi không được để trống")
    if _collection is None:
        raise HTTPException(503, "DB chưa sẵn sàng. Chạy 'python ingest.py' trước!")

    try:
        context_texts, sources = retrieve(req.question)
        prompt = build_prompt(req.question, context_texts, req.history)
        
        # Gọi custom LLM
        response = await llm_client.chat.completions.create(
            model=CUSTOM_LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(500, f"Lỗi: {str(e)}")


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
