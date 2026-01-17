#!/bin/bash

# LocalCowork 启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 启动 LocalCowork${NC}"

# 检查 Ollama 是否运行
check_ollama() {
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Ollama 未运行，正在启动...${NC}"
        ollama serve &
        sleep 3
    fi

    # 检查模型是否存在
    if ! ollama list | grep -q "qwen2.5-coder:32b"; then
        echo -e "${YELLOW}📥 下载模型 qwen2.5-coder:32b...${NC}"
        ollama pull qwen2.5-coder:32b
    fi
}

# 安装依赖
install_deps() {
    if [ ! -d "venv" ]; then
        echo -e "${GREEN}📦 创建虚拟环境...${NC}"
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt
}

# 主逻辑
main() {
    check_ollama
    install_deps

    case "${1:-ui}" in
        ui)
            echo -e "${GREEN}🌐 启动 Web 界面 http://localhost:7860${NC}"
            python -m src.main --mode ui
            ;;
        cli)
            shift
            python -m src.main "$@"
            ;;
        *)
            echo "用法: ./run.sh [ui|cli] [任务]"
            echo "  ui  - 启动 Web 界面"
            echo "  cli - 命令行模式"
            ;;
    esac
}

main "$@"
