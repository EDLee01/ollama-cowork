"""Shell 命令执行工具"""
import subprocess
import shlex
from typing import Optional
from .base import BaseTool, ToolResult, tool_registry


# 禁止执行的危险命令
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf /*",
    "mkfs",
    "dd if=/dev/zero",
    ":(){:|:&};:",  # Fork bomb
    "chmod -R 777 /",
    "wget | bash",
    "curl | bash",
]

# 允许的命令白名单（可选，更严格的模式）
ALLOWED_COMMANDS = [
    "ls", "cat", "head", "tail", "grep", "find", "wc",
    "sort", "uniq", "cut", "awk", "sed",
    "python", "python3", "pip", "pip3",
    "node", "npm", "npx",
    "git", "echo", "date", "pwd", "env",
    "mkdir", "touch", "cp", "mv",
]


class ShellTool(BaseTool):
    name = "run_shell"
    description = "在沙盒环境中执行 Shell 命令。支持常用的 Linux 命令"
    parameters_schema = {
        "command": {
            "type": "string",
            "description": "要执行的 Shell 命令"
        },
        "timeout": {
            "type": "integer",
            "description": "超时时间（秒），默认 30"
        }
    }
    requires_confirmation = True

    def __init__(self, workspace: str, use_whitelist: bool = False):
        self.workspace = workspace
        self.use_whitelist = use_whitelist

    def _is_dangerous(self, command: str) -> bool:
        """检查是否是危险命令"""
        cmd_lower = command.lower().strip()

        # 检查危险命令列表
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in cmd_lower:
                return True

        # 检查是否包含危险模式
        dangerous_patterns = [
            "rm -rf",
            "rm -r /",
            "> /dev/",
            "| sh",
            "| bash",
            "sudo",
            "su -",
        ]
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                return True

        return False

    def _is_allowed(self, command: str) -> bool:
        """检查命令是否在白名单中"""
        if not self.use_whitelist:
            return True

        # 获取命令的第一个词
        try:
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return False
            base_cmd = cmd_parts[0].split("/")[-1]  # 处理 /usr/bin/python 这样的路径
            return base_cmd in ALLOWED_COMMANDS
        except:
            return False

    def execute(self, command: str, timeout: int = 30) -> ToolResult:
        # 安全检查
        if self._is_dangerous(command):
            return ToolResult(
                success=False,
                output="",
                error=f"安全错误：检测到危险命令，拒绝执行: {command}"
            )

        if not self._is_allowed(command):
            return ToolResult(
                success=False,
                output="",
                error=f"安全错误：命令不在允许列表中: {command}"
            )

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
                output += f"\n[STDERR]\n{result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"命令返回码: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"命令执行超时（{timeout}秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class PythonTool(BaseTool):
    name = "run_python"
    description = "执行 Python 代码。适合数据处理、文件操作、复杂计算"
    parameters_schema = {
        "code": {
            "type": "string",
            "description": "要执行的 Python 代码"
        }
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = workspace

    def execute(self, code: str) -> ToolResult:
        try:
            # 将代码写入临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                dir=self.workspace,
                delete=False
            ) as f:
                f.write(code)
                script_path = f.name

            # 执行脚本
            result = subprocess.run(
                ["python3", script_path],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=60
            )

            # 清理临时文件
            import os
            os.unlink(script_path)

            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"执行失败"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Python 脚本执行超时（60秒）"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


def register_shell_tools(workspace: str):
    """注册 Shell 工具"""
    tool_registry.register(ShellTool(workspace))
    tool_registry.register(PythonTool(workspace))
