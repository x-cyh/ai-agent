import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    agent_name = "Gemma4 Agent"
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")

    if api_key:
        print(f"API Key found;已設定")
    else:
        print("未設定 API Key;請檢查 .env 或系統環境變數")
        return
    
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=1.0
    )
    
    message = f"你好(用繁體中文回答)"
    print(f"\n使用者:{message}")
    
    response = llm.invoke(message)
    print(f"\nGemma4 Agent:{response.content}")
    


if __name__ == "__main__":
    main()
