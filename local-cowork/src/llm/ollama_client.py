"""Ollama LLM 客户端"""
import json
from typing import Generator, Optional
from dataclasses import dataclass
import ollama
from loguru import logger


@dataclass
class Message:
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


class OllamaClient:
    def __init__(
        self,
        model: str = "qwen2.5-coder:32b",
        api_base: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.model = model
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = ollama.Client(host=api_base)

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> Message:
        """发送聊天请求"""
        # 转换消息格式
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        # 如果有工具定义，添加到请求中
        if tools:
            kwargs["tools"] = tools

        try:
            if stream:
                return self._stream_chat(**kwargs)
            else:
                response = self.client.chat(**kwargs)
                return self._parse_response(response)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    def _parse_response(self, response: dict) -> Message:
        """解析响应"""
        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = None

        # 解析工具调用
        if "tool_calls" in message:
            tool_calls = [
                ToolCall(
                    id=tc.get("id", f"call_{i}"),
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                )
                for i, tc in enumerate(message["tool_calls"])
            ]

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls
        )

    def _stream_chat(self, **kwargs) -> Generator[str, None, None]:
        """流式输出"""
        for chunk in self.client.chat(stream=True, **kwargs):
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]


def create_tool_schema(name: str, description: str, parameters: dict) -> dict:
    """创建工具 schema（OpenAI function calling 格式）"""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys())
            }
        }
    }
