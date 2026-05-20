import subprocess

def run_calculator_with_input(inputs):
    process = subprocess.Popen(
        ['python', 'calculator.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input="\n".join(inputs))
    return stdout

if __name__ == "__main__":
    # 模擬輸入: 1 (加法), 1 (第一個數), 1 (第二個數)
    result = run_calculator_with_input(["1", "1", "1"])
    print("--- 模擬執行結果 ---")
    print(result)
