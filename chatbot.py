#!/usr/bin/env python3
"""
Chatbot using Ollama's Qwen model with basic tool calling support.
This follows the agentic pattern with simple tool definitions.
"""

import requests
import json
import sys
import logging
import os
from dotenv import load_dotenv
from tools import execute_tool, get_available_tools

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:latest"

# System prompt configuration
# The prompt is loaded from a text file at startup (default: system_prompt.txt).
# You can override the path with the SYSTEM_PROMPT_PATH environment variable.
SYSTEM_PROMPT_PATH = os.getenv("SYSTEM_PROMPT_PATH", "system_prompt.txt")
SYSTEM_PROMPT: str = ""


def process_query(query: str, tools: list):
    """
    Process a user query using Ollama Qwen with tool support.
    Implements the agentic loop pattern that handles tool_use blocks.
    """
    # Build messages array with system prompt if configured
    messages = []
    if SYSTEM_PROMPT:
        messages.append({'role': 'system', 'content': SYSTEM_PROMPT})
        logger.debug("Added system prompt to messages")
    
    messages.append({'role': 'user', 'content': query})
    
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": tools,
        "stream": False
    }
    
    try:
        logger.debug(f"Sending request to Ollama: {OLLAMA_URL}")
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        
        # Check for specific error codes
        if response.status_code == 404:
            logger.error(f"Ollama endpoint not found. The model '{OLLAMA_MODEL}' may not support tool calling.")
            logger.error("The /api/chat endpoint returned 404. This could mean:")
            logger.error("1. Your Ollama version is too old (need 0.1.26+)")
            logger.error("2. The model doesn't support tool/function calling")
            logger.error(f"Model: {OLLAMA_MODEL}, Endpoint: {OLLAMA_URL}")
            logger.error("Possible solutions:")
            logger.error("1. Update Ollama: brew upgrade ollama (or download latest from ollama.ai)")
            logger.error("2. Try a model that supports tools: ollama pull qwen2.5:latest")
            logger.error("3. Check Ollama version: ollama --version (need 0.1.26+)")
            return
        
        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"Received response: {response_data}")
        
    except requests.exceptions.Timeout:
        logger.error("Request to Ollama timed out. Ollama may be processing a large request.")
        return
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama. Make sure it's running.")
        return
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from Ollama: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return
    
    process_query_flag = True
    iteration = 0
    max_iterations = 10  # Prevent infinite loops
    
    while process_query_flag and iteration < max_iterations:
        iteration += 1
        logger.debug(f"Processing iteration {iteration}")
        
        message = response_data.get('message', {})
        content = message.get('content', '')
        tool_calls = message.get('tool_calls', [])
        
        # If there's text content, log it
        if content:
            logger.info(f"LLM Response: {content}")
        
        # Check if there are tool calls
        if tool_calls:
            logger.info(f"Processing {len(tool_calls)} tool call(s)")
            # Add assistant message with tool calls to history
            messages.append(message)
            
            # Process each tool call
            for tool_call in tool_calls:
                try:
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function']['arguments']
                    
                    logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                    
                    # Call the tool
                    result = execute_tool(tool_name, tool_args)
                    logger.debug(f"Tool result: {result}")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": str(result)
                    })
                except KeyError as e:
                    logger.error(f"Malformed tool call: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error executing tool: {e}", exc_info=True)
                    continue
            
            # Get next response from Ollama
            try:
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "tools": tools,
                    "stream": False
                }
                response = requests.post(OLLAMA_URL, json=payload, timeout=30)
                response.raise_for_status()
                response_data = response.json()
            except Exception as e:
                logger.error(f"Error getting follow-up response: {e}")
                break
        else:
            # No more tool calls, we're done
            logger.debug("No more tool calls, ending loop")
            process_query_flag = False
    
    if iteration >= max_iterations:
        logger.warning("Max iterations reached, stopping to prevent infinite loop")


def chat_with_qwen(tools):
    """
    Main chatbot loop using Ollama Qwen with basic tools.
    Type 'quit', 'exit', or 'bye' to end the conversation.
    """
    logger.info("=" * 60)
    logger.info("Qwen Chatbot - Powered by Ollama with Tools")
    logger.info("=" * 60)
    logger.info("Type 'quit', 'exit', or 'bye' to end the conversation.")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                logger.info("User initiated exit")
                logger.info("Goodbye! Thanks for chatting!")
                break
            
            if not user_input:
                continue
            
            logger.info(f"User query: {user_input}")
            logger.info("Qwen: Processing query...")
            process_query(user_input, tools)
            logger.debug("Query processing completed")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            logger.info("Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Unexpected error in chat loop: {e}", exc_info=True)


def log_api_key_status() -> None:
    """Log the status of any API keys used by the application."""
    api_keys = {
        "ALPHAVANTAGE_API_KEY": os.getenv("ALPHAVANTAGE_API_KEY"),
    }
    for name, value in api_keys.items():
        if value:
            logger.info("%s loaded from environment", name)
        else:
            logger.info("%s not set", name)


def load_system_prompt_from_file() -> None:
    """Load the system prompt from the configured file into the global variable."""
    global SYSTEM_PROMPT
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read().strip()
        if SYSTEM_PROMPT:
            logger.info(
                "System prompt loaded from '%s' (%d characters)",
                SYSTEM_PROMPT_PATH,
                len(SYSTEM_PROMPT),
            )
        else:
            logger.info(
                "System prompt file '%s' is empty; no system prompt will be used",
                SYSTEM_PROMPT_PATH,
            )
    except FileNotFoundError:
        logger.info(
            "No system prompt file found at '%s'. Proceeding without system prompt.",
            SYSTEM_PROMPT_PATH,
        )
    except Exception as e:
        logger.error(
            "Error loading system prompt from '%s': %s",
            SYSTEM_PROMPT_PATH,
            e,
            exc_info=True,
        )


def ensure_ollama_available() -> None:
    """Verify Ollama is reachable and the desired model is available."""
    try:
        logger.debug("Checking Ollama connection...")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models_data = response.json()
        models = models_data.get("models", [])

        logger.info("Connected to Ollama. Found %d model(s)", len(models))

        model_names = [m.get("name", "") for m in models]
        logger.debug("Available models: %s", model_names)

        if not any("qwen" in name.lower() for name in model_names):
            logger.warning("No Qwen model found in Ollama.")
            logger.warning("You can install one with: ollama pull qwen3:latest")
        else:
            logger.info("Qwen model is available in Ollama")

    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama at http://localhost:11434")
        raise
    except requests.exceptions.Timeout:
        logger.error("Timeout connecting to Ollama")
        raise
    except Exception as e:
        logger.error("Unexpected error connecting to Ollama: %s", e, exc_info=True)
        raise


def initialize_tools():
    """Load and return the available tools."""
    try:
        tools = get_available_tools()
        logger.info("Loaded %d tool(s)", len(tools))
        return tools
    except Exception as e:
        logger.error("Error loading tools: %s", e, exc_info=True)
        raise


def main() -> None:
    """Application entry point."""
    logger.info("Starting chatbot application")

    # Startup checks and configuration
    log_api_key_status()
    load_system_prompt_from_file()
    ensure_ollama_available()

    # Initialize tools and start chat loop
    tools = initialize_tools()
    try:
        chat_with_qwen(tools)
    except Exception as e:
        logger.critical("Fatal error in chat loop: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        # Allow sys.exit() to propagate normally
        raise
    except Exception:
        # Any unhandled exception is already logged in main()
        sys.exit(1)
