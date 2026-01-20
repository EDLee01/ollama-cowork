"""多 LLM 提供商支持"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Generator, Any
import json
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


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> LLMResponse | Generator[str, None, None]:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API 提供商（也兼容 DeepSeek, Together 等）"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        api_base: Optional[str] = None
    ):
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )

    def get_model_name(self) -> str:
        return self.model

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> LLMResponse | Generator[str, None, None]:
        # 转换消息格式
        openai_messages = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            openai_messages.append(m)

        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if stream:
            return self._stream_chat(**kwargs)

        response = self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    def _stream_chat(self, **kwargs) -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(**kwargs)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _parse_response(self, response) -> LLMResponse:
        choice = response.choices[0]
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                ))

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        )


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API 提供商"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        from anthropic import Anthropic

        self.model = model
        self.client = Anthropic(api_key=api_key)

    def get_model_name(self) -> str:
        return self.model

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> LLMResponse | Generator[str, None, None]:
        # 分离 system message
        system = ""
        claude_messages = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            elif msg.role == "tool":
                # Claude 使用 tool_result 格式
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        kwargs = {
            "model": self.model,
            "messages": claude_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system:
            kwargs["system"] = system

        if tools:
            # 转换为 Claude 工具格式
            kwargs["tools"] = self._convert_tools(tools)

        if stream:
            return self._stream_chat(**kwargs)

        response = self.client.messages.create(**kwargs)
        return self._parse_response(response)

    def _convert_tools(self, openai_tools: list[dict]) -> list[dict]:
        """将 OpenAI 工具格式转换为 Claude 格式"""
        claude_tools = []
        for tool in openai_tools:
            if tool["type"] == "function":
                func = tool["function"]
                claude_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                })
        return claude_tools

    def _stream_chat(self, **kwargs) -> Generator[str, None, None]:
        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def _parse_response(self, response) -> LLMResponse:
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            }
        )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API 提供商"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro"
    ):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    def get_model_name(self) -> str:
        return self.model_name

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> LLMResponse | Generator[str, None, None]:
        import google.generativeai as genai

        # 转换消息格式
        history = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                history.append({"role": "model", "parts": [msg.content]})

        # 配置生成参数
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        # 创建带系统指令的模型
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system_instruction,
            generation_config=generation_config
        )

        chat = model.start_chat(history=history[:-1] if history else [])

        if stream:
            return self._stream_chat(chat, history[-1]["parts"][0] if history else "")

        response = chat.send_message(history[-1]["parts"][0] if history else "")
        return LLMResponse(
            content=response.text,
            tool_calls=[],
            finish_reason="stop"
        )

    def _stream_chat(self, chat, message: str) -> Generator[str, None, None]:
        response = chat.send_message(message, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API 提供商（基于 OpenAI 兼容接口）"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(
            api_key=api_key,
            model=model,
            api_base="https://api.deepseek.com/v1"
        )


# 提供商注册表
PROVIDERS = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "gemini": GeminiProvider,
    "google": GeminiProvider,
    "deepseek": DeepSeekProvider,
}


def create_provider(
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """创建 LLM 提供商实例"""
    provider = provider.lower()

    if provider not in PROVIDERS:
        raise ValueError(f"不支持的提供商: {provider}. 支持: {list(PROVIDERS.keys())}")

    provider_class = PROVIDERS[provider]

    # 默认模型
    default_models = {
        "openai": "gpt-4o",
        "claude": "claude-sonnet-4-20250514",
        "anthropic": "claude-sonnet-4-20250514",
        "gemini": "gemini-1.5-pro",
        "google": "gemini-1.5-pro",
        "deepseek": "deepseek-chat",
    }

    model = model or default_models.get(provider)
    logger.info(f"初始化 {provider} 提供商，模型: {model}")

    return provider_class(api_key=api_key, model=model, **kwargs)
