"""网络搜索和获取工具"""
from .base import BaseTool, ToolResult, tool_registry


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "使用 DuckDuckGo 搜索互联网"
    parameters_schema = {
        "query": {"type": "string", "description": "搜索关键词"},
        "max_results": {"type": "integer", "description": "最大结果数，默认5", "optional": True}
    }

    def execute(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return ToolResult(True, "未找到相关结果")

            output_lines = []
            for i, r in enumerate(results, 1):
                output_lines.append(f"{i}. **{r['title']}**")
                output_lines.append(f"   {r['href']}")
                output_lines.append(f"   {r['body'][:200]}...")
                output_lines.append("")

            return ToolResult(True, "\n".join(output_lines))
        except ImportError:
            return ToolResult(False, "", "缺少 duckduckgo-search 库")
        except Exception as e:
            return ToolResult(False, "", str(e))


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "获取网页内容（返回纯文本）"
    parameters_schema = {
        "url": {"type": "string", "description": "网页 URL"},
        "max_length": {"type": "integer", "description": "最大返回字符数，默认5000", "optional": True}
    }

    def execute(self, url: str, max_length: int = 5000) -> ToolResult:
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; FlexCowork/1.0)"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 移除脚本和样式
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)

            # 截断
            if len(text) > max_length:
                text = text[:max_length] + "\n...(内容已截断)"

            return ToolResult(True, text)
        except ImportError:
            return ToolResult(False, "", "缺少 requests 或 beautifulsoup4 库")
        except Exception as e:
            return ToolResult(False, "", str(e))


def register_web_tools():
    """注册网络工具"""
    tool_registry.register(WebSearchTool())
    tool_registry.register(WebFetchTool())
