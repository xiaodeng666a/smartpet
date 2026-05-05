import html
import re
import webbrowser
from urllib.parse import quote_plus

import requests
from langchain.tools import tool


SEARCH_ENDPOINT = "https://www.baidu.com/s"
MAX_RESULTS = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _strip_tags(text: str) -> str:
    text = re.sub(r"<.*?>", "", text, flags=re.S)
    return html.unescape(text).strip()


def _extract_snippet(search_from: str) -> str:
    snippet_patterns = [
        r'<div[^>]*class="c-abstract"[^>]*>(?P<snippet>.*?)</div>',
        r'<span[^>]*class="content-right_8Zs40"[^>]*>(?P<snippet>.*?)</span>',
        r'<div[^>]*class="content-right_8Zs40"[^>]*>(?P<snippet>.*?)</div>',
        r'<div[^>]*class="c-span-last"[^>]*>(?P<snippet>.*?)</div>',
    ]

    for pattern in snippet_patterns:
        match = re.search(pattern, search_from, flags=re.S)
        if match:
            snippet = _strip_tags(match.group("snippet"))
            if snippet:
                return snippet
    return ""


def _parse_results(page: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<h3[^>]*>\s*<a[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        flags=re.S,
    )

    results: list[dict[str, str]] = []
    for match in pattern.finditer(page):
        title = _strip_tags(match.group("title"))
        href = html.unescape(match.group("href")).strip()
        if not title or not href:
            continue

        trailing_html = page[match.end() : match.end() + 1600]
        snippet = _extract_snippet(trailing_html)
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= MAX_RESULTS:
            break

    return results


def _format_results(query: str, results: list[dict[str, str]]) -> str:
    if not results:
        return f"我没有为“{query}”查到可靠的网页结果。"

    lines = [f"我帮你查了“{query}”，找到这些网页结果：", ""]
    for index, item in enumerate(results, start=1):
        lines.append(f"{index}. {item['title']}")
        lines.append(f"   链接：{item['url']}")
        if item["snippet"]:
            lines.append(f"   摘要：{item['snippet']}")
        lines.append("")
    return "\n".join(lines).strip()


@tool
def search_web(query: str) -> str:
    """Search the public web and return a few results."""
    cleaned = query.strip()
    if not cleaned:
        return "请告诉我你想搜索什么内容。"

    search_url = f"{SEARCH_ENDPOINT}?wd={quote_plus(cleaned)}"

    try:
        response = requests.get(
            search_url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
    except Exception as exc:
        return f"网页查询失败：{exc}"

    results = _parse_results(response.text)
    if not results:
        try:
            webbrowser.open(search_url)
            return (
                f"我暂时还没有稳定解析出“{cleaned}”的结果，"
                "不过已经帮你打开百度搜索页啦，你可以先看看网页上的实时内容。"
            )
        except Exception:
            return f"我没有为“{cleaned}”查到可靠的网页结果。"

    return _format_results(cleaned, results)
