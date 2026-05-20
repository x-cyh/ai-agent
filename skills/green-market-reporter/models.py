from dataclasses import dataclass, field
from typing import List

@dataclass
class ReportData:
    """
    定義綠生活循環市集報告的核心資料模型。
    所有的資料在進入 Engine 處理前，都必須符合此結構。
    """
    title: str
    date: str
    summary: str
    description: str
    image_paths: List[str] = field(default_factory=list)
    image_captions: List[str] = field(default_factory=list)

    def validate_structure(self) -> bool:
        """
        初步的結構驗證：檢查圖片數量與圖說數量是否匹配，
        以及圖片路徑是否不為空。
        """
        if not self.title or not self.date:
            return False
        
        # 檢查圖片與圖說是否成對 (如果有的話)
        if self.image_paths and self.image_captions:
            if len(self.image_paths) != len(self.image_captions):
                return False
        
        return True
