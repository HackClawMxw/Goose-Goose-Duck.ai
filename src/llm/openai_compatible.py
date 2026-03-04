"""
OpenAI兼容接口实现（支持OpenAI、DeepSeek等）
"""
from typing import List, Dict, Optional
import logging
from .base import BaseLLM

logger = logging.getLogger(__name__)


class OpenAICompatibleLLM(BaseLLM):
    """OpenAI兼容接口（支持OpenAI、DeepSeek等）"""

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        super().__init__(model, api_key, base_url, **kwargs)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"OpenAI兼容客户端初始化成功: {model} @ {base_url}")
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """对话接口"""
        try:
            temperature = temperature if temperature is not None else self.config.get('temperature', 0.7)
            max_tokens = max_tokens if max_tokens is not None else self.config.get('max_tokens', 2000)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            result = response.choices[0].message.content
            logger.debug(f"OpenAI响应: {result[:100]}...")
            return result

        except Exception as e:
            logger.error(f"OpenAI调用失败: {e}")
            raise

    def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """带系统提示的对话接口"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages, temperature, max_tokens, **kwargs)
