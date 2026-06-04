"""Đặt thư mục codebase/ lên sys.path để `import agent` chạy được khi
gọi pytest từ gốc repo. (pytest tự nạp conftest.py gần nhất.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
