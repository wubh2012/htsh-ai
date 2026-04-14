"""AI调用客户端"""
import json
import aiohttp
from typing import Optional, List, Dict, Any
from config import AI_PROVIDERS, DEFAULT_PROVIDER


class AIClient:
    """AI调用客户端，支持多个Provider"""

    def __init__(self, provider: str = DEFAULT_PROVIDER, api_key: Optional[str] = None,
                 endpoint: Optional[str] = None, model: Optional[str] = None):
        """
        初始化AI客户端
        :param provider: AI提供商
        :param api_key: API密钥（如果为空则使用config中的配置）
        :param endpoint: API endpoint
        :param model: 模型名称
        """
        self.provider = provider.lower()
        self._load_config(api_key, endpoint, model)

    def _load_config(self, api_key: Optional[str], endpoint: Optional[str], model: Optional[str]):
        """加载配置"""
        if self.provider not in AI_PROVIDERS:
            raise ValueError(f"不支持的AI Provider: {self.provider}")

        config = AI_PROVIDERS[self.provider]
        self.api_key = api_key or config.get("api_key", "")
        self.endpoint = endpoint or config.get("endpoint", "")
        self.model = model or config.get("model", "")

        if not self.api_key:
            raise ValueError(f"{config['name']} 的API Key未配置，请在AI配置中设置")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用AI模型
        :param messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        :return: AI返回的文本
        """
        if self.provider == "zhipuai":
            return await self._call_zhipuai(messages, **kwargs)
        elif self.provider == "dashscope":
            return await self._call_dashscope(messages, **kwargs)
        elif self.provider == "wenxin":
            return await self._call_wenxin(messages, **kwargs)
        elif self.provider == "openai" or self.provider == "siliconflow":
            return await self._call_openai(messages, **kwargs)
        else:
            raise ValueError(f"不支持的Provider: {self.provider}")

    async def _call_zhipuai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用智谱AI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60, connect=30)) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise RuntimeError(f"智谱AI返回错误状态码 {response.status}: {response_text[:500]}")
                    data = await response.json()
                    # 提取响应内容
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    elif "data" in data and len(data["data"]["choices"]) > 0:
                        return data["data"]["choices"][0]["message"]["content"]
                    else:
                        raise ValueError(f"智谱AI返回格式异常: {data}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"智谱AI调用失败: {type(e).__name__}: {str(e)}")

    async def _call_dashscope(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用通义千问"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60, connect=30)) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise RuntimeError(f"通义千问返回错误状态码 {response.status}: {response_text[:500]}")
                    data = await response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        raise ValueError(f"通义千问返回格式异常: {data}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"通义千问调用失败: {type(e).__name__}: {str(e)}")

    async def _call_wenxin(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用百度文心一言"""
        # 文心一言使用不同的认证方式
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        # 将消息格式转换为文心一言格式
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            else:
                formatted_messages.append({"role": role, "content": msg["content"]})

        payload = {
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", 0.3),
        }

        # 文心一言需要在URL中包含api_key
        url = f"{self.endpoint}?access_token={self.api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60, connect=30)) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise RuntimeError(f"文心一言返回错误状态码 {response.status}: {response_text[:500]}")
                    data = await response.json()
                    if "result" in data:
                        return data["result"]
                    else:
                        raise ValueError(f"文心一言返回格式异常: {data}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"文心一言调用失败: {type(e).__name__}: {str(e)}")

    async def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用OpenAI GPT（使用aiohttp提高中文兼容性）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=180, connect=30)) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise RuntimeError(f"AI服务返回错误状态码 {response.status}: {response_text[:500] if response_text else '无响应内容'}")
                    data = await response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        raise ValueError(f"OpenAI返回格式异常: {data}")
        except aiohttp.ServerTimeoutError as e:
            raise TimeoutError(f"AI服务读取超时，请检查网络连接或稍后重试。原始错误: {str(e) or 'TimeoutError'}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"AI服务连接失败: {type(e).__name__}: {str(e) or 'ClientError'}")
        except Exception as e:
            raise RuntimeError(f"AI服务调用失败: {type(e).__name__}: {str(e) or '未知错误'}")

    @staticmethod
    def get_supported_providers() -> List[str]:
        """获取支持的Provider列表"""
        return list(AI_PROVIDERS.keys())

    @staticmethod
    def get_provider_info(provider: str) -> Dict[str, str]:
        """获取Provider信息"""
        if provider.lower() in AI_PROVIDERS:
            config = AI_PROVIDERS[provider.lower()]
            return {
                "name": config["name"],
                "model": config.get("model", ""),
            }
        return {}
