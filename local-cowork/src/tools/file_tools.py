"""文件操作工具"""
import os
import shutil
from pathlib import Path
from .base import BaseTool, ToolResult, tool_registry


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "读取文件内容。支持文本文件（.txt, .md, .py, .json 等）"
    parameters_schema = {
        "path": {
            "type": "string",
            "description": "文件路径（相对于工作目录）"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str) -> ToolResult:
        try:
            file_path = self.workspace / path

            # 安全检查：确保路径在 workspace 内
            if not file_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(
                    success=False,
                    output="",
                    error="安全错误：不允许访问工作目录之外的文件"
                )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"文件不存在: {path}"
                )

            content = file_path.read_text(encoding="utf-8")
            return ToolResult(
                success=True,
                output=content
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入内容到文件。如果文件不存在则创建，存在则覆盖"
    parameters_schema = {
        "path": {
            "type": "string",
            "description": "文件路径（相对于工作目录）"
        },
        "content": {
            "type": "string",
            "description": "要写入的内容"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str, content: str) -> ToolResult:
        try:
            file_path = self.workspace / path

            # 安全检查
            if not file_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(
                    success=False,
                    output="",
                    error="安全错误：不允许访问工作目录之外的文件"
                )

            # 创建父目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"已写入文件: {path}",
                artifacts=[str(file_path)]
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "列出目录内容，包括文件和子目录"
    parameters_schema = {
        "path": {
            "type": "string",
            "description": "目录路径（相对于工作目录），默认为当前目录"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str = ".") -> ToolResult:
        try:
            dir_path = self.workspace / path

            # 安全检查
            if not dir_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(
                    success=False,
                    output="",
                    error="安全错误：不允许访问工作目录之外的目录"
                )

            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"目录不存在: {path}"
                )

            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "📁" if item.is_dir() else "📄"
                size = item.stat().st_size if item.is_file() else "-"
                items.append(f"{item_type} {item.name:<40} {size:>10}")

            output = f"目录: {path}\n" + "-" * 60 + "\n" + "\n".join(items)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "移动或重命名文件/目录"
    parameters_schema = {
        "source": {
            "type": "string",
            "description": "源路径"
        },
        "destination": {
            "type": "string",
            "description": "目标路径"
        }
    }
    requires_confirmation = True

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, source: str, destination: str) -> ToolResult:
        try:
            src_path = self.workspace / source
            dst_path = self.workspace / destination

            # 安全检查
            for p in [src_path, dst_path]:
                if not p.resolve().is_relative_to(self.workspace.resolve()):
                    return ToolResult(
                        success=False,
                        output="",
                        error="安全错误：不允许访问工作目录之外的文件"
                    )

            shutil.move(str(src_path), str(dst_path))
            return ToolResult(
                success=True,
                output=f"已移动: {source} -> {destination}"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "删除文件或空目录"
    parameters_schema = {
        "path": {
            "type": "string",
            "description": "要删除的文件/目录路径"
        }
    }
    requires_confirmation = True  # 删除操作需要确认

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, path: str) -> ToolResult:
        try:
            file_path = self.workspace / path

            # 安全检查
            if not file_path.resolve().is_relative_to(self.workspace.resolve()):
                return ToolResult(
                    success=False,
                    output="",
                    error="安全错误：不允许访问工作目录之外的文件"
                )

            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                file_path.rmdir()  # 只删除空目录
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"路径不存在: {path}"
                )

            return ToolResult(
                success=True,
                output=f"已删除: {path}"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


def register_file_tools(workspace: str):
    """注册所有文件工具"""
    tool_registry.register(ReadFileTool(workspace))
    tool_registry.register(WriteFileTool(workspace))
    tool_registry.register(ListDirectoryTool(workspace))
    tool_registry.register(MoveFileTool(workspace))
    tool_registry.register(DeleteFileTool(workspace))
