# LocalCowork

基于 Ollama 的本地 AI Agent 系统，类似 Claude Code/Cowork 的本地替代方案。

## 功能特性

- **文件系统操作**：读取、写入、移动、删除文件（带沙盒隔离）
- **Shell 命令执行**：在 Docker 沙盒中安全执行命令
- **文档生成**：创建 Word、Excel、PPT 文档
- **网络搜索**：搜索互联网获取最新信息
- **技能系统**：可扩展的 YAML 配置技能
- **Web 界面**：基于 Gradio 的交互式 UI

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| LLM | Ollama + Qwen2.5-Coder-32B | 本地大语言模型 |
| Agent 框架 | 自研 Python | 轻量级，完全可控 |
| 沙盒 | Docker | 隔离命令执行 |
| Web UI | Gradio | Python 原生 UI |
| 配置 | YAML + Python | 声明式配置 |

## 快速开始

### 前置条件

- Python 3.10+
- [Ollama](https://ollama.ai/) 已安装并运行
- Docker（可选，用于沙盒执行）

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd local-cowork

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 拉取模型（如果未安装）
ollama pull qwen2.5-coder:32b
```

### 运行

**方式一：使用启动脚本（推荐）**

```bash
# 启动 Web UI
./run.sh ui

# 命令行模式
./run.sh cli "帮我整理当前目录的文件"
```

**方式二：直接运行**

```bash
# Web UI 模式
python -m src.main --mode ui

# CLI 模式
python -m src.main "你的任务描述"
```

访问 http://localhost:7860 使用 Web 界面。

## 项目结构

```
local-cowork/
├── config/
│   └── config.yaml          # 主配置文件
├── docker/
│   ├── Dockerfile           # 沙盒镜像
│   └── docker-compose.yml   # 服务编排
├── skills/                  # 技能定义目录
│   └── docx/
│       └── skill.yaml       # Word 文档技能
├── src/
│   ├── agent/
│   │   ├── core.py          # Agent 核心循环
│   │   └── executor.py      # Docker 沙盒执行器
│   ├── llm/
│   │   ├── ollama_client.py # Ollama 客户端
│   │   └── prompts.py       # 系统提示词
│   ├── skills/
│   │   └── loader.py        # 技能加载器
│   ├── tools/
│   │   ├── base.py          # 工具基类和注册表
│   │   ├── file_tools.py    # 文件操作工具
│   │   ├── shell_tools.py   # Shell 执行工具
│   │   ├── web_tools.py     # 网络搜索工具
│   │   └── document_tools.py# 文档生成工具
│   ├── ui/
│   │   └── gradio_app.py    # Gradio Web 界面
│   └── main.py              # 主入口
├── workspace/               # 默认工作目录
├── requirements.txt         # Python 依赖
└── run.sh                   # 启动脚本
```

## 内置工具

| 工具名 | 功能 | 需要确认 |
|--------|------|----------|
| `read_file` | 读取文件内容 | 否 |
| `write_file` | 写入文件 | 是 |
| `list_directory` | 列出目录内容 | 否 |
| `move_file` | 移动/重命名文件 | 是 |
| `delete_file` | 删除文件 | 是 |
| `execute_shell` | 执行 Shell 命令 | 是 |
| `execute_python` | 执行 Python 代码 | 是 |
| `web_search` | 网络搜索 | 否 |
| `create_docx` | 创建 Word 文档 | 否 |
| `create_xlsx` | 创建 Excel 表格 | 否 |
| `create_pptx` | 创建 PPT 演示文稿 | 否 |

## 配置说明

编辑 `config/config.yaml` 自定义配置：

```yaml
llm:
  provider: ollama
  model: qwen2.5-coder:32b    # 可更换其他模型
  api_base: http://localhost:11434
  temperature: 0.7

agent:
  max_iterations: 50          # 最大迭代次数
  timeout: 300                # 任务超时（秒）
  auto_approve: false         # 自动批准危险操作

sandbox:
  enabled: true
  type: docker
  memory_limit: 4g
  cpu_limit: 4
```

## 添加自定义技能

在 `skills/` 目录下创建新技能：

```yaml
# skills/my_skill/skill.yaml
name: my_skill
version: "1.0"
description: "我的自定义技能"

triggers:
  - "触发词1"
  - "触发词2"

best_practices: |
  技能使用的最佳实践说明...

examples:
  - input: "示例输入"
    output: "示例输出"
```

## 安全特性

- **路径沙盒**：限制文件操作在工作目录内
- **危险命令检测**：自动识别 `rm -rf`、`sudo` 等危险操作
- **用户确认**：危险操作需要用户明确确认
- **Docker 隔离**：Shell 命令在隔离容器中执行

## 许可证

MIT License
