"""Agent 核心 - Agentic Loop 实现"""
from dataclasses import dataclass, field
from typing import Callable, Optional
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ..llm.providers import BaseLLMProvider, Message, LLMResponse, ToolCall
from ..llm.prompts import AGENT_SYSTEM_PROMPT
from ..tools.base import tool_registry, ToolResult


console = Console()


@dataclass
class AgentConfig:
    max_iterations: int = 50
    timeout: int = 300
    verbose: bool = True
    auto_approve: bool = False


@dataclass
class AgentState:
    messages: list[Message] = field(default_factory=list)
    iteration: int = 0
    artifacts: list[str] = field(default_factory=list)
    total_tokens: dict = field(default_factory=lambda: {"prompt": 0, "completion": 0})


class Agent:
    """FlexCowork Agent"""

    def __init__(
        self,
        llm: BaseLLMProvider,
        workspace: str,
        config: Optional[AgentConfig] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ):
        self.llm = llm
        self.workspace = workspace
        self.config = config or AgentConfig()
        self.confirm_callback = confirm_callback or self._default_confirm
        self.state = AgentState()

    def _default_confirm(self, message: str) -> bool:
        """默认确认函数"""
        if self.config.auto_approve:
            return True
        response = input(f"\n⚠️  {message}\n确认执行? [y/N]: ")
        return response.lower() in ("y", "yes")

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return AGENT_SYSTEM_PROMPT.format(
            tools_description=tool_registry.get_tools_description(),
            workspace_path=self.workspace
        )

    def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        tool = tool_registry.get(tool_call.name)
        if not tool:
            return ToolResult(False, "", f"未知工具: {tool_call.name}")

        # 需要确认的工具
        if tool.requires_confirmation and not self.config.auto_approve:
            args_str = ", ".join(f"{k}={v}" for k, v in tool_call.arguments.items())
            if not self.confirm_callback(f"执行 {tool_call.name}({args_str})"):
                return ToolResult(False, "", "用户取消执行")

        if self.config.verbose:
            console.print(f"[cyan]🔧 执行工具:[/cyan] {tool_call.name}")
            for k, v in tool_call.arguments.items():
                console.print(f"   {k}: {str(v)[:100]}...")

        try:
            result = tool.execute(**tool_call.arguments)

            if result.artifacts:
                self.state.artifacts.extend(result.artifacts)

            if self.config.verbose:
                if result.success:
                    console.print(f"[green]✓ 成功[/green]")
                    if result.output:
                        console.print(Panel(result.output[:500], title="输出"))
                else:
                    console.print(f"[red]✗ 失败: {result.error}[/red]")

            return result
        except Exception as e:
            logger.exception(f"工具执行异常: {tool_call.name}")
            return ToolResult(False, "", str(e))

    def run(self, task: str) -> str:
        """运行 Agent"""
        logger.info(f"开始执行任务: {task[:100]}...")

        # 初始化消息
        self.state.messages = [
            Message(role="system", content=self._build_system_prompt()),
            Message(role="user", content=task)
        ]

        if self.config.verbose:
            console.print(Panel(task, title="📋 任务", border_style="blue"))

        # Agentic Loop
        while self.state.iteration < self.config.max_iterations:
            self.state.iteration += 1

            if self.config.verbose:
                console.print(f"\n[dim]--- 迭代 {self.state.iteration} ---[/dim]")

            # 调用 LLM
            try:
                response = self.llm.chat(
                    messages=self.state.messages,
                    tools=tool_registry.get_openai_schemas()
                )
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                return f"LLM 调用失败: {e}"

            # 更新 token 统计
            if response.usage:
                self.state.total_tokens["prompt"] += response.usage.get("prompt_tokens", 0)
                self.state.total_tokens["completion"] += response.usage.get("completion_tokens", 0)

            # 处理响应
            if response.content:
                if self.config.verbose:
                    console.print(Panel(
                        Markdown(response.content),
                        title="🤖 Assistant",
                        border_style="green"
                    ))

            # 没有工具调用，任务完成
            if not response.tool_calls:
                self.state.messages.append(Message(
                    role="assistant",
                    content=response.content
                ))
                return response.content

            # 添加 assistant 消息（包含工具调用）
            self.state.messages.append(Message(
                role="assistant",
                content=response.content,
                tool_calls=[{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": str(tc.arguments)
                    }
                } for tc in response.tool_calls]
            ))

            # 执行工具调用
            for tool_call in response.tool_calls:
                result = self._execute_tool(tool_call)

                # 添加工具结果消息
                result_content = result.output if result.success else f"Error: {result.error}"
                self.state.messages.append(Message(
                    role="tool",
                    content=result_content,
                    tool_call_id=tool_call.id
                ))

        # 达到最大迭代次数
        return "达到最大迭代次数，任务未完成"

    def get_artifacts(self) -> list[str]:
        """获取产生的文件列表"""
        return self.state.artifacts

    def get_token_usage(self) -> dict:
        """获取 token 使用统计"""
        return self.state.total_tokens
