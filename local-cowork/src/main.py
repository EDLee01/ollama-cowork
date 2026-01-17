"""LocalCowork 主入口"""
import argparse
from pathlib import Path
from loguru import logger

from .llm.ollama_client import OllamaClient
from .agent.core import Agent, AgentConfig
from .tools.base import tool_registry
from .tools.file_tools import register_file_tools
from .tools.shell_tools import register_shell_tools
from .tools.web_tools import register_web_tools
from .tools.document_tools import register_document_tools
from .skills.loader import SkillLoader


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level,
        colorize=True
    )


def main():
    parser = argparse.ArgumentParser(description="LocalCowork - 本地 AI Agent")
    parser.add_argument("--mode", choices=["cli", "ui"], default="cli", help="运行模式")
    parser.add_argument("--workspace", default="./workspace", help="工作目录")
    parser.add_argument("--model", default="qwen2.5-coder:32b", help="Ollama 模型")
    parser.add_argument("--auto-approve", action="store_true", help="自动批准危险操作")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    parser.add_argument("task", nargs="?", help="要执行的任务（CLI 模式）")

    args = parser.parse_args()

    setup_logging(args.verbose)

    # 确保工作目录存在
    workspace = Path(args.workspace).absolute()
    workspace.mkdir(parents=True, exist_ok=True)

    # 注册工具
    workspace_str = str(workspace)
    register_file_tools(workspace_str)
    register_shell_tools(workspace_str)
    register_web_tools()
    register_document_tools(workspace_str)

    # 加载 Skills
    skill_loader = SkillLoader("skills")
    skill_loader.load_all()

    if args.mode == "ui":
        # Web UI 模式
        from .ui.gradio_app import LocalCoworkUI
        ui = LocalCoworkUI()
        ui.launch(server_name="0.0.0.0", server_port=7860)
    else:
        # CLI 模式
        if not args.task:
            print("请输入任务，或使用 --mode ui 启动 Web 界面")
            return

        # 创建 LLM 客户端
        llm = OllamaClient(model=args.model)

        # 创建 Agent
        config = AgentConfig(
            auto_approve=args.auto_approve,
            verbose=args.verbose
        )

        agent = Agent(llm=llm, workspace=workspace_str, config=config)

        # 执行任务
        result = agent.run(args.task)

        print("\n" + "=" * 60)
        print("📋 最终结果:")
        print(result)

        artifacts = agent.get_artifacts()
        if artifacts:
            print("\n📁 产生的文件:")
            for a in artifacts:
                print(f"  - {a}")


if __name__ == "__main__":
    main()
