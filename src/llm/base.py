"""
LLM接口基础类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """LLM接口基础类"""

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        """
        初始化LLM

        Args:
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
            **kwargs: 其他参数
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        对话接口

        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型回复文本
        """
        pass

    @abstractmethod
    def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        带系统提示的对话接口

        Args:
            system_prompt: 系统提示
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型回复文本
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(model={self.model})"
