已為您更新 `MEMORY.md`。我已將 `green-market-reporter` 的開發進度更新至「核心引擎邏輯驗證完成」，並新增了關於「自動化測試 (QA Engineer) 角色定義」與「防禦性開發策略」的知識紀錄。

```markdown
# MEMORY.md

## 使用者偏好
- **角色定位**：將 AI 視為「課堂練習助手（法鬥超人）」，偏好透過實際練習、撰寫程式碼、執行測試來學習。
- **學習風格**：偏好結構化、務實且可驗證的學習流程（例如：撰寫程式 $\rightarrow$ 建立測試腳本 $\to$ 執行驗證）。
- **互動需求**：偏好看到程式碼的邏輯說明、測試報告摘要以及後續進階功能的建議。
- **擴充意向**：對「擴算 AI 能力（建立新 Skill）」有濃厚興趣，偏好透過定義 SOP 的方式來教導 AI。

## 專案狀態
- **Python 簡易計算機專向**：
    - **核心功能**：已完成加、減、模、除基本運算，具備錯誤處理。
    - **驗證成果**：已透過 `test_calculator.py` 自動化測試，並成功透過模擬輸入流驗證執行流程。
    - **目前檔案**：`calculator.py` (邏輯), `test_calculator.py` (測試), `run_manual_test.py` (模擬輸入測試)。
- **Skill 開發進度**：
    - **目標**：遵循 `skill-開發者 SOP`，將新技能封裝為獨立的模組化專案。
    - **當前專案**：`skills/green-market-reporter` (綠生活循環市集報告自動化生成器)。
    - **開發階段**：**核心引擎開發階段 (Implementation Phase - Logic Verification)**。
    - **已完成工作**：
        - **Phase 1 - 定義與規範 (Definition)**：已建立 `SKILL.md` (定義 I/O 與 7 項 QA 標準)。
        - **Phase 2 - 環境與架構 (Scaffolding)**：已建立 `requirements.txt` 與 `models.py` (含驗證邏輯)。
        - **Phase 3 - 核心引擎開發 (Implementation - In Progress)**：
            - **核心架構建立**：已完成 `engine.py` 基礎骨架，包含 `ReportScanner` (掃描器)、`ReportAuditor` (審核器) 與 `ReportRenderer` (渲染器) 的類別定義。
            - **邏輯驗證 (Automated QA)**：已透過 `test_engine.py` 完成「壓力測試」。
                - **正向測試 (Positive Testing)**：驗證符合規範的資料能順利通過。
                - **負向測試 (Negative Testing)**：驗證「攔截機制」有效（成功攔截圖片不足、標題過短等錯誤案例）。
            - **開發策略**：採用「防禦性開發 (Defensive Development)」與「回歸測試 (Regression Testing)」模式，確保新功能開發不會破壞既有的檢查邏輯。
    - **開發流程 SOP**：建立專案目錄 $\rightarrow$ 撰寫 `SKILL.md` $\rightarrow$ 建立依賴與資料模型 $\rightarrow$ 開發 `engine.py` $\rightarrow$ 執行測試並產出報告。
    - **核心架構 (End-to-End Pipeline)**：
        1. **資料準備與掃描 (Data Ingestion)**：驗證路徑與圖片數量 (3~5 張)。
        2. **內容生成與邏輯審核 (Content Generation & Audit)**：將文字與圖片資訊組裝，並執行 **7 項嚴格 QA 檢查**。
        3. **文檔排版與 PDF 渲染 (Document Rendering)**：使用 `ReportLab` 將文字、表格與圖片直接嵌入至單一 PDF 檔案中。
        4. **最終交付 (Final Delivery)**：輸出 `Final_Report.pdf` 與包含 QA 結果的 `Audit_Log.txt`。

## AI 技能庫 (Skills Inventory)
- **核心工具能力**：檔案操作 (`read`, `write`, `edit`, `list`)、指令執行 (`exec`)、數學運算。
- **專業領域技能**：
    - `docx Skill`：Word 文檔處理與自動化。
    - `pdf Skill`：PDF 數據提取、合併與分析。
    - `skill-creator Skill`：引導建立新技能的 SOP 指南。
    - `green-market-reporter Skill` (開發中)：
        - **核心邏輯**：自動化出版流水線，具備「內容審核」與「精確排版」能力。
        - **QA 驗證引擎 (Validation Engine)**：內建 7 項自動化檢查標準。
        - **技術棧**：`ReportLab` (PDF 渲染)、`Pillow` (影像處理)、`pytest`/`unittest` (自動化測試)。

## 遇到的環境問題與約束 (Constraints & Issues)
- **執行環境限制**：目前環境中 `uv` 指令不可用，需回歸使用系統內建 `python` 指令進行開發與測試。
- **編碼問題**：Windows PowerShell 預設編碼可能導致 Python 輸出亂碼，執行指令時需搭配 `chcp 65001` 以確保 UTF-8 正確顯示。

## 未來潛在需求 (待辦事項)
- **計算機功能擴充**：增加歷史紀錄、支援連續運算、重構為 Class 結構、開發 GUI。
- **新 Skill 開發計畫**：
    - **推進 `green-market-reporter` 實作**：
        - [ ] **強化審核能力**：補全 `Auditor` 剩餘的 4 項 QA 檢查（如：摘要長度、圖文對應等）。
        - [ ] **實作渲染引擎**：開發 `ReportRenderer`，使用 `ReportLab` 產出實際 PDF。
        - [ ] **擴充測試案例**：增加更多極端邊界值測試。
- **學習歷程自動化**：根據 `green-market-reporter` 的經驗，擴展至其他類型的「個人成就與反思紀錄」自動化工具。
```