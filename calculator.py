def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        return "錯誤：除數不能為零！"
    return x / y

def main():
    print("--- 簡易 Python 計算機 ---")
    print("請選擇運算類型：")
    print("1. 加法 (+)")
    print("2. 減法 (-)")
    print("3. 乘法 (*)")
    print("4. 除法 (/)")
    
    choice = input("輸入選擇 (1/2/3/4): ")

    if choice in ('1', '2', '3', '4'):
        try:
            num1 = float(input("輸入第一個數字: "))
            num2 = float(input("輸入第二個數字: "))
        except ValueError:
            print("錯誤：請輸入有效的數字。")
            return

        if choice == '1':
            print(f"結果: {num1} + {num2} = {add(num1, num2)}")
        elif choice == '2':
            print(f"結果: {num1} - {num2} = {subtract(num1, num2)}")
        elif choice == '3':
            print(f"結果: {num1} * {num2} = {multiply(num1, num2)}")
        elif choice == '4':
            result = divide(num1, num2)
            if isinstance(result, str):
                print(result)
            else:
                print(f"結果: {num1} / {num2} = {result}")
    else:
        print("無效的選擇")

if __name__ == "__main__":
    main()
