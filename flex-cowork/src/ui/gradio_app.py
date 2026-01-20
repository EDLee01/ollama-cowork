"""Gradio Web 界面 - 支持多提供商选择"""
import os
import gradio as gr
from pathlib import Path
from typing import Generator, Optional

from ..agent.core import Agent, AgentConfig
from ..llm.providers import create_provider, PROVIDERS
from ..tools.base import tool_registry
from ..tools.file_tools import register_file_tools
from ..tools.shell_tools import register_shell_tools
from ..tools.web_tools import register_web_tools
from ..tools.document_tools import register_document_tools


# 提供商和默认模型
PROVIDER_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "claude": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
    "deepseek": ["deepseek-chat", "deepseek-coder"],
}

# API Key 环境变量名
API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


class FlexCoworkUI:
    """FlexCowork Web 界面"""

    def __init__(self):
        self.workspace = Path("./workspace").absolute()
        self.workspace.mkdir(exist_ok=True)
        self.current_provider = None
        self.current_model = None

        # 注册工具
        self._register_tools()

    def _register_tools(self):
        """注册所有工具"""
        workspace_str = str(self.workspace)
        register_file_tools(workspace_str)
        register_shell_tools(workspace_str)
        register_web_tools()
        register_document_tools(workspace_str)

    def _get_api_key(self, provider: str, custom_key: str) -> Optional[str]:
        """获取 API Key"""
        if custom_key.strip():
            return custom_key.strip()
        return os.environ.get(API_KEY_ENV.get(provider, ""))

    def execute_task(
        self,
        task: str,
        provider: str,
        model: str,
        api_key: str,
        auto_approve: bool,
        temperature: float,
        history: list
    ) -> Generator:
        """执行任务"""
        if not task.strip():
            yield history + [[task, "❌ 请输入任务描述"]], "", ""
            return

        # 获取 API Key
        key = self._get_api_key(provider, api_key)
        if not key:
            env_name = API_KEY_ENV.get(provider, "API_KEY")
            yield history + [[task, f"❌ 请提供 API Key（或设置环境变量 {env_name}）"]], "", ""
            return

        # 创建 LLM 提供商
        try:
            llm = create_provider(provider, api_key=key, model=model)
        except Exception as e:
            yield history + [[task, f"❌ 创建 LLM 失败: {e}"]], "", ""
            return

        # 创建 Agent
        config = AgentConfig(
            max_iterations=30,
            verbose=False,  # UI 模式下不使用 console 输出
            auto_approve=auto_approve
        )

        agent = Agent(
            llm=llm,
            workspace=str(self.workspace),
            config=config,
            confirm_callback=lambda msg: auto_approve
        )

        # 更新历史
        history = history + [[task, "⏳ 正在处理..."]]
        yield history, "", ""

        # 执行
        try:
            result = agent.run(task)
            history[-1][1] = result

            # 统计信息
            usage = agent.get_token_usage()
            stats = f"📊 Token: {usage['prompt']} + {usage['completion']} = {usage['prompt'] + usage['completion']}"

            # 产生的文件
            artifacts = agent.get_artifacts()
            artifacts_text = ""
            if artifacts:
                artifacts_text = "📁 产生的文件:\n" + "\n".join(f"- {Path(a).name}" for a in artifacts)

            yield history, artifacts_text, stats
        except Exception as e:
            history[-1][1] = f"❌ 执行失败: {str(e)}"
            yield history, "", ""

    def update_models(self, provider: str):
        """更新模型下拉框"""
        models = PROVIDER_MODELS.get(provider, ["default"])
        return gr.update(choices=models, value=models[0])

    def list_workspace_files(self) -> str:
        """列出工作区文件"""
        files = []
        for item in self.workspace.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(self.workspace)
                size = item.stat().st_size
                if size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                files.append(f"📄 {rel_path} ({size_str})")

        return "\n".join(files[:50]) if files else "📁 工作区为空"

    def upload_file(self, file) -> tuple[str, str]:
        """上传文件"""
        if file is None:
            return "请选择文件", self.list_workspace_files()

        dest = self.workspace / Path(file.name).name
        with open(dest, "wb") as f:
            f.write(file.read())

        return f"✅ 已上传: {dest.name}", self.list_workspace_files()

    def _get_tools_markdown(self) -> str:
        """获取工具列表"""
        lines = ["| 工具 | 功能 | 需确认 |", "|------|------|--------|"]
        for tool in tool_registry.list_tools():
            confirm = "⚠️" if tool.requires_confirmation else "✓"
            lines.append(f"| `{tool.name}` | {tool.description} | {confirm} |")
        return "\n".join(lines)

    def build_ui(self) -> gr.Blocks:
        """构建界面"""
        with gr.Blocks(
            title="FlexCowork",
            theme=gr.themes.Soft(),
            css="""
            .provider-row { margin-bottom: 10px; }
            .stats-text { font-family: monospace; }
            """
        ) as app:
            gr.Markdown("""
            # 🚀 FlexCowork
            **灵活的 AI Agent 系统** - 支持 OpenAI / Claude / Gemini / DeepSeek
            """)

            with gr.Row():
                # 左侧：聊天和设置
                with gr.Column(scale=2):
                    # 提供商设置
                    with gr.Row(elem_classes="provider-row"):
                        provider = gr.Dropdown(
                            label="🔌 提供商",
                            choices=list(PROVIDER_MODELS.keys()),
                            value="openai",
                            scale=1
                        )
                        model = gr.Dropdown(
                            label="🤖 模型",
                            choices=PROVIDER_MODELS["openai"],
                            value="gpt-4o",
                            scale=1
                        )
                        api_key = gr.Textbox(
                            label="🔑 API Key (可选，优先使用环境变量)",
                            type="password",
                            placeholder="sk-... 或留空使用环境变量",
                            scale=2
                        )

                    # 聊天区域
                    chatbot = gr.Chatbot(
                        label="对话",
                        height=450,
                        show_copy_button=True
                    )

                    # 输入区域
                    with gr.Row():
                        task_input = gr.Textbox(
                            label="任务描述",
                            placeholder="例如：创建一个项目进度报告的 Word 文档...",
                            lines=2,
                            scale=4
                        )
                        submit_btn = gr.Button("🚀 执行", variant="primary", scale=1)

                    # 选项
                    with gr.Row():
                        auto_approve = gr.Checkbox(label="自动批准危险操作", value=False)
                        temperature = gr.Slider(
                            label="Temperature",
                            minimum=0,
                            maximum=1,
                            value=0.7,
                            step=0.1
                        )
                        clear_btn = gr.Button("🗑️ 清空")

                    # 统计信息
                    stats_display = gr.Textbox(
                        label="统计",
                        interactive=False,
                        elem_classes="stats-text"
                    )

                # 右侧：工作区和工具
                with gr.Column(scale=1):
                    with gr.Tab("📁 工作区"):
                        workspace_display = gr.Textbox(
                            label=f"目录: {self.workspace}",
                            value=self.list_workspace_files(),
                            lines=12,
                            interactive=False
                        )
                        refresh_btn = gr.Button("🔄 刷新")

                        gr.Markdown("### 上传文件")
                        upload = gr.File(label="选择文件")
                        upload_status = gr.Textbox(label="状态", interactive=False)

                    with gr.Tab("📂 文件输出"):
                        artifacts_display = gr.Textbox(
                            label="产生的文件",
                            lines=10,
                            interactive=False
                        )

                    with gr.Tab("🔧 工具列表"):
                        gr.Markdown(self._get_tools_markdown())

            # 事件绑定
            provider.change(
                fn=self.update_models,
                inputs=[provider],
                outputs=[model]
            )

            submit_btn.click(
                fn=self.execute_task,
                inputs=[task_input, provider, model, api_key, auto_approve, temperature, chatbot],
                outputs=[chatbot, artifacts_display, stats_display]
            )

            task_input.submit(
                fn=self.execute_task,
                inputs=[task_input, provider, model, api_key, auto_approve, temperature, chatbot],
                outputs=[chatbot, artifacts_display, stats_display]
            )

            clear_btn.click(
                fn=lambda: ([], "", ""),
                outputs=[chatbot, artifacts_display, stats_display]
            )

            refresh_btn.click(
                fn=self.list_workspace_files,
                outputs=[workspace_display]
            )

            upload.change(
                fn=self.upload_file,
                inputs=[upload],
                outputs=[upload_status, workspace_display]
            )

        return app

    def launch(self, **kwargs):
        """启动应用"""
        app = self.build_ui()
        app.launch(**kwargs)


def main():
    ui = FlexCoworkUI()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
