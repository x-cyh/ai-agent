"""靜態測試 10_Life_Story.py 的依賴與功能。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=== 1. 測試 page_shell 與 shell_ui import ===")
try:
    from studio_shell.page_shell import page_shell
    from studio_shell.shell_ui import (
        format_extra_context,
        load_page_data,
        save_page_data,
        shared_data_path,
        page_slug,
    )
    print("page_shell: OK")
    print("format_extra_context: OK")
    print("load_page_data: OK")
    print("save_page_data: OK")
    print("shared_data_path: OK")
    print("page_slug: OK")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print()
print("=== 2. 測試 page_slug 對中文頁名的處理 ===")
print(f"人生故事書 -> {page_slug('人生故事書')}")
print(f"Smart Assistant -> {page_slug('Smart Assistant')}")
print(f"總覽 -> {page_slug('總覽')}")

print()
print("=== 3. 測試資料檔案讀寫 ===")
SHELL_ROOT = Path("studio_shell")
data = load_page_data("人生故事書", shell_root=SHELL_ROOT)
print(f"讀取 人生故事書.json: {data}")
save_page_data("人生故事書", data, shell_root=SHELL_ROOT)
print("寫回 人生故事書.json: OK")

print()
print("=== 4. 測試 format_extra_context ===")
ctx = format_extra_context(
    "人生故事書",
    故事主線="測試主線",
    訪談進度="測試進度",
)
print(ctx)

print()
print("=== 5. 測試 shared_data_path ===")
p = shared_data_path("人生故事書", shell_root=SHELL_ROOT)
print(f"shared_data_path: {p}")
print(f"檔案存在: {p.is_file()}")

print()
print("=== 6. 測試 10_Life_Story.py 語法 ===")
import py_compile
try:
    py_compile.compile("studio_shell/pages/10_Life_Story.py", doraise=True)
    print("10_Life_Story.py 語法: OK")
except py_compile.PyCompileError as e:
    print(f"FAIL: {e}")

print()
print("=== 7. 測試 app.py 語法 ===")
try:
    py_compile.compile("studio_shell/app.py", doraise=True)
    print("app.py 語法: OK")
except py_compile.PyCompileError as e:
    print(f"FAIL: {e}")

print()
print("=== 全部測試完成 ===")