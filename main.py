import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def build_system_prompt() -> str:
    """建立系統提示字串。"""
    system_text = "你是課堂程式助教。請使用繁體中文；先給一句重點結論，必要時再補一句說明。"
    nick = "法門超人"
    return f"{system_text}\n\n【本場次顯示名稱】 {nick}"

def main():
    # 讀取配置
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    agent_name = "Gemma4 Agent"

    if not api_key:
        print("❌ 未設定 API Key，請檢查 .env 檔案。")
        return

    # 初始化 LLM
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=0.7
    )

    # 建立記憶體串列 (本題稱 messages)
    messages = []

    print(f"🚀 {agent_name} 已就緒！")
    print(f"--- 提示：輸入 'exit' 或 'q' 離開對話，輸入 'clear' 重置記憶 ---")

    try:
        while True:
            # 取得使用者輸入
            message = input("\n使用者: ").strip()

            # 只送空白 continue
            if not message:
                continue

            # 輸入 exit 或 q 留下告別 break
            if message.lower() == "exit" or message.lower() == "q":
                print(f"\n{agent_name}: 再見！")
                break

            # 處理重置記憶
            if message.lower() == 'clear':
                messages = [SystemMessage(content="你是一個親切的助理，請一律使用「繁體中文」回答使用者的所有問題。")]
                print(f"\n{agent_name}: 記憶已重置。")
                continue

            # 1. 先把本輪字句建成 human_message
            human_message = HumanMessage(content=message)

            # 2. 組合成 context_messages 送給 LLM
            system_message = SystemMessage(content=build_system_prompt())
            context_messages = [
                system_message,
                *messages,
                human_message
            ]

            # 呼叫模型 (使用串流輸出)
            try:
                print(f"\n{agent_name}: ", end="", flush=True)
                full_response = ""
                
                # 3. 累積回應的 AIChunkMessage (串流中)
                for chunk in llm.stream(context_messages):
                    if chunk.content:
                        for char in chunk.content:
                            print(char, end="", flush=True)
                            full_response += char
                            time.sleep(0.01)  # 稍微加快速度提升體驗
                
                print()  # 結束後換行

                # 4. 串流結束後，合併成 AIMessage 並與 human_message 存入 messages 中
                messages.append(human_message)
                messages.append(AIMessage(content=full_response))
                
            except Exception as e:
                print(f"\n❌ 發生錯誤: {e}")

    except KeyboardInterrupt:
        print(f"\n\n{agent_name}: 偵測到強制結束，再見！")

if __name__ == "__main__":
    main()
