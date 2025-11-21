# QuantAlpha - 智能量化研究代理系統

QuantAlpha 是一個先進的 AI 驅動量化研究系統，旨在自動化 Alpha 因子的挖掘、回測和優化。該系統利用多個專門的 AI 代理（研究員、評論員、圖書管理員等）來協作完成從想法生成到策略歸檔的整個流程。

## 主要功能

*   **多代理協作架構**：
    *   **Researcher (研究員)**：提出新的因子想法，支援 DSL 和自訂 Python 程式碼（非線性因子）。
    *   **Critic (評論員)**：評估回測結果，提供詳細的績效分析和改進建議。
    *   **Librarian (圖書管理員)**：管理知識庫（RAG），檢索相關文獻和過去的經驗教訓。
    *   **Backtester (回測員)**：執行嚴格的 Walk-Forward 回測，防止前視偏差。
    *   **Feature Engineer (特徵工程師)**：計算和管理特徵數據。
    *   **Reporter (報告員)**：生成人類可讀的報告和儀表板。

*   **強大的因子引擎**：
    *   支援聲明式 DSL (Domain Specific Language) 定義因子。
    *   支援自訂 Python 程式碼，用於複雜的非線性邏輯（如機器學習模型、條件邏輯）。
    *   內建沙盒環境 (`SandboxExecutor`) 和程式碼驗證器 (`CodeValidator`)，確保自訂程式碼的安全執行。

*   **嚴格的回測系統**：
    *   **Walk-Forward Validation**：滾動視窗驗證，模擬真實交易環境。
    *   **Embargo (清除間隔)**：防止訓練集和測試集之間的數據洩漏。
    *   **全面指標**：Sharpe Ratio, Max Drawdown, IC (Information Coefficient), Turnover 等。

*   **成功因子歸檔**：
    *   自動歸檔符合嚴格標準（如 Sharpe > 1.8）的因子。
    *   保存完整的因子定義、回測結果、權益曲線和代理對話日誌。
    *   提供 `ArchiveViewer` 工具來查看和比較歸檔的因子。

## 安裝與設置

1.  **複製儲存庫**：
    ```bash
    git clone https://github.com/your-repo/QuantAlpha.git
    cd QuantAlpha
    ```

2.  **安裝依賴**：
    建議使用 Python 3.10+。
    ```bash
    pip install -r requirements.txt
    ```
    *注意：如果您使用的是 Python 3.14，請確保 `numba` 等依賴項兼容，或暫時註釋掉。*

3.  **設置環境變數**：
    確保您有必要的 API 金鑰（如 OpenAI, Anthropic 或 Ollama 設置）。

## 使用指南

### 1. 執行完整流程演示
我們提供了一個演示腳本，展示從因子定義到回測和歸檔的完整流程：
```bash
python scripts/run_full_flow.py
```
這將執行一個非線性動量因子的回測，並生成績效圖表 `nonlinear_factor_performance.png`。

### 2. 查看歸檔因子
使用 CLI 工具查看已歸檔的成功因子：
```bash
python scripts/view_archived_factors.py list
python scripts/view_archived_factors.py show <factor_name>
```

### 3. 執行單元測試
驗證系統功能：
```bash
pytest tests/
```

## 專案結構

*   `src/`
    *   `agents/`: AI 代理的實作 (Researcher, Critic, etc.)
    *   `factors/`: 因子計算引擎、DSL 解析器、非線性執行器
    *   `backtest/`: 回測管道、指標計算、投資組合構建
    *   `memory/`: 數據存儲、因子註冊表
    *   `rag/`: RAG (檢索增強生成) 系統
    *   `archive/`: 成功因子歸檔系統
    *   `tools/`: 各種實用工具 (數據獲取、計算等)
*   `scripts/`: 執行腳本和演示
*   `tests/`: 單元測試和整合測試
*   `configs/`: 設定檔 (交易成本、約束條件等)

## 開發狀態

目前已完成以下階段：
*   ✅ **Phase 1**: 核心組件與工具
*   ✅ **Phase 2**: 回測引擎
*   ✅ **Phase 4**: 端到端管道驗證
*   ✅ **Phase 5**: 非線性 Alpha 因子基礎設施
*   ✅ **Phase 6**: 成功因子歸檔系統
*   ⚠️ **Phase 3**: 代理整合 (部分完成，受限於依賴項)

## 貢獻

歡迎提交 Pull Requests 或 Issues 來改進 QuantAlpha！
