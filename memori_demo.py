import os
from memori import Memori
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup Ollama with OpenAI-compatible client
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Setup SQLite
engine = create_engine("sqlite:///memori.db")
Session = sessionmaker(bind=engine)

# Setup Memori
mem = Memori(conn=Session).openai.register(client)
mem.attribution(entity_id="sarang", process_id="chatbot-v1")
mem.config.storage.build()

def chat(user_message):
    """Send a message and get a response"""
    response = client.chat.completions.create(
        model="qwen3:latest",
        messages=[{"role": "user", "content": user_message}],
    )
    return response.choices[0].message.content

def main():
    print("🤖 Chatbot with Memory (powered by Qwen3:8b)")
    print("I can answer questions AND remember facts about you!")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = chat(user_input)
        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()
