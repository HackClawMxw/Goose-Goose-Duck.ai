"""
LLM工厂类 - 根据配置创建不同的LLM实例
"""
from typing import Dict, Any
import logging
from .base import BaseLLM
from .glm import GLMLLM
from .openai_compatible import OpenAICompatibleLLM

logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM工厂类"""

    @staticmethod
    def create_llm(config: Dict[str, Any]) -> BaseLLM:
        """
        根据配置创建LLM实例

        Args:
            config: LLM配置字典

        Returns:
            LLM实例

        Raises:
            ValueError: 不支持的LLM类型
        """
        model = config.get('model', '')
        api_key = config.get('api_key', '')
        base_url = config.get('base_url', '')

        # 如果没有提供api_key，尝试从环境变量读取
        if not api_key:
            import os
            if 'glm' in model.lower():
                api_key = os.getenv('GLM_API_KEY', '')
            elif 'gpt' in model.lower() or 'openai' in model.lower():
                api_key = os.getenv('OPENAI_API_KEY', '')
            elif 'deepseek' in model.lower():
                api_key = os.getenv('DEEPSEEK_API_KEY', '')

        if not api_key:
            raise ValueError(f"未找到API密钥，请检查配置或环境变量")

        # 准备额外的配置参数（排除已使用的参数）
        extra_config = {k: v for k, v in config.items()
                       if k not in ['model', 'api_key', 'base_url']}

        # 根据模型名称判断使用哪个LLM类
        if 'glm' in model.lower():
            logger.info(f"创建GLM LLM: {model}")
            return GLMLLM(model, api_key, base_url, **extra_config)
        else:
            # 其他模型使用OpenAI兼容接口
            logger.info(f"创建OpenAI兼容 LLM: {model}")
            return OpenAICompatibleLLM(model, api_key, base_url, **extra_config)


__all__ = ['BaseLLM', 'GLMLLM', 'OpenAICompatibleLLM', 'LLMFactory']
