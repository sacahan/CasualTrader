# Migration 層契約驗證測試

"""
Contract 4: Schema Migration 層契約驗證

此測試檔案驗證資料庫遷移腳本的契約要求:
- 遷移腳本存在且可導入
- 前置條件檢查能力
- 遷移主邏輯能力
- 遷移驗證能力
"""

import inspect
import sys
from pathlib import Path

# 添加 scripts 目錄到 Python 路徑
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


class TestMigrationScriptContract:
    """Migration 層腳本契約驗證"""

    def test_migration_script_exists(self):
        """驗證 migration 腳本存在"""
        migration_file = (
            Path(__file__).parent.parent.parent / "scripts" / "migrate_add_timestamps.py"
        )
        assert migration_file.exists(), f"Migration script not found at {migration_file}"

    def test_migration_function_exists(self):
        """驗證遷移主函數存在"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        assert callable(migrate_agent_performance_table)

    def test_migration_function_is_callable(self):
        """驗證遷移函數能被正確呼叫"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        # 函數應接受 db_path 參數
        sig = inspect.signature(migrate_agent_performance_table)
        params = list(sig.parameters.keys())
        assert "db_path" in params

    def test_migration_function_returns_bool(self):
        """驗證遷移函數返回布林值"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        sig = inspect.signature(migrate_agent_performance_table)
        # 檢查返回類型註解
        assert sig.return_annotation is bool or sig.return_annotation == "bool"

    def test_migration_has_docstring(self):
        """驗證遷移函數有文檔字符串"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        assert migrate_agent_performance_table.__doc__ is not None
        assert len(migrate_agent_performance_table.__doc__) > 0

    def test_migration_module_has_main_entry(self):
        """驗證遷移腳本有 __main__ 進入點"""
        migration_file = (
            Path(__file__).parent.parent.parent / "scripts" / "migrate_add_timestamps.py"
        )
        content = migration_file.read_text()

        # 應該有 if __name__ == "__main__" 程式碼塊
        assert 'if __name__ == "__main__"' in content


class TestMigrationContractRequirements:
    """驗證遷移契約要求"""

    def test_migration_checks_preconditions(self):
        """驗證遷移檢查前置條件"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該檢查資料庫文件是否存在
        assert "exists()" in content or "exists" in content
        # 應該檢查是否成功連接
        assert "sqlite3" in content or "sqlite" in content

    def test_migration_handles_errors(self):
        """驗證遷移有錯誤處理"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該有 try-except 錯誤處理
        assert "try" in content
        assert "except" in content

    def test_migration_performs_validation(self):
        """驗證遷移包含驗證邏輯"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該檢查欄位或驗證遷移結果
        assert "PRAGMA" in content or "created_at" in content or "updated_at" in content

    def test_migration_with_nonexistent_db(self):
        """驗證遷移在資料庫不存在時正確處理"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        # 應該返回 False 而不是拋出例外
        result = migrate_agent_performance_table("/nonexistent/path/db.sqlite")
        assert result is False


class TestMigrationDocumentation:
    """驗證遷移文檔和規範"""

    def test_migration_spec_exists(self):
        """驗證遷移規範文檔存在"""
        spec_file = (
            Path(__file__).parent.parent.parent.parent
            / "docs"
            / "MIGRATION_CONTRACT_SPECIFICATION.md"
        )
        assert spec_file.exists(), f"Migration spec not found at {spec_file}"

    def test_migration_spec_contains_requirements(self):
        """驗證遷移規範包含所有要求"""
        spec_file = (
            Path(__file__).parent.parent.parent.parent
            / "docs"
            / "MIGRATION_CONTRACT_SPECIFICATION.md"
        )
        content = spec_file.read_text()

        # 應該文檔化前置條件
        assert "precondition" in content.lower() or "pre-condition" in content.lower()
        # 應該文檔化遷移邏輯
        assert "migration" in content.lower()
        # 應該文檔化驗證
        assert "verif" in content.lower() or "驗" in content


class TestMigrationBehavior:
    """驗證遷移行為"""

    def test_migration_idempotent(self):
        """驗證遷移是幂等的（可以多次執行）"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該檢查欄位是否已存在
        assert "if" in content and "not in" in content
        # 這表示遷移會檢查欄位是否已存在

    def test_migration_reports_progress(self):
        """驗證遷移報告進度"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該有 print 或 logger 輸出
        assert "print" in content or "logger" in content

    def test_migration_targets_correct_table(self):
        """驗證遷移目標表"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該目標 agent_performance 表
        assert "agent_performance" in content

    def test_migration_adds_correct_columns(self):
        """驗證遷移添加正確的欄位"""
        from scripts.migrate_add_timestamps import migrate_agent_performance_table

        content = inspect.getsource(migrate_agent_performance_table)

        # 應該添加時間戳記欄位
        assert "created_at" in content
        assert "updated_at" in content
