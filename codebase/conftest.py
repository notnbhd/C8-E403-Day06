"""Đặt thư mục codebase/ lên sys.path để `import agent` chạy được khi
gọi pytest từ gốc repo. (pytest tự nạp conftest.py gần nhất.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Test phải OFFLINE & deterministic (xem agent/README.md): vô hiệu hoá mọi LLM/RAG
# key — kể cả khi .env có CUSTOM_LLM_KEY/GEMINI_API_KEY. Đặt "" trước khi import
# agent.config (load_dotenv override=False sẽ không ghi đè giá trị đã có).
for _k in ("OPENROUTER_API_KEY", "CUSTOM_LLM_KEY", "GEMINI_API_KEY"):
    os.environ[_k] = ""

# Buộc tool dùng MOCK data (không chạm Supabase) để test deterministic + offline,
# kể cả khi .env bật AGENT_USE_MOCK_TOOLS=0 cho app thật.
os.environ["AGENT_USE_MOCK_TOOLS"] = "1"
