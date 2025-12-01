# MCP Playground - Learning MCP Together

This is a learning project to explore Model Context Protocol (MCP) through simple, practical examples.

## Getting Started

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running
   - Install from: https://ollama.ai
   - Start Ollama: `ollama serve` (or it may run automatically)
   - Pull the qwen3 model: `ollama pull qwen3:latest`

### Setup

1. Create a virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Configure system prompt:
   - Edit `system_prompt.txt` to customize the system prompt
   - Or set `SYSTEM_PROMPT_PATH` in `.env` to use a different file:
   ```bash
   SYSTEM_PROMPT_PATH=path/to/your/prompt.txt
   ```

4. (Optional) Configure API keys:
Create a `.env` file in the project root and add:
```bash
ALPHAVANTAGE_API_KEY=your_alpha_vantage_api_key_here  # Optional, for stock symbol search fallback
```

The system prompt is loaded from a file and sent to the LLM at the start of each conversation to customize its behavior, personality, or instructions.

## Examples

### Example 1: Simple Qwen3 Chatbot

A basic command-line chatbot using Ollama's qwen3:latest model.

**Run it:**
```bash
python chatbot.py
```

**Features:**
- Interactive command-line chat interface
- Streaming responses for real-time feedback
- Conversation history maintained for context
- Graceful error handling

**Usage:**
- Type your message and press Enter
- Type `quit`, `exit`, or `bye` to end the conversation
- Press Ctrl+C to interrupt

## Next Steps

We'll build more examples as we learn MCP together:
- Integrating MCP servers with the chatbot
- Using MCP tools in conversations
- Building more complex agent workflows


