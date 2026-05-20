import os
import shutil
import unittest
from engine import ReportScanner, ReportAuditor
from models import ReportData

class TestGreenMarketEngine(unittest.TestCase):
    def setUp(self):
        """測試前的準備：建立模擬的圖片目錄與資料"""
        self.test_dir = "test_images_tmp"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # 建立一些空的 dummy 圖片檔案
        self.dummy_images = []
        for i in range(4):  # 預設建立 4 張，符合 3-5 規範
            img_path = os.path.join(self.test_dir, f"test_{i}.jpg")
            with open(img_path, "w") as f:
                f.write("dummy content")
            self.dummy_images.append(img_path)

        self.valid_data = ReportData(
            title="綠生活市集 2023",
            date="2023-10-27",
            summary="本次市集非常熱鬧。",
            description="介紹了許多環保產品。",
            image_captions=["圖1", "圖2", "圖3", "圖4"]
        )

    def tearDown(self):
        """測試後的清理：刪除臨時目錄"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_scanner_correct_count(self):
        """驗證 Scanner 是否能正確計算圖片數量"""
        scanner = ReportScanner(self.test_dir)
        found_images = scanner.scan()
        self.assertEqual(len(found_images), 4)

    def test_auditor_pass_case(self):
        """驗證符合規範的資料是否能通過審核"""
        auditor = ReportAuditor(self.valid_data, self.dummy_images)
        is_passed = auditor.run_all_checks()
        self.assertTrue(is_passed, f"Audit failed unexpectedly: {auditor.audit_log}")

    def test_auditor_fail_image_count(self):
        """驗證圖片數量不符時，Auditor 是否能攔截 (FAIL)"""
        # 故意減少圖片到 1 張 (不符合 3-5 規範)
        few_images = [self.dummy_images[0]]
        auditor = ReportAuditor(self.valid_data, few_images)
        is_passed = auditor.run_all_checks()
        self.assertFalse(is_passed)
        # 檢查 Log 中是否有 FAIL 訊息
        self.assertTrue(any("FAIL" in log for log in auditor.audit_log))

    def test_auditor_fail_title_length(self):
        """驗證標題太短時，Auditor 是否能攔截 (FAIL)"""
        short_data = ReportData(
            title="短", # 太短
            date="2023-10-27",
            summary="摘要",
            description="描述",
            image_captions=[]
        )
        auditor = ReportAuditor(short_data, self.dummy_images)
        is_passed = auditor.run_all_checks()
        self.assertFalse(is_passed)

if __name__ == "__main__":
    unittest.main()
