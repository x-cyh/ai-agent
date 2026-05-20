import subprocess
import sys

def run_test(input_str):
    """執行 calculator.py 並傳入模擬的輸入字串"""
    process = subprocess.Popen(
        [sys.executable, 'calculator.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=input_str)
    return stdout

def test_calculator():
    print("開始測試計算機邏輯...\n")
    
    # 測試 1: 加法 (1 + 2 = 3)
    print("測試 1: 加法 (1 + 2)")
    res1 = run_test("1\n1\n2\n")
    assert "3.0" in res1
    print("✅ 通過")

    # 測試 2: 減法 (10 - 5 = 5)
    print("\n測試 2: 減法 (10 - 5)")
    res2 = run_test("2\n10\n5\n")
    assert "5.0" in res2
    print("✅ 通過")

    # 測試 3: 乘法 (3 * 4 = 12)
    print("\n測試 3: 乘法 (3 * 4)")
    res3 = run_test("3\n3\n4\n")
    assert "12.0" in res3
    print("✅ 通過")

    # 測試 4: 除法 (8 / 2 = 4)
    print("\n測試 4: 除法 (8 / 2)")
    res4 = run_test("4\n8\n2\n")
    assert "4.0" in res4
    print("✅ 通過")

    # 測試 5: 除以零錯誤處理
    print("\n測試 5: 除以零錯誤處理")
    res5 = run_test("4\n8\n0\n")
    assert "錯誤：除數不能為零！" in res5
    print("✅ 通過")

    print("\n🎉 所有測試項目均已通過！")

if __name__ == "__main__":
    try:
        test_calculator()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
