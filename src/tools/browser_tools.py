import webbrowser
from urllib.parse import quote_plus

from langchain.tools import tool


SITE_MAP = {
    "百度": "https://www.baidu.com",
    "github": "https://github.com",
    "b站": "https://www.bilibili.com",
    "哔哩哔哩": "https://www.bilibili.com",
    "bilibili": "https://www.bilibili.com",
    "知乎": "https://www.zhihu.com",
    "谷歌": "https://www.google.com",
    "google": "https://www.google.com",
}

SITE_SEARCH_MAP = {
    "百度": "https://www.baidu.com/s?wd={query}",
    "b站": "https://search.bilibili.com/all?keyword={query}",
    "哔哩哔哩": "https://search.bilibili.com/all?keyword={query}",
    "bilibili": "https://search.bilibili.com/all?keyword={query}",
    "知乎": "https://www.zhihu.com/search?type=content&q={query}",
    "github": "https://github.com/search?q={query}",
    "谷歌": "https://www.google.com/search?q={query}",
    "google": "https://www.google.com/search?q={query}",
}

SITE_ALIASES = {
    "百度": "百度",
    "百度里": "百度",
    "百度上": "百度",
    "百度里面": "百度",
    "b站": "b站",
    "b站里": "b站",
    "b站上": "b站",
    "b站里面": "b站",
    "哔哩哔哩": "哔哩哔哩",
    "哔哩哔哩里": "哔哩哔哩",
    "哔哩哔哩上": "哔哩哔哩",
    "哔哩哔哩里面": "哔哩哔哩",
    "bilibili": "bilibili",
    "知乎": "知乎",
    "知乎里": "知乎",
    "知乎上": "知乎",
    "知乎里面": "知乎",
    "github": "github",
    "github里": "github",
    "github上": "github",
    "谷歌": "谷歌",
    "谷歌里": "谷歌",
    "谷歌上": "谷歌",
    "google": "google",
}


def _normalize_target(target: str) -> tuple[str, str]:
    cleaned = target.strip()
    return cleaned, cleaned.lower()


def _normalize_site_name(site: str) -> str:
    cleaned = site.strip()
    for prefix in ("我想在", "帮我在", "请在", "在", "我想", "帮我", "请", "去"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    for suffix in ("里面", "里", "上", "网站", "网页", "平台", "的"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
    return SITE_ALIASES.get(cleaned, cleaned)


def _resolve_url(target: str) -> str | None:
    cleaned, cleaned_lower = _normalize_target(target)

    if cleaned in SITE_MAP:
        return SITE_MAP[cleaned]
    if cleaned_lower in SITE_MAP:
        return SITE_MAP[cleaned_lower]
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    return None


def _format_open_result(target: str, url: str | None) -> str:
    if not url:
        return f"我还不知道怎么打开 {target}，你可以直接给我网址。"
    return f"已经帮你打开 {url}"


def _resolve_search_url(site: str, query: str) -> str | None:
    normalized_site = _normalize_site_name(site)
    cleaned_site, cleaned_site_lower = _normalize_target(normalized_site)
    template = SITE_SEARCH_MAP.get(cleaned_site) or SITE_SEARCH_MAP.get(cleaned_site_lower)
    if not template:
        return None
    return template.format(query=quote_plus(query.strip()))


@tool
def open_website(target: str) -> str:
    """Open a common website in the default browser."""
    url = _resolve_url(target)
    if not url:
        return _format_open_result(target, None)

    webbrowser.open(url)
    return _format_open_result(target, url)


@tool
def search_website(site: str, query: str) -> str:
    """Open a supported website's internal search results page."""
    if not query.strip():
        return "请告诉我你想在这个网站里搜什么内容。"

    search_url = _resolve_search_url(site, query)
    if not search_url:
        return f"我还不知道怎么在 {site} 里搜索，你可以换一个网站或者直接让我搜网页。"

    webbrowser.open(search_url)
    return f"已经帮你在 {site} 里搜索 {query} 啦。"
