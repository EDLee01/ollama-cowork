"""Agent 核心循环"""
import json
import re
from typing import Optional, Callable
from dataclasses import dataclass, field
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ..llm.ollama_client import OllamaClient, Message
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
    task: str
    messages: list[Message] = field(default_factory=list)
    iteration: int = 0
    completed: bool = False
    artifacts: list[str] = field(default_factory=list)


class Agent:
    """LocalCowork Agent 核心"""

    def __init__(
        self,
        llm: OllamaClient,
        workspace: str,
        config: Optional[AgentConfig] = None,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ):
        self.llm = llm
        self.workspace = workspace
        self.config = config or AgentConfig()
        self.confirm_callback = confirm_callback or self._default_confirm
        self.state: Optional[AgentState] = None

    def _default_confirm(self, message: str) -> bool:
        """默认确认回调"""
        response = input(f"\n⚠️  {message} [y/N]: ")
        return response.lower() in ["y", "yes"]

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return AGENT_SYSTEM_PROMPT.format(
            tools_description=tool_registry.get_descriptions(),
            workspace_path=self.workspace,
            skills_description="暂无加载的 Skills"
        )

    def _parse_tool_call(self, content: str) -> Optional[tuple[str, dict]]:
        """从 LLM 输出中解析工具调用"""
        # 尝试解析结构化格式
        # 格式: 工具：xxx\n参数：\n```json\n{...}\n```

        tool_match = re.search(r"工具[：:]\s*(\w+)", content)
        if not tool_match:
            return None

        tool_name = tool_match.group(1)

        # 解析 JSON 参数
        json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        if json_match:
            try:
                params = json.loads(json_match.group(1))
                return tool_name, params
            except json.JSONDecodeError:
                pass

        # 尝试直接解析 JSON
        json_match = re.search(r"\{[^{}]*\}", content)
        if json_match:
            try:
                params = json.loads(json_match.group(0))
                return tool_name, params
            except json.JSONDecodeError:
                pass

        return tool_name, {}

    def _execute_tool(self, tool_name: str, params: dict) -> ToolResult:
        """执行工具"""
        tool = tool_registry.get(tool_name)

        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"未知工具: {tool_name}"
            )

        # 需要确认的工具
        if tool.requires_confirmation and not self.config.auto_approve:
            confirm_msg = f"即将执行 {tool_name}，参数: {json.dumps(params, ensure_ascii=False)}"
            if not self.confirm_callback(confirm_msg):
                return ToolResult(
                    success=False,
                    output="",
                    error="用户取消执行"
                )

        # 执行工具
        try:
            result = tool.execute(**params)
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"工具执行异常: {str(e)}"
            )

    def _display_step(self, step_type: str, content: str):
        """显示执行步骤"""
        if not self.config.verbose:
            return

        styles = {
            "thinking": ("blue", "🤔 思考"),
            "tool": ("yellow", "🔧 工具"),
            "result": ("green", "✅ 结果"),
            "error": ("red", "❌ 错误"),
            "summary": ("cyan", "📋 总结"),
        }

        color, title = styles.get(step_type, ("white", step_type))
        console.print(Panel(content, title=title, border_style=color))

    def run(self, task: str) -> str:
        """执行任务"""
        self.state = AgentState(task=task)

        # 初始化消息
        system_prompt = self._build_system_prompt()
        self.state.messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=task)
        ]

        console.print(f"\n[bold green]📝 任务:[/] {task}\n")

        while self.state.iteration < self.config.max_iterations:
            self.state.iteration += 1
            logger.info(f"迭代 {self.state.iteration}/{self.config.max_iterations}")

            # 调用 LLM
            try:
                response = self.llm.chat(
                    messages=self.state.messages,
                    tools=tool_registry.get_schemas()
                )
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                break

            content = response.content
            self.state.messages.append(Message(role="assistant", content=content))

            # 检查是否完成
            if "总结：" in content or "总结:" in content:
                self._display_step("summary", content)
                self.state.completed = True
                break

            # 解析工具调用
            tool_call = self._parse_tool_call(content)

            if tool_call:
                tool_name, params = tool_call
                self._display_step("thinking", content.split("工具")[0])
                self._display_step("tool", f"{tool_name}\n{json.dumps(params, ensure_ascii=False, indent=2)}")

                # 执行工具
                result = self._execute_tool(tool_name, params)

                if result.success:
                    self._display_step("result", result.output[:500])
                    self.state.artifacts.extend(result.artifacts)
                else:
                    self._display_step("error", result.error or "未知错误")

                # 将结果添加到消息
                result_msg = f"工具执行结果:\n成功: {result.success}\n输出: {result.output}"
                if result.error:
                    result_msg += f"\n错误: {result.error}"

                self.state.messages.append(Message(role="user", content=result_msg))
            else:
                # 没有工具调用，可能是中间思考
                self._display_step("thinking", content)

        # 返回最终结果
        if self.state.completed:
            return content
        else:
            return "任务未能在最大迭代次数内完成"

    def get_artifacts(self) -> list[str]:
        """获取产生的文件列表"""
        return self.state.artifacts if self.state else []
