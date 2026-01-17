"""工具基类定义"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


class ToolParameters(BaseModel):
    """工具参数基类"""
    pass


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    artifacts: list[str] = field(default_factory=list)  # 产生的文件列表


class BaseTool(ABC):
    """工具基类"""

    name: str = "base_tool"
    description: str = "Base tool description"
    parameters_schema: dict = {}
    requires_confirmation: bool = False  # 是否需要用户确认

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def to_schema(self) -> dict:
        """转换为 OpenAI function calling schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters_schema,
                    "required": list(self.parameters_schema.keys())
                }
            }
        }

    def validate_params(self, **kwargs) -> bool:
        """验证参数"""
        required = list(self.parameters_schema.keys())
        return all(k in kwargs for k in required)


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """列出所有工具"""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """获取所有工具的 schema"""
        return [tool.to_schema() for tool in self._tools.values()]

    def get_descriptions(self) -> str:
        """获取工具描述文本"""
        lines = []
        for tool in self._tools.values():
            params = ", ".join(f"{k}: {v.get('type', 'any')}"
                              for k, v in tool.parameters_schema.items())
            lines.append(f"- **{tool.name}**({params}): {tool.description}")
        return "\n".join(lines)


# 全局工具注册表
tool_registry = ToolRegistry()
