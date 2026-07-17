# core/ai/ollama_client.py
import logging

logger = logging.getLogger(__name__)

def ask_ollama(prompt, model="qwen2.5-coder:1.5b"):
    """
    调用 Ollama API（如果可用），否则返回错误提示
    """
    try:
        import ollama
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except ImportError:
        logger.warning("Ollama library not installed. LLM features disabled.")
        return "Error: Ollama not installed"
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"Error: {e}"