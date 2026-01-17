"""Gradio Web 界面"""
import gradio as gr
from pathlib import Path
from typing import Generator
import threading
import queue

from ..agent.core import Agent, AgentConfig
from ..llm.ollama_client import OllamaClient
from ..tools.base import tool_registry
from ..tools.file_tools import register_file_tools
from ..tools.shell_tools import register_shell_tools
from ..tools.web_tools import register_web_tools
from ..tools.document_tools import register_document_tools


class LocalCoworkUI:
    """LocalCowork Web 界面"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.workspace = Path("./workspace").absolute()
        self.workspace.mkdir(exist_ok=True)

        # 初始化 LLM
        self.llm = OllamaClient(
            model="qwen2.5-coder:32b",
            api_base="http://localhost:11434"
        )

        # 注册工具
        self._register_tools()

        # 消息队列用于流式输出
        self.output_queue = queue.Queue()

    def _register_tools(self):
        """注册所有工具"""
        workspace_str = str(self.workspace)
        register_file_tools(workspace_str)
        register_shell_tools(workspace_str)
        register_web_tools()
        register_document_tools(workspace_str)

    def _confirm_callback(self, message: str) -> bool:
        """确认回调 - Web 版暂时自动确认"""
        return True

    def execute_task(
        self,
        task: str,
        auto_approve: bool,
        history: list
    ) -> Generator:
        """执行任务"""
        if not task.strip():
            yield history + [[task, "请输入任务描述"]], ""
            return

        # 创建 Agent
        config = AgentConfig(
            max_iterations=30,
            verbose=True,
            auto_approve=auto_approve
        )

        agent = Agent(
            llm=self.llm,
            workspace=str(self.workspace),
            config=config,
            confirm_callback=self._confirm_callback
        )

        # 执行并更新历史
        history = history + [[task, ""]]

        try:
            result = agent.run(task)
            history[-1][1] = result

            # 获取产生的文件
            artifacts = agent.get_artifacts()
            artifacts_text = ""
            if artifacts:
                artifacts_text = "📁 产生的文件:\n" + "\n".join(f"- {a}" for a in artifacts)

            yield history, artifacts_text
        except Exception as e:
            history[-1][1] = f"❌ 执行失败: {str(e)}"
            yield history, ""

    def list_workspace_files(self) -> str:
        """列出工作区文件"""
        files = []
        for item in self.workspace.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(self.workspace)
                size = item.stat().st_size
                files.append(f"📄 {rel_path} ({size} bytes)")

        if not files:
            return "工作区为空"
        return "\n".join(files[:50])  # 限制显示数量

    def upload_file(self, file) -> str:
        """上传文件到工作区"""
        if file is None:
            return "请选择文件"

        dest = self.workspace / Path(file.name).name
        with open(dest, "wb") as f:
            f.write(file.read())

        return f"✅ 已上传: {dest.name}"

    def build_ui(self) -> gr.Blocks:
        """构建 Gradio 界面"""
        with gr.Blocks(
            title="LocalCowork",
            theme=gr.themes.Soft()
        ) as app:
            gr.Markdown("# 🤖 LocalCowork - 本地 AI Agent")
            gr.Markdown("基于 Ollama 的本地 AI 助手，可以操作文件、执行命令、创建文档")

            with gr.Row():
                # 左侧：聊天区域
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        label="对话历史",
                        height=500,
                        show_copy_button=True
                    )

                    with gr.Row():
                        task_input = gr.Textbox(
                            label="任务描述",
                            placeholder="例如：整理当前目录的文件，按类型分类",
                            lines=2,
                            scale=4
                        )
                        submit_btn = gr.Button("🚀 执行", variant="primary", scale=1)

                    with gr.Row():
                        auto_approve = gr.Checkbox(
                            label="自动批准危险操作",
                            value=False
                        )
                        clear_btn = gr.Button("🗑️ 清空对话")

                # 右侧：工作区和设置
                with gr.Column(scale=1):
                    with gr.Tab("📁 工作区"):
                        workspace_display = gr.Textbox(
                            label=f"工作目录: {self.workspace}",
                            value=self.list_workspace_files(),
                            lines=15,
                            interactive=False
                        )
                        refresh_btn = gr.Button("🔄 刷新")

                        gr.Markdown("### 上传文件")
                        upload = gr.File(label="选择文件")
                        upload_status = gr.Textbox(label="上传状态", interactive=False)

                    with gr.Tab("🔧 工具"):
                        tools_display = gr.Markdown(
                            value=self._get_tools_markdown()
                        )

                    with gr.Tab("📊 输出"):
                        artifacts_display = gr.Textbox(
                            label="产生的文件",
                            lines=10,
                            interactive=False
                        )

            # 事件绑定
            submit_btn.click(
                fn=self.execute_task,
                inputs=[task_input, auto_approve, chatbot],
                outputs=[chatbot, artifacts_display]
            )

            task_input.submit(
                fn=self.execute_task,
                inputs=[task_input, auto_approve, chatbot],
                outputs=[chatbot, artifacts_display]
            )

            clear_btn.click(
                fn=lambda: ([], ""),
                outputs=[chatbot, artifacts_display]
            )

            refresh_btn.click(
                fn=self.list_workspace_files,
                outputs=[workspace_display]
            )

            upload.change(
                fn=self.upload_file,
                inputs=[upload],
                outputs=[upload_status]
            ).then(
                fn=self.list_workspace_files,
                outputs=[workspace_display]
            )

        return app

    def _get_tools_markdown(self) -> str:
        """获取工具列表 Markdown"""
        lines = ["## 可用工具\n"]
        for tool in tool_registry.list_tools():
            lines.append(f"### 🔧 {tool.name}")
            lines.append(f"{tool.description}\n")
            if tool.requires_confirmation:
                lines.append("⚠️ *需要用户确认*\n")
        return "\n".join(lines)

    def launch(self, **kwargs):
        """启动应用"""
        app = self.build_ui()
        app.launch(**kwargs)


def main():
    ui = LocalCoworkUI()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
