#!/bin/bash

# FlexCowork 启动脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 FlexCowork - 灵活的 AI Agent 系统${NC}"

# 安装依赖
install_deps() {
    if [ ! -d "venv" ]; then
        echo -e "${GREEN}📦 创建虚拟环境...${NC}"
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt
}

# 检查 API Key
check_api_keys() {
    echo -e "${YELLOW}📋 API Key 状态:${NC}"

    [ -n "$OPENAI_API_KEY" ] && echo "  ✓ OPENAI_API_KEY 已设置" || echo "  ○ OPENAI_API_KEY 未设置"
    [ -n "$ANTHROPIC_API_KEY" ] && echo "  ✓ ANTHROPIC_API_KEY 已设置" || echo "  ○ ANTHROPIC_API_KEY 未设置"
    [ -n "$GOOGLE_API_KEY" ] && echo "  ✓ GOOGLE_API_KEY 已设置" || echo "  ○ GOOGLE_API_KEY 未设置"
    [ -n "$DEEPSEEK_API_KEY" ] && echo "  ✓ DEEPSEEK_API_KEY 已设置" || echo "  ○ DEEPSEEK_API_KEY 未设置"
    echo ""
}

# 显示帮助
show_help() {
    echo "用法: ./run.sh [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  ui              启动 Web 界面 (默认)"
    echo "  cli <任务>      命令行模式执行任务"
    echo "  setup           仅安装依赖"
    echo "  help            显示帮助"
    echo ""
    echo "选项 (CLI 模式):"
    echo "  --provider      提供商: openai, claude, gemini, deepseek (默认: openai)"
    echo "  --model         模型名称"
    echo "  --api-key       API Key"
    echo ""
    echo "示例:"
    echo "  ./run.sh ui"
    echo "  ./run.sh cli --provider claude \"创建项目报告\""
    echo "  OPENAI_API_KEY=sk-xxx ./run.sh cli \"分析代码\""
}

# 主逻辑
main() {
    case "${1:-ui}" in
        ui)
            install_deps
            check_api_keys
            echo -e "${GREEN}🌐 启动 Web 界面 http://localhost:7860${NC}"
            python -m src.main --mode ui
            ;;
        cli)
            install_deps
            shift
            python -m src.main --mode cli "$@"
            ;;
        setup)
            install_deps
            echo -e "${GREEN}✓ 依赖安装完成${NC}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            # 如果第一个参数不是命令，当作任务处理
            install_deps
            python -m src.main --mode cli "$@"
            ;;
    esac
}

main "$@"
