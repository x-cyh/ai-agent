import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

def main():
    agent_name = os.getenv("OPENAI_API_KEY")
    message = f"Hi, {agent_name}"
    print(message)
    

if __name__ == "__main__":
    main()
