"""文档生成工具"""
from pathlib import Path
from .base import BaseTool, ToolResult, tool_registry


class CreateDocxTool(BaseTool):
    name = "create_docx"
    description = "创建 Word 文档（.docx）。支持标题、段落、列表"
    parameters_schema = {
        "filename": {
            "type": "string",
            "description": "文件名（不含扩展名）"
        },
        "content": {
            "type": "string",
            "description": "文档内容（Markdown 格式，会自动转换）"
        },
        "title": {
            "type": "string",
            "description": "文档标题"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, filename: str, content: str, title: str = "") -> ToolResult:
        try:
            from docx import Document
            from docx.shared import Pt, Inches

            doc = Document()

            # 添加标题
            if title:
                doc.add_heading(title, 0)

            # 简单的 Markdown 解析
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("# "):
                    doc.add_heading(line[2:], 1)
                elif line.startswith("## "):
                    doc.add_heading(line[3:], 2)
                elif line.startswith("### "):
                    doc.add_heading(line[4:], 3)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:], style="List Bullet")
                elif line[0].isdigit() and ". " in line[:4]:
                    doc.add_paragraph(line.split(". ", 1)[1], style="List Number")
                else:
                    doc.add_paragraph(line)

            # 保存文件
            filepath = self.workspace / f"{filename}.docx"
            doc.save(str(filepath))

            return ToolResult(
                success=True,
                output=f"已创建 Word 文档: {filename}.docx",
                artifacts=[str(filepath)]
            )
        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="缺少 python-docx 库，请安装: pip install python-docx"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class CreateXlsxTool(BaseTool):
    name = "create_xlsx"
    description = "创建 Excel 表格（.xlsx）。支持多工作表、数据写入"
    parameters_schema = {
        "filename": {
            "type": "string",
            "description": "文件名（不含扩展名）"
        },
        "data": {
            "type": "string",
            "description": "CSV 格式的数据，用逗号分隔列，换行分隔行"
        },
        "sheet_name": {
            "type": "string",
            "description": "工作表名称，默认 Sheet1"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, filename: str, data: str, sheet_name: str = "Sheet1") -> ToolResult:
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter

            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name

            # 解析 CSV 数据
            rows = data.strip().split("\n")
            for row_idx, row in enumerate(rows, 1):
                cells = row.split(",")
                for col_idx, cell in enumerate(cells, 1):
                    ws.cell(row=row_idx, column=col_idx, value=cell.strip())

            # 调整列宽
            for col_idx in range(1, ws.max_column + 1):
                ws.column_dimensions[get_column_letter(col_idx)].width = 15

            # 保存文件
            filepath = self.workspace / f"{filename}.xlsx"
            wb.save(str(filepath))

            return ToolResult(
                success=True,
                output=f"已创建 Excel 文件: {filename}.xlsx",
                artifacts=[str(filepath)]
            )
        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="缺少 openpyxl 库，请安装: pip install openpyxl"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class CreatePptxTool(BaseTool):
    name = "create_pptx"
    description = "创建 PowerPoint 演示文稿（.pptx）"
    parameters_schema = {
        "filename": {
            "type": "string",
            "description": "文件名（不含扩展名）"
        },
        "slides": {
            "type": "string",
            "description": "幻灯片内容，每张用 --- 分隔，第一行为标题，其余为内容"
        }
    }

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)

    def execute(self, filename: str, slides: str) -> ToolResult:
        try:
            from pptx import Presentation
            from pptx.util import Inches, Pt

            prs = Presentation()

            # 解析幻灯片内容
            slide_contents = slides.split("---")

            for slide_content in slide_contents:
                lines = [l.strip() for l in slide_content.strip().split("\n") if l.strip()]
                if not lines:
                    continue

                title = lines[0].lstrip("#").strip()
                body = "\n".join(lines[1:]) if len(lines) > 1 else ""

                # 添加幻灯片
                slide_layout = prs.slide_layouts[1]  # Title and Content
                slide = prs.slides.add_slide(slide_layout)

                slide.shapes.title.text = title
                if body and slide.placeholders[1]:
                    slide.placeholders[1].text = body

            # 保存文件
            filepath = self.workspace / f"{filename}.pptx"
            prs.save(str(filepath))

            return ToolResult(
                success=True,
                output=f"已创建 PPT 文件: {filename}.pptx，共 {len(prs.slides)} 张幻灯片",
                artifacts=[str(filepath)]
            )
        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="缺少 python-pptx 库，请安装: pip install python-pptx"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


def register_document_tools(workspace: str):
    """注册文档工具"""
    tool_registry.register(CreateDocxTool(workspace))
    tool_registry.register(CreateXlsxTool(workspace))
    tool_registry.register(CreatePptxTool(workspace))
