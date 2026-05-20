import os
from typing import List
from models import ReportData

class ReportScanner:
    """負責掃描輸入路徑並驗證基礎資源 (如圖片數量)"""
    def __init__(self, image_dir: str):
        self.image_dir = image_dir

    def scan(self) -> List[str]:
        """
        掃描目錄下的圖片檔案。
        符合 SKILL.md 規範：檢查圖片數量是否在 3~5 張之間。
        """
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        if not os.path.exists(self.image_dir):
            print(f"Error: Directory {self.image_dir} does not exist.")
            return []
        
        images = [
            os.path.join(self.image_dir, f) 
            for f in os.listdir(self.image_dir) 
            if f.lower().endswith(valid_extensions)
        ]
        return images

class ReportAuditor:
    """負責執行 SKILL.md 定ும்的 7 項 QA 檢查"""
    def __init__(self, data: ReportData, image_paths: List[str]):
        self.data = data
        self.image_paths = image_paths
        self.audit_log = []
        self.is_passed = True

    def add_log(self, check_name: str, status: str, message: str):
        self.audit_log.append(f"[{status}] {check_name}: {message}")
        if status == "FAIL":
            self.is_passed = False

    def run_all_checks(self) -> bool:
        """執行所有預定義的 QA 檢查"""
        self.audit_log = []
        self.is_passed = True
        
        # 檢查 1: 圖片數量檢查 (3-5 張)
        img_count = len(self.image_paths)
        if 3 <= img_count <= 5:
            self.add_log("Image Count", "PASS", f"Found {img_count} images.")
        else:
            self.add_log("Image Count", "FAIL", f"Found {img_count} images, expected 3-5.")

        # 檢查 2: 標題長度檢查 (範例)
        if len(self.data.title) >= 5:
            self.add_log("Title Length", "PASS", "Title is sufficiently descriptive.")
        else:
            self.add_log("Title Length", "FAIL", "Title is too short.")

        # 檢查 3: 摘要是否存在
        if self.data.summary.strip():
            self.add_log("Summary Presence", "PASS", "Summary is provided.")
        else:
            self.add_log("Summary Presence", "FAIL", "Summary is empty.")

        # 這裡預留其他 4 項檢查的空間...
        
        return self.is_passed

    def save_log(self, log_path: str):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.audit_log))

class ReportRenderer:
    """負責使用 ReportLab 將資料渲染成 PDF"""
    def __init__(self, data: ReportData, image_paths: List[str]):
        self.data = data
        self.image_paths = image_paths

    def render(self, output_path: str):
        """
        實作 PDF 渲染邏輯 (目前僅建立佔位符)
        """
        print(f"Rendering report to {output_path}...")
        # 實際開發時會使用 reportlab 繪製
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Report Title: {self.data.title}\n")
            f.write(f"Date: {self.data.date}\n")
            f.write(f"Summary: {self.data.summary}\n")
            f.write(f"Description: {self.data.description}\n")
        print("Rendering complete (Placeholder mode).")

if __name__ == "__main__":
    print("Engine structure initialized.")
