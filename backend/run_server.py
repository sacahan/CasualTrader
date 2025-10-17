#!/usr/bin/env python3
"""
啟動 CasualTrader API Server

設置正確的 Python 路徑並啟動 FastAPI 應用
"""

import os
import sys
import warnings
from pathlib import Path

# 抑制 multiprocessing resource_tracker 警告（在強制關閉時出現）
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning:multiprocessing.resource_tracker"
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")

# 將 src 加入 Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 現在可以導入並啟動應用
if __name__ == "__main__":
    import uvicorn

    # 使用 import string 格式以支援熱重載
    uvicorn.run(
        "api.server:app",  # 使用字符串格式而非直接導入
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,  # 啟用熱重載
    )
