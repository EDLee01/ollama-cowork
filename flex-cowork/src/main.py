"""FlexCowork 主入口"""
import argparse
import os
from pathlib import Path

from loguru import logger
from rich.console import Console

from .llm.providers import create_provider
from .agent.core import Agent, AgentConfig
from .tools.base import tool_registry
from .tools.file_tools import register_file_tools
from .tools.shell_tools import register_shell_tools
from .tools.web_tools import register_web_tools
from .tools.document_tools import register_document_tools


console = Console()


def setup_workspace(path: str) -> Path:
    """设置工作目录"""
    workspace = Path(path).absolute()
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def register_all_tools(workspace: str):
    """注册所有工具"""
    register_file_tools(workspace)
    register_shell_tools(workspace)
    register_web_tools()
    register_document_tools(workspace)
    logger.info(f"已注册 {len(tool_registry.list_tools())} 个工具")


def run_cli(args):
    """CLI 模式"""
    # 设置工作目录
    workspace = setup_workspace(args.workspace)
    register_all_tools(str(workspace))

    # 获取 API Key
    api_key_env = {
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }

    api_key = args.api_key or os.environ.get(api_key_env.get(args.provider, ""))
    if not api_key:
        console.print(f"[red]错误: 请提供 API Key (--api-key 或设置 {api_key_env.get(args.provider)})[/red]")
        return

    # 创建 LLM
    try:
        llm = create_provider(args.provider, api_key=api_key, model=args.model)
    except Exception as e:
        console.print(f"[red]创建 LLM 失败: {e}[/red]")
        return

    # 创建 Agent
    config = AgentConfig(
        max_iterations=args.max_iterations,
        verbose=True,
        auto_approve=args.auto_approve
    )

    agent = Agent(llm=llm, workspace=str(workspace), config=config)

    # 执行任务
    task = " ".join(args.task)
    if not task:
        console.print("[yellow]请提供任务描述[/yellow]")
        return

    console.print(f"\n[bold blue]🚀 FlexCowork[/bold blue] - {llm.get_model_name()}")
    console.print(f"[dim]工作目录: {workspace}[/dim]\n")

    result = agent.run(task)

    # 显示结果
    console.print("\n" + "=" * 50)
    usage = agent.get_token_usage()
    console.print(f"[dim]Token 使用: {usage['prompt']} + {usage['completion']} = {usage['prompt'] + usage['completion']}[/dim]")

    artifacts = agent.get_artifacts()
    if artifacts:
        console.print("\n[green]📁 产生的文件:[/green]")
        for a in artifacts:
            console.print(f"  - {a}")


def run_ui(args):
    """UI 模式"""
    from .ui.gradio_app import FlexCoworkUI

    console.print("[bold blue]🚀 FlexCowork Web UI[/bold blue]")
    console.print(f"[dim]启动中... http://{args.host}:{args.port}[/dim]\n")

    ui = FlexCoworkUI()
    ui.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share
    )


def main():
    parser = argparse.ArgumentParser(
        description="FlexCowork - 灵活的 AI Agent 系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Web UI 模式
  python -m src.main --mode ui

  # CLI 模式 (OpenAI)
  python -m src.main --provider openai "创建一个项目报告"

  # CLI 模式 (Claude)
  python -m src.main --provider claude --model claude-sonnet-4-20250514 "分析当前目录"

  # 使用自定义 API Key
  python -m src.main --provider deepseek --api-key sk-xxx "搜索最新新闻"
        """
    )

    parser.add_argument(
        "--mode",
        choices=["cli", "ui"],
        default="cli",
        help="运行模式: cli 或 ui (默认: cli)"
    )

    parser.add_argument(
        "--provider",
        choices=["openai", "claude", "gemini", "deepseek"],
        default="openai",
        help="LLM 提供商 (默认: openai)"
    )

    parser.add_argument(
        "--model",
        default=None,
        help="模型名称 (默认: 提供商的默认模型)"
    )

    parser.add_argument(
        "--api-key",
        default=None,
        help="API Key (也可通过环境变量设置)"
    )

    parser.add_argument(
        "--workspace",
        default="./workspace",
        help="工作目录 (默认: ./workspace)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=30,
        help="最大迭代次数 (默认: 30)"
    )

    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="自动批准危险操作"
    )

    # UI 模式参数
    parser.add_argument("--host", default="0.0.0.0", help="UI 监听地址")
    parser.add_argument("--port", type=int, default=7860, help="UI 端口")
    parser.add_argument("--share", action="store_true", help="创建公共链接")

    # 任务参数
    parser.add_argument("task", nargs="*", help="任务描述 (CLI 模式)")

    args = parser.parse_args()

    if args.mode == "ui":
        run_ui(args)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
