import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    agent_name = "Agent 666"
    # message = f"hi i am {}"
    if api_key is None:
        print("未設定 API Key;請檢查 .env 或系統環境變數")
        exit()
    else:
        print(f"API Key found;已設定:{api_key}")
    
    # response = llm.invoke("Hi, I'm Agent 666")
    # print(response.content)



if __name__ == "__main__":
    main()
