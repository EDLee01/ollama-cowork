"""工具系统基础类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from loguru import logger


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: str = ""
    artifacts: list[str] = field(default_factory=list)  # 产生的文件路径


class BaseTool(ABC):
    """工具基类"""
    name: str = ""
    description: str = ""
    parameters_schema: dict = {}
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def to_openai_schema(self) -> dict:
        """转换为 OpenAI 工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters_schema,
                    "required": [
                        k for k, v in self.parameters_schema.items()
                        if not v.get("optional", False)
                    ]
                }
            }
        }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"注册工具: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def get_openai_schemas(self) -> list[dict]:
        """获取所有工具的 OpenAI 格式 schema"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def get_tools_description(self) -> str:
        """获取工具描述文本"""
        lines = []
        for tool in self._tools.values():
            params = ", ".join(f"{k}: {v.get('type', 'string')}"
                             for k, v in tool.parameters_schema.items())
            confirm = "⚠️ 需确认" if tool.requires_confirmation else ""
            lines.append(f"- **{tool.name}**({params}): {tool.description} {confirm}")
        return "\n".join(lines)


# 全局工具注册表
tool_registry = ToolRegistry()
