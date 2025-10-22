"""
Pytest 配置文件 - 設置導入路徑
"""

import sys
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
