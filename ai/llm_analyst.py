# core/ai/llm_analyst.py
import json
import logging
import re
from core.ai.ollama_client import ask_ollama

logger = logging.getLogger(__name__)

class LLMAnalyst:
    def __init__(self, model_name: str = "qwen2.5-coder:1.5b"):
        self.model = model_name
        self.enabled = True
        # 测试 Ollama 是否可用
        try:
            import ollama
            # 简单测试（可选）
            # ollama.list()
        except ImportError:
            logger.warning("Ollama library not installed. LLM Analyst disabled.")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Ollama not ready: {e}. LLM Analyst disabled.")
            self.enabled = False

    def analyze(self, df_summary: dict) -> dict:
        """
        如果 LLM 启用，则调用 Ollama 进行分析；否则返回默认中性结果。
        """
        if not self.enabled:
            return {
                "bias": "neutral",
                "risk_adjustment": 1.0,
                "preferred_strategy": None,
                "comment": "LLM disabled"
            }

        prompt = f"""
You are an expert trading analyst. Based on the following market summary, 
provide your short-term (next 4-8 hours) outlook and a recommended strategy.

Market Summary:
{json.dumps(df_summary, indent=2)}

Output ONLY a JSON object with the following keys:
- "bias": "bullish" or "bearish" or "neutral"
- "risk_adjustment": a float between 0.5 and 1.5 (0.5 = very conservative, 1.5 = aggressive)
- "preferred_strategy": one of ["MA_CROSSOVER", "RSI_CROSSOVER", "BOLLINGER_REVERSION", "TURTLE_BREAKOUT", "QUANTUM_VELOCITY"]
- "comment": a short explanation (max 30 words)

Do not include any other text.
"""
        try:
            response = ask_ollama(prompt, model=self.model)
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "bias": "neutral",
                    "risk_adjustment": 1.0,
                    "preferred_strategy": None,
                    "comment": "LLM response parsing failed"
                }
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            result = {
                "bias": "neutral",
                "risk_adjustment": 1.0,
                "preferred_strategy": None,
                "comment": str(e)
            }
        return result