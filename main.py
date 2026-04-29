import os
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    print(api_key)
    agent_name = "666"
    message = f"Hi, I'm {agent_name}"
    print(message)

    


if __name__ == "__main__":
    main()
