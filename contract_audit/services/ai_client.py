"""AI调用客户端。"""
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import aiohttp

from models.database import get_db


class AIClient:
    """统一使用 OpenAI 兼容协议调用 AI 服务。"""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = provider.strip() if provider else None
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self._config_loaded = False

    async def _load_database_config(self) -> Dict[str, Any]:
        async with get_db() as db:
            if self.provider:
                cursor = await db.execute(
                    "SELECT provider, api_key, endpoint, model, enabled "
                    "FROM ai_config WHERE provider = ?",
                    (self.provider,),
                )
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"AI配置 {self.provider} 不存在")
            else:
                cursor = await db.execute(
                    "SELECT provider, api_key, endpoint, model, enabled "
                    "FROM ai_config WHERE enabled = TRUE ORDER BY id LIMIT 1"
                )
                row = await cursor.fetchone()
                if not row:
                    raise ValueError("未启用任何AI配置，请先在AI配置中启用一条配置")

        return dict(row)

    async def _ensure_config_loaded(self):
        if self.api_key and self.endpoint and self.model:
            self._config_loaded = True
            return

        if self._config_loaded and self.api_key and self.endpoint and self.model:
            return

        config = await self._load_database_config()
        self.provider = self.provider or config["provider"]
        self.api_key = self.api_key or config["api_key"]
        self.endpoint = self.endpoint or config["endpoint"]
        self.model = self.model or config["model"]

        missing_fields = [
            field_name
            for field_name, value in (
                ("api_key", self.api_key),
                ("endpoint", self.endpoint),
                ("model", self.model),
            )
            if not value
        ]
        if missing_fields:
            config_name = self.provider or "当前启用配置"
            raise ValueError(
                f"AI配置 {config_name} 缺少必要字段: {', '.join(missing_fields)}"
            )

        self._config_loaded = True

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 AI 模型。"""
        await self._ensure_config_loaded()
        return await self._call_openai(messages, **kwargs)

    def _normalize_endpoint(self) -> str:
        endpoint = (self.endpoint or "").strip()
        if not endpoint:
            return endpoint

        parsed = urlparse(endpoint)
        path = parsed.path.rstrip("/")
        if path.endswith("/chat/completions"):
            return endpoint

        if not path:
            path = "/chat/completions"
        else:
            path = f"{path}/chat/completions"

        return urlunparse(parsed._replace(path=path))

    @staticmethod
    def _extract_text_content(data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError(f"OpenAI兼容接口返回格式异常: {data}")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            text = "".join(text_parts).strip()
            if text:
                return text

        raise ValueError(f"OpenAI兼容接口返回格式异常: {data}")

    async def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 OpenAI 兼容接口。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }
        endpoint = self._normalize_endpoint()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180, connect=30),
                ) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        error_text = response_text[:500] if response_text else "无响应内容"
                        raise RuntimeError(
                            f"AI服务返回错误状态码 {response.status}: {error_text}"
                        )
                    data = await response.json()
                    return self._extract_text_content(data)
        except aiohttp.ServerTimeoutError as exc:
            raise TimeoutError(
                "AI服务读取超时，请检查网络连接或稍后重试。"
            ) from exc
        except aiohttp.ClientError as exc:
            raise RuntimeError(
                f"AI服务连接失败: {type(exc).__name__}: {str(exc) or 'ClientError'}"
            ) from exc
        except Exception as exc:
            if isinstance(exc, (TimeoutError, RuntimeError, ValueError)):
                raise
            raise RuntimeError(
                f"AI服务调用失败: {type(exc).__name__}: {str(exc) or '未知错误'}"
            ) from exc
