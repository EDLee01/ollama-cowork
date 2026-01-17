"""网络搜索工具"""
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from .base import BaseTool, ToolResult, tool_registry


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "使用 DuckDuckGo 搜索互联网。适合查找最新信息、新闻、文档"
    parameters_schema = {
        "query": {
            "type": "string",
            "description": "搜索关键词"
        },
        "max_results": {
            "type": "integer",
            "description": "返回结果数量，默认 5"
        }
    }

    def execute(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return ToolResult(
                    success=True,
                    output="没有找到相关结果"
                )

            output_lines = [f"搜索结果：{query}\n" + "=" * 50]
            for i, r in enumerate(results, 1):
                output_lines.append(f"\n[{i}] {r.get('title', 'No Title')}")
                output_lines.append(f"    URL: {r.get('href', 'No URL')}")
                output_lines.append(f"    {r.get('body', 'No Description')[:200]}...")

            return ToolResult(
                success=True,
                output="\n".join(output_lines)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"搜索失败: {str(e)}"
            )


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "获取网页内容。返回网页的主要文本内容"
    parameters_schema = {
        "url": {
            "type": "string",
            "description": "网页 URL"
        }
    }

    def execute(self, url: str) -> ToolResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # 获取文本
            text = soup.get_text(separator="\n", strip=True)

            # 限制长度
            if len(text) > 5000:
                text = text[:5000] + "\n...[内容已截断]"

            return ToolResult(
                success=True,
                output=f"URL: {url}\n\n{text}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"获取网页失败: {str(e)}"
            )


def register_web_tools():
    """注册网络工具"""
    tool_registry.register(WebSearchTool())
    tool_registry.register(WebFetchTool())
