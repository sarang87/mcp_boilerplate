#!/usr/bin/env python3
"""
Diagnostic script to test Ollama setup and tool calling support.
"""

import requests
import json

def test_ollama_connection():
    """Test basic Ollama connection"""
    print("=" * 60)
    print("Testing Ollama Connection")
    print("=" * 60)
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get('models', [])
        
        print(f"✓ Connected to Ollama")
        print(f"✓ Found {len(models)} model(s):")
        for model in models:
            print(f"  - {model.get('name', 'unknown')}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False


def test_chat_endpoint():
    """Test /api/chat endpoint"""
    print("\n" + "=" * 60)
    print("Testing /api/chat endpoint")
    print("=" * 60)
    
    payload = {
        "model": "qwen2.5:latest",
        "messages": [{"role": "user", "content": "Say hello"}],
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ /api/chat endpoint works")
            data = response.json()
            print(f"Response: {data.get('message', {}).get('content', 'No content')[:100]}")
            return True
        else:
            print(f"✗ /api/chat returned {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_tool_calling():
    """Test tool calling support"""
    print("\n" + "=" * 60)
    print("Testing Tool Calling Support")
    print("=" * 60)
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "A test message"
                        }
                    },
                    "required": ["message"]
                }
            }
        }
    ]
    
    payload = {
        "model": "qwen2.5:latest",
        "messages": [{"role": "user", "content": "Call the test_tool with message 'hello'"}],
        "tools": tools,
        "stream": False
    }
    
    try:
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Tool calling endpoint works")
            data = response.json()
            message = data.get('message', {})
            tool_calls = message.get('tool_calls', [])
            
            if tool_calls:
                print(f"✓ Model supports tool calling! Found {len(tool_calls)} tool call(s)")
                for tc in tool_calls:
                    print(f"  Tool: {tc.get('function', {}).get('name', 'unknown')}")
            else:
                print("⚠️  Model responded but didn't use tools")
                print(f"  Response: {message.get('content', 'No content')[:100]}")
            return True
        elif response.status_code == 404:
            print("✗ 404 Error: Tool calling not supported")
            print("\nThis means:")
            print("  1. Your Ollama version is too old (need 0.1.26+)")
            print("  2. Or the endpoint doesn't exist")
            print("\nTo fix:")
            print("  - Update Ollama: brew upgrade ollama")
            print("  - Or download from: https://ollama.ai")
            return False
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    print("\n🔍 Ollama Diagnostic Tool\n")
    
    results = []
    results.append(("Connection", test_ollama_connection()))
    results.append(("Chat Endpoint", test_chat_endpoint()))
    results.append(("Tool Calling", test_tool_calling()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}")
    
    if all(r[1] for r in results):
        print("\n✓ All tests passed! Your setup is ready.")
    else:
        print("\n⚠️  Some tests failed. See above for details.")


if __name__ == "__main__":
    main()

