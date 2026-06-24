import os
from datetime import datetime

# 確保 story_outputs 資料夾存在
output_dir = r"C:\Users\AI_1\Desktop\ai-agent\studio_shell\story_outputs"
os.makedirs(output_dir, exist_ok=True)

# 取得目前時間戳記 (格式: YYYYMMDD_HHMMSS)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 故事標題（去除特殊字元避免檔名問題）
story_title = "你爸國小的經歷"

# 完整檔名
filename = f"{timestamp}_{story_title}.md"
filepath = os.path.join(output_dir, filename)

# 故事內容（初稿，根據目前蒐集到的事實整理）
content = f"""# 你爸國小的經歷

> 故事狀態：in_progress（測試匯出版）
> 建立時間：2026-06-24
> 匯出時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📖 故事主線

**主題：** 爸爸小學四年級時，因為家境關係需要幫忙家裡工作，某天早上因為太累遲到，被導師誤會是故意偷懶，在全班面前被嚴厲斥責。當下他覺得委屈又丟臉，回家後默默把這件事藏在心裡，沒跟家人說。多年後他回想這段，體會到老師當時也是出於關心，而那段被誤會的經歷，反而讓他學會忍耐與溝通的重要。

---

## 🎯 故事結構

### ① 主線
✅ 已設定

### ② 背景
⏳ 待補（年代、社會氛圍、家庭狀況）

### ③ 開端
✅ 某天早上因為太累遲到

### ④ 衝突
✅ 被導師誤會是故意偷懶，在全班面前被嚴厲斥責

### ⑤ 決定
✅ 默默把這件事藏在心裡，沒跟家人說

### ⑥ 結果
✅ 多年後回想這段經歷

### ⑦ 意義
✅ 體會到老師當時也是出於關心；學會忍耐與溝通的重要

### ⑧ 留給孩子的話
⏳ 待補

---

## 📝 已蒐集事實

- **故事ID：** story_20260624_153007_346bbc
- **故事標題：** 你爸國小的經歷
- **故事狀態：** in_progress
- **爸爸年級：** 四年級
- **遲到原因：** 因為家境關係需要幫忙家裡工作，太累
- **衝突事件：** 被導師誤會故意偷懶，當眾嚴厲斥責
- **爸爸當下感受：** 委屈、丟臉
- **爸爸的決定：** 默默藏在心裡，沒跟家人說
- **多年後的領悟：** 老師當時是出於關心
- **學到的課題：** 忍耐與溝通的重要

---

## 🔖 訪談進度

- 訪談輪數：4
- 測試狀態：✅ 匯出檔案測試成功

---

*本檔案為測試匯出版，由人生故事書系統自動產生。*
"""

# 寫入檔案
with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 匯出成功！")
print(f"📄 檔案路徑：{filepath}")
print(f"📏 檔案大小：{os.path.getsize(filepath)} bytes")