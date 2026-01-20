# FlexCowork

🚀 **灵活的 AI Agent 系统** - 支持多种 LLM API 提供商

FlexCowork 是一个支持 OpenAI、Claude、Gemini、DeepSeek 等多种 API 的 AI Agent 系统，无需本地 GPU，通过云端 API 即可使用强大的 AI 能力。

## ✨ 特性

- **多提供商支持**：OpenAI / Claude / Gemini / DeepSeek 一键切换
- **统一接口**：不同提供商使用相同的工具和交互方式
- **丰富工具集**：文件操作、Shell 命令、文档生成、网络搜索
- **Web UI**：基于 Gradio 的现代化界面，支持提供商/模型选择
- **CLI 模式**：命令行快速执行任务
- **安全机制**：危险操作确认、路径沙盒隔离

## 🔌 支持的提供商

| 提供商 | 模型示例 | 环境变量 |
|--------|----------|----------|
| **OpenAI** | gpt-4o, gpt-4o-mini | `OPENAI_API_KEY` |
| **Claude** | claude-sonnet-4-20250514, claude-opus-4-20250514 | `ANTHROPIC_API_KEY` |
| **Gemini** | gemini-1.5-pro, gemini-2.0-flash | `GOOGLE_API_KEY` |
| **DeepSeek** | deepseek-chat, deepseek-coder | `DEEPSEEK_API_KEY` |

## 🚀 快速开始

### 安装

```bash
cd flex-cowork

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 设置 API Key

```bash
# 方式一：环境变量（推荐）
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."

# 方式二：在 UI 中输入
# 方式三：CLI --api-key 参数
```

### 运行

**Web UI 模式（推荐）**

```bash
./run.sh ui
# 或
python -m src.main --mode ui
```

访问 http://localhost:7860

**CLI 模式**

```bash
# 使用 OpenAI (默认)
./run.sh cli "创建一个项目进度报告"

# 使用 Claude
./run.sh cli --provider claude "分析当前目录的代码结构"

# 使用 DeepSeek
./run.sh cli --provider deepseek --model deepseek-coder "写一个快速排序算法"

# 指定 API Key
./run.sh cli --provider openai --api-key sk-xxx "搜索最新 AI 新闻"
```

## 📁 项目结构

```
flex-cowork/
├── config/
│   └── config.yaml          # 配置文件
├── src/
│   ├── agent/
│   │   └── core.py          # Agent 核心循环
│   ├── llm/
│   │   ├── providers.py     # 多提供商 LLM 客户端
│   │   └── prompts.py       # 系统提示词
│   ├── tools/
│   │   ├── base.py          # 工具基类
│   │   ├── file_tools.py    # 文件操作
│   │   ├── shell_tools.py   # Shell 执行
│   │   ├── web_tools.py     # 网络搜索
│   │   └── document_tools.py# 文档生成
│   ├── ui/
│   │   └── gradio_app.py    # Gradio Web 界面
│   └── main.py              # 主入口
├── workspace/               # 默认工作目录
├── requirements.txt
├── run.sh
└── README.md
```

## 🔧 内置工具

| 工具 | 功能 | 需确认 |
|------|------|--------|
| `read_file` | 读取文件内容 | ✗ |
| `write_file` | 写入文件 | ✓ |
| `list_directory` | 列出目录 | ✗ |
| `move_file` | 移动/重命名 | ✓ |
| `delete_file` | 删除文件 | ✓ |
| `execute_shell` | 执行 Shell 命令 | ✓ |
| `execute_python` | 执行 Python 代码 | ✓ |
| `web_search` | DuckDuckGo 搜索 | ✗ |
| `web_fetch` | 获取网页内容 | ✗ |
| `create_docx` | 创建 Word 文档 | ✗ |
| `create_xlsx` | 创建 Excel 表格 | ✗ |
| `create_pptx` | 创建 PPT | ✗ |

## ⚙️ 配置

编辑 `config/config.yaml`：

```yaml
llm:
  default_provider: openai
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o
    claude:
      api_key: ${ANTHROPIC_API_KEY}
      model: claude-sonnet-4-20250514
  temperature: 0.7
  max_tokens: 4096

agent:
  max_iterations: 50
  auto_approve: false
```

## 🔐 安全特性

- **路径沙盒**：所有文件操作限制在工作目录内
- **危险命令检测**：自动拦截 `rm -rf /` 等危险命令
- **操作确认**：写入、删除、执行等操作需用户确认
- **API Key 保护**：支持环境变量，避免明文存储

## 📊 与 LocalCowork 对比

| 特性 | LocalCowork | FlexCowork |
|------|-------------|------------|
| LLM | Ollama (本地) | API (云端) |
| GPU 需求 | 需要 | 不需要 |
| 模型 | qwen2.5-coder | GPT-4o/Claude/Gemini 等 |
| 部署 | 需下载模型 | 开箱即用 |
| 成本 | 免费 | 按 API 计费 |
| 响应速度 | 取决于硬件 | 通常更快 |

## 📝 许可证

MIT License
