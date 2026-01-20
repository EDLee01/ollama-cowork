"""Shell 命令执行工具"""
import subprocess
import sys
from pathlib import Path
from .base import BaseTool, ToolResult, tool_registry


# 危险命令黑名单
DANGEROUS_COMMANDS = [
    "rm -rf /", "rm -rf ~", "rm -rf *",
    "mkfs", "dd if=", ":(){:|:&};:",
    "chmod -R 777 /", "chown -R",
    "> /dev/sda", "mv ~ /dev/null"
]


class ExecuteShellTool(BaseTool):
    name = "execute_shell"
    description = "执行 Shell 命令（在工作目录中）"
    parameters_schema = {
        "command": {"type": "string", "description": "要执行的命令"},
        "timeout": {"type": "integer", "description": "超时时间（秒），默认30", "optional": True}
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, command: str, timeout: int = 30) -> ToolResult:
        # 危险命令检查
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                return ToolResult(False, "", f"拒绝执行危险命令: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error="" if result.returncode == 0 else f"退出码: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"命令执行超时（{timeout}秒）")
        except Exception as e:
            return ToolResult(False, "", str(e))


class ExecutePythonTool(BaseTool):
    name = "execute_python"
    description = "执行 Python 代码片段"
    parameters_schema = {
        "code": {"type": "string", "description": "要执行的 Python 代码"},
        "timeout": {"type": "integer", "description": "超时时间（秒），默认30", "optional": True}
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, code: str, timeout: int = 30) -> ToolResult:
        try:
            # 创建临时脚本文件
            script_path = self.workspace / "_temp_script.py"
            script_path.write_text(code, encoding="utf-8")

            try:
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                output = result.stdout
                if result.stderr:
                    output += f"\n[stderr]: {result.stderr}"

                return ToolResult(
                    success=result.returncode == 0,
                    output=output,
                    error="" if result.returncode == 0 else f"退出码: {result.returncode}"
                )
            finally:
                # 清理临时文件
                if script_path.exists():
                    script_path.unlink()

        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"代码执行超时（{timeout}秒）")
        except Exception as e:
            return ToolResult(False, "", str(e))


def register_shell_tools(workspace: str):
    """注册 Shell 工具"""
    tool_registry.register(ExecuteShellTool(workspace))
    tool_registry.register(ExecutePythonTool(workspace))
