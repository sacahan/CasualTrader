#!/usr/bin/env python3
"""
啟動 CasualTrader API Server

設置正確的 Python 路徑並啟動 FastAPI 應用
"""

import sys
from pathlib import Path

# 將 src 加入 Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 現在可以導入並啟動應用
if __name__ == "__main__":
    from api.server import main

    main()
