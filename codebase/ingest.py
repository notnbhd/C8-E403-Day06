"""
ingest.py - Parse PDF → Chunk → Embed → Lưu ChromaDB
Chỉ chạy một lần (hoặc khi có tài liệu mới)
"""

import os
import sys
import warnings
import fitz  # PyMuPDF
import chromadb

# Dùng google-generativeai cho embedding (đã test OK)
# Suppress deprecation warning vì chỉ dùng embed_content, không dùng các feature đã remove
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
import google.generativeai as genai_embed

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Chưa set GEMINI_API_KEY trong file .env")
    sys.exit(1)

genai_embed.configure(api_key=GEMINI_API_KEY)

PDF_PATH    = "tài liệu nghiên cứu tập gym.pdf"
CHROMA_PATH = "./chroma_db"
COLLECTION  = "gym_docs"
CHUNK_SIZE  = 600   # ký tự
OVERLAP     = 120   # ký tự (~20%)
BATCH_SIZE  = 50    # số chunks mỗi lần gọi embedding API


# ── 1. Parse PDF ──────────────────────────────────────────────────────────────
def parse_pdf(path: str) -> list[dict]:
    print(f"📄 Đọc file: {path}")
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({"text": text, "page": i})
    print(f"   ✅ {len(pages)} trang có nội dung")
    return pages


# ── 2. Chunking (sliding window) ──────────────────────────────────────────────
def chunk_pages(pages: list[dict]) -> list[dict]:
    print("✂️  Chia chunks...")
    chunks, idx = [], 0
    for p in pages:
        text, page_num = p["text"], p["page"]
        start = 0
        while start < len(text):
            piece = text[start:start + CHUNK_SIZE].strip()
            if len(piece) >= 50:
                chunks.append({
                    "id":    f"chunk_{idx}_page_{page_num}",
                    "text":  piece,
                    "page":  page_num,
                })
                idx += 1
            start += CHUNK_SIZE - OVERLAP
    print(f"   ✅ {len(chunks)} chunks")
    return chunks


# ── 3. Embed (batch) ──────────────────────────────────────────────────────────
def embed_batch(texts: list[str]) -> list[list[float]]:
    all_vecs = []
    n = len(texts)
    for i in range(0, n, BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        print(f"   🔄 Batch {i // BATCH_SIZE + 1}/{-(-n // BATCH_SIZE)} ({len(batch)} chunks)...")
        res = genai_embed.embed_content(
            model="models/gemini-embedding-001",
            content=batch,
            task_type="retrieval_document",
        )
        all_vecs.extend(res["embedding"])
    return all_vecs


# ── 4. Lưu ChromaDB ───────────────────────────────────────────────────────────
def save_chroma(chunks: list[dict], embeddings: list[list[float]]):
    print("💾 Lưu vào ChromaDB...")
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        chroma.delete_collection(COLLECTION)
        print("   🗑️  Xóa collection cũ")
    except Exception:
        pass

    col = chroma.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    col.add(
        ids        = [c["id"]   for c in chunks],
        embeddings = embeddings,
        documents  = [c["text"] for c in chunks],
        metadatas  = [{"page": c["page"]} for c in chunks],
    )
    print(f"   ✅ Đã lưu {len(chunks)} chunks")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  INGEST PIPELINE — RAG Gym Chatbot")
    print("=" * 55)

    if not os.path.exists(PDF_PATH):
        print(f"❌ Không tìm thấy: {PDF_PATH}")
        sys.exit(1)

    pages      = parse_pdf(PDF_PATH)
    chunks     = chunk_pages(pages)
    print("\n🧠 Tạo embeddings (Gemini gemini-embedding-001)...")
    embeddings = embed_batch([c["text"] for c in chunks])
    save_chroma(chunks, embeddings)

    print("\n" + "=" * 55)
    print("  ✅ XONG! Chạy tiếp: python3 app.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
