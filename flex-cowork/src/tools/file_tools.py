"""文件操作工具"""
import os
import shutil
from pathlib import Path
from .base import BaseTool, ToolResult, tool_registry


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取文件内容"
    parameters_schema = {
        "path": {"type": "string", "description": "文件路径（相对于工作目录）"}
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str) -> ToolResult:
        try:
            file_path = self.workspace / path
            if not file_path.exists():
                return ToolResult(False, "", f"文件不存在: {path}")

            # 安全检查
            if not file_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(False, "", "不允许访问工作目录外的文件")

            content = file_path.read_text(encoding="utf-8")
            return ToolResult(True, content)
        except Exception as e:
            return ToolResult(False, "", str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入文件内容（会覆盖已存在的文件）"
    parameters_schema = {
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "要写入的内容"}
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str, content: str) -> ToolResult:
        try:
            file_path = self.workspace / path
            if not file_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(False, "", "不允许写入工作目录外的文件")

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult(True, f"已写入文件: {path}", artifacts=[str(file_path)])
        except Exception as e:
            return ToolResult(False, "", str(e))


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "列出目录内容"
    parameters_schema = {
        "path": {"type": "string", "description": "目录路径，默认为当前工作目录", "optional": True}
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str = ".") -> ToolResult:
        try:
            dir_path = self.workspace / path
            if not dir_path.exists():
                return ToolResult(False, "", f"目录不存在: {path}")

            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "📁" if item.is_dir() else "📄"
                size = f"({item.stat().st_size} bytes)" if item.is_file() else ""
                items.append(f"{prefix} {item.name} {size}")

            return ToolResult(True, "\n".join(items) if items else "(空目录)")
        except Exception as e:
            return ToolResult(False, "", str(e))


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "移动或重命名文件"
    parameters_schema = {
        "source": {"type": "string", "description": "源文件路径"},
        "destination": {"type": "string", "description": "目标路径"}
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, source: str, destination: str) -> ToolResult:
        try:
            src = self.workspace / source
            dst = self.workspace / destination

            if not src.exists():
                return ToolResult(False, "", f"源文件不存在: {source}")

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return ToolResult(True, f"已移动: {source} -> {destination}")
        except Exception as e:
            return ToolResult(False, "", str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "删除文件或目录"
    parameters_schema = {
        "path": {"type": "string", "description": "要删除的路径"}
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str) -> ToolResult:
        try:
            target = self.workspace / path
            if not target.exists():
                return ToolResult(False, "", f"路径不存在: {path}")

            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)

            return ToolResult(True, f"已删除: {path}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def register_file_tools(workspace: str):
    """注册文件工具"""
    tool_registry.register(ReadFileTool(workspace))
    tool_registry.register(WriteFileTool(workspace))
    tool_registry.register(ListDirectoryTool(workspace))
    tool_registry.register(MoveFileTool(workspace))
    tool_registry.register(DeleteFileTool(workspace))
