import asyncio
import json
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from langchain.agents import create_agent

from src.config import (
    build_chat_model,
    configurable_model,
    is_key_loaded,
    model_retry_middleware,
)
from src.middlware.guardrails_middleware import GuardrailsMiddleware
from src.prompts.pet_prompt import pet_prompt
from src.tools.browser_tools import open_website, search_website
from src.tools.file_check_tools import check_any_file_path_result
from src.tools.find_and_read_file import find_and_read_file, read_file_by_path
from src.tools.list_project_files import list_project_files
from src.tools.open_local_file import open_local_file
from src.tools.read_markdown import read_markdown
from src.tools.search_web import search_web
from src.tools.weather_tool import get_weather


guardrails_middleware = GuardrailsMiddleware(block_off_topic=True)
file_qa_model = build_chat_model(temperature=0.2)
weather_voice_model = build_chat_model(temperature=0.6)


pet_agent = create_agent(
    model=configurable_model,
    tools=[
        open_website,
        search_website,
        get_weather,
        search_web,
        open_local_file,
        list_project_files,
        read_markdown,
        find_and_read_file,
    ],
    system_prompt=pet_prompt,
    middleware=[guardrails_middleware, model_retry_middleware],
)


FILE_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\n]+")

IDENTITY_PATTERNS = [
    r"^你叫什么(?:名字)?[？?]?$",
    r"^你的名字是什么[？?]?$",
    r"^你是谁[？?]?$",
]

OPEN_PATTERNS = [
    r"^打开\s*(.+)$",
    r"^帮我打开\s*(.+)$",
    r"^帮忙打开\s*(.+)$",
    r"^请打开\s*(.+)$",
    r"^去打开\s*(.+)$",
]

SEARCH_PATTERNS = [
    r"^(?:搜索|搜一下|搜一搜|查一下|查一查|查询|帮我搜索|帮我查)\s*(.+)$",
    r"^(?:搜|查|查找)\s*(.+)$",
]
SITE_SEARCH_PATTERNS = [
    r"^在(.+?)上(?:搜索|搜一下|搜一搜)\s*(.+)$",
    r"^在(.+?)里(?:搜索|搜一下|搜一搜|搜)\s*(.+)$",
    r"^去(.+?)搜\s*(.+)$",
    r"^帮我在(.+?)上(?:搜索|搜一下|搜一搜)\s*(.+)$",
    r"^帮我在(.+?)里(?:搜索|搜一下|搜一搜|搜)\s*(.+)$",
    r"^在(.+?)上(?:看|找)\s*(.+)$",
    r"^在(.+?)里(?:看|找)\s*(.+)$",
    r"^(.+?)上的(.+)$",
    r"^(.+?)里的(.+)$",
    r"^(百度|b站|哔哩哔哩|bilibili|知乎|github|谷歌|google)(?:搜索|搜一下|搜一搜|搜)\s*(.+)$",
]

WEATHER_PATTERNS = [
    r"^(?:查一下|查一查|查询|看看|帮我查)\s*(.+?)\s*天气$",
    r"^(.+?)的\s*(?:今天|今日)?天气(?:怎么样|如何|咋样)?$",
    r"^(.+?)\s*(?:今天|今日)?天气(?:怎么样|如何|咋样)?$",
    r"^(.+?)的\s*(?:今天|今日)?气温(?:怎么样|如何|咋样)?$",
    r"^(.+?)\s*(?:今天|今日)?气温(?:怎么样|如何|咋样)?$",
]
WEATHER_FOLLOWUP_KEYWORDS = (
    "这个天气",
    "这种天气",
    "这天气",
    "适合",
    "要不要",
    "穿什么",
    "带伞",
    "出门",
    "热不热",
    "冷不冷",
)

READ_FILE_PATTERNS = [
    r"^(?:读取|读一下|读一读|看看|查看)\s*(桌面|文档|下载|项目)(?:上|里|中的)?(?:的)?\s*(.+)$",
]

READ_LAST_FILE_PATTERNS = [
    r"^(?:读取|读一下|读一读|看看|查看)\s*(?:它|这个|这个文件|该文件)$",
    r"^(?:帮我)?(?:总结|摘要|概括|分析)\s*(?:它|这个|这个文件|该文件)$",
]

FOLLOW_UP_FILE_KEYWORDS = ("摘要", "结论", "主要内容", "主要讲了什么", "说了什么", "概括", "总结", "分析")
FOLLOW_UP_FILE_REFERENCES = ("文档", "文件", "这篇文档", "这份文件", "它")
REALTIME_HINTS = ("天气", "气温", "温度", "新闻", "热搜", "价格", "汇率", "股价")
TIME_PATTERNS = [
    r"^(?:现在|当前)?几点了[？?]?$",
    r"^(?:现在|当前)?什么时间了[？?]?$",
    r"^(?:现在|当前)?几点[？?]?$",
    r"^(?:现在|当前)?时间(?:是多少|是什么)?[？?]?$",
    r"^(?:本地)?时间(?:是多少|是什么)?[？?]?$",
]
DATE_PATTERNS = [
    r"^(?:今天|今日)几号[？?]?$",
    r"^(?:今天|今日)多少号[？?]?$",
    r"^(?:今天|今日)日期(?:是多少|是什么)?[？?]?$",
    r"^(?:今天|今日)是几月几号[？?]?$",
]
WEEKDAY_PATTERNS = [
    r"^(?:今天|今日)星期几[？?]?$",
    r"^(?:今天|今日)周几[？?]?$",
    r"^(?:今天|今日)礼拜几[？?]?$",
]
DAYPART_PATTERNS = [
    r"^现在是上午还是下午[？?]?$",
    r"^现在是白天还是晚上[？?]?$",
    r"^现在是早上还是晚上[？?]?$",
    r"^现在是中午吗[？?]?$",
    r"^现在是晚上吗[？?]?$",
]
KNOWN_SITE_NAMES = ("百度", "b站", "哔哩哔哩", "bilibili", "知乎", "github", "谷歌", "google")

SITE_QUERY_PREFIXES = (
    "我想看",
    "我想听",
    "我想搜",
    "我想找",
    "我想在",
    "帮我看",
    "帮我听",
    "帮我搜",
    "帮我找",
    "帮我在",
    "请帮我看",
    "请帮我听",
    "请帮我搜",
    "请帮我找",
    "请在",
    "在",
    "去",
)

SITE_QUERY_VERBS = (
    "搜索",
    "搜一下",
    "搜一搜",
    "搜",
    "查一下",
    "查一查",
    "查询",
    "查",
    "找一下",
    "找一找",
    "找",
    "看一下",
    "看一看",
    "看",
    "听一下",
    "听一听",
    "听",
)


def key_loaded() -> bool:
    return is_key_loaded()


def _build_messages(history: Iterable[tuple[str, str]], user_input: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for role, content in history:
        mapped_role = "assistant" if role == "ai" else "user"
        messages.append({"role": mapped_role, "content": content})
    messages.append({"role": "user", "content": user_input})
    return messages


def _match_identity(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in IDENTITY_PATTERNS)


def _match_time_query(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in TIME_PATTERNS)


def _match_date_query(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in DATE_PATTERNS)


def _match_weekday_query(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in WEEKDAY_PATTERNS)


def _match_daypart_query(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in DAYPART_PATTERNS)


def _get_local_time_text() -> str:
    now = datetime.now()
    return (
        f"当然知道呀，现在是 {now.hour} 点 {now.minute:02d} 分"
        f"{now.second:02d} 秒，阿尼亚是按你这台电脑的本地时间来看的哦 (*^▽^*)"
    )


def _get_local_date_text() -> str:
    now = datetime.now()
    return f"今天是 {now.year} 年 {now.month} 月 {now.day} 号呀，哇库哇库 (*^▽^*)"


def _get_local_weekday_text() -> str:
    now = datetime.now()
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    return f"今天是 {weekday_map[now.weekday()]} 呀~"


def _get_local_daypart_text() -> str:
    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 11:
        part = "现在是早上"
    elif 11 <= hour < 13:
        part = "现在是中午"
    elif 13 <= hour < 18:
        part = "现在是下午"
    elif 18 <= hour < 24:
        part = "现在是晚上"
    else:
        part = "现在是凌晨"

    return f"{part}呀，现在本地时间是 {hour} 点 {now.minute:02d} 分。"


def _extract_open_target(user_input: str) -> str | None:
    cleaned = user_input.strip()
    for pattern in OPEN_PATTERNS:
        match = re.match(pattern, cleaned)
        if match:
            return match.group(1).strip()
    if "打开网页" in cleaned or "打开网站" in cleaned:
        return ""
    return None


def _extract_search_query(user_input: str) -> str | None:
    cleaned = user_input.strip()
    for pattern in SEARCH_PATTERNS:
        match = re.match(pattern, cleaned)
        if match:
            return match.group(1).strip()
    if cleaned in {"天气", "气温", "温度"}:
        return None
    if any(hint in cleaned for hint in REALTIME_HINTS):
        return cleaned
    return None



def _clean_site_query_text(text: str) -> str:
    cleaned = text.strip()

    for prefix in SITE_QUERY_PREFIXES:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    cleaned = re.sub(r"^(里|上|里面|中的|上的|里的|中)\s*", "", cleaned)
    cleaned = re.sub(r"^(给我|帮我|一下|一个)\s*", "", cleaned)

    changed = True
    while changed:
        changed = False
        for verb in SITE_QUERY_VERBS:
            if cleaned.startswith(verb):
                cleaned = cleaned[len(verb):].strip()
                changed = True

    cleaned = cleaned.lstrip("的").strip()
    return cleaned


def _extract_site_search_request(user_input: str) -> tuple[str, str] | None:
    cleaned = user_input.strip()

    for site in KNOWN_SITE_NAMES:
        if site not in cleaned:
            continue

        before, after = cleaned.split(site, 1)
        after = _clean_site_query_text(after)
        if after:
            return site, after

        before = _clean_site_query_text(before)
        if before:
            return site, before

    for pattern in SITE_SEARCH_PATTERNS:
        match = re.match(pattern, cleaned)
        if match:
            site = match.group(1).strip()
            query = match.group(2).strip()
            if not site or not query:
                continue
            if site in {"电影", "视频", "内容"}:
                continue
            query = _clean_site_query_text(query)
            if not query:
                continue
            return site, query
    return None
def _extract_weather_city(user_input: str) -> str | None:
    cleaned = user_input.strip()
    for pattern in WEATHER_PATTERNS:
        match = re.match(pattern, cleaned)
        if match:
            city = match.group(1).strip()
            city = re.sub(r"^(今天|今日)", "", city).strip()
            return city
    return None


def _extract_last_weather_city(history: Iterable[tuple[str, str]]) -> str | None:
    for role, content in reversed(list(history)):
        if role != "human":
            continue
        city = _extract_weather_city(content)
        if city:
            return city
    return None


def _should_answer_about_weather(history: list[tuple[str, str]], user_input: str) -> str | None:
    cleaned = user_input.strip()
    if not any(keyword in cleaned for keyword in WEATHER_FOLLOWUP_KEYWORDS):
        return None
    return _extract_last_weather_city(history)


def _extract_file_request(user_input: str) -> tuple[str, str] | None:
    cleaned = user_input.strip()
    for pattern in READ_FILE_PATTERNS:
        match = re.match(pattern, cleaned)
        if match:
            location = match.group(1).strip()
            keyword = match.group(2).strip()
            keyword = re.sub(r"(文件)$", "", keyword).strip()
            return location, keyword
    return None


def _should_read_last_file(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(re.match(pattern, cleaned) for pattern in READ_LAST_FILE_PATTERNS)


def _should_answer_about_last_file(user_input: str) -> bool:
    cleaned = user_input.strip()
    return any(keyword in cleaned for keyword in FOLLOW_UP_FILE_KEYWORDS) and any(
        ref in cleaned for ref in FOLLOW_UP_FILE_REFERENCES
    )


def _extract_last_found_path(history: Iterable[tuple[str, str]]) -> str | None:
    for role, content in reversed(list(history)):
        if role != "ai":
            continue
        matches = FILE_PATH_PATTERN.findall(content)
        if matches:
            return matches[-1]
    return None


def _read_last_file_content(history: list[tuple[str, str]]) -> str | None:
    last_path = _extract_last_found_path(history)
    if not last_path:
        return None

    check_result = check_any_file_path_result(last_path)
    if not check_result.valid or not check_result.resolved_path:
        return f"读取失败：{check_result.error}"

    return read_file_by_path(Path(check_result.resolved_path))


def _try_read_last_file(history: list[tuple[str, str]]) -> str | None:
    content = _read_last_file_content(history)
    if content is None:
        return "我还不知道你说的是哪一个文件。你可以先告诉我文件名，比如“读取桌面上的论文初稿2”。"
    return content


async def _answer_about_last_file(history: list[tuple[str, str]], user_input: str) -> str:
    file_content = _read_last_file_content(history)
    if file_content is None:
        return "我还不知道你说的是哪一个文件。你可以先让我读取那份文件，再继续追问内容。"

    if file_content.startswith("读取失败：") or "还不能直接读取内容" in file_content:
        return file_content

    prompt = [
        {
            "role": "system",
            "content": (
                "你是一个文件问答助手。你必须只根据提供的文件内容回答。"
                "如果文件里没有明确答案，就直接说没有在文件内容里找到，不要猜。"
                "回答用简洁中文。"
            ),
        },
        {
            "role": "user",
            "content": f"文件内容如下：\n\n{file_content}\n\n用户问题：{user_input}",
        },
    ]
    response = await file_qa_model.ainvoke(prompt)
    return response.content if isinstance(response.content, str) else str(response.content)


async def _answer_weather(city: str) -> str:
    raw_result = get_weather.invoke({"city": city})
    try:
        payload = json.loads(raw_result)
    except Exception:
        return raw_result

    if not payload.get("ok"):
        return payload.get("message", "天气查询失败了。")

    prompt = [
        {
            "role": "system",
            "content": (
                "你是名字叫阿尼亚的桌宠助手。"
                "你现在要把真实天气数据自然地说给用户听。"
                "只允许根据给定数据转述，不要补充不存在的信息。"
                "语气要像动漫里的阿尼亚：短句、直接、可爱一点。"
                "可以偶尔说“阿尼亚觉得”或“哇库哇库”，但不要每句都说。"
                "重点要先说明白，不要为了可爱影响准确。"
            ),
        },
        {
            "role": "user",
            "content": f"请把下面这份天气数据整理成自然中文回答：\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]
    response = await weather_voice_model.ainvoke(prompt)
    return response.content if isinstance(response.content, str) else str(response.content)


async def _answer_weather_followup(city: str, user_input: str) -> str:
    raw_result = get_weather.invoke({"city": city})
    try:
        payload = json.loads(raw_result)
    except Exception:
        return raw_result

    if not payload.get("ok"):
        return payload.get("message", "天气查询失败了。")

    prompt = [
        {
            "role": "system",
            "content": (
                "你是名字叫阿尼亚的桌宠助手。"
                "用户正在基于刚才查到的天气继续追问。"
                "你必须只根据给定的天气数据和用户问题来回答，不要编造实时信息。"
                "语气要像动漫里的阿尼亚：短句、直接、可爱一点。"
                "可以偶尔带一点阿尼亚口吻，但不要太吵，不要编造信息。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"天气数据：{json.dumps(payload, ensure_ascii=False)}\n"
                f"用户追问：{user_input}"
            ),
        },
    ]
    response = await weather_voice_model.ainvoke(prompt)
    return response.content if isinstance(response.content, str) else str(response.content)


def _try_open_local_file(history: list[tuple[str, str]], target: str) -> str | None:
    if target in {"它", "这个", "这个文件", "该文件"}:
        last_path = _extract_last_found_path(history)
        if last_path:
            return open_local_file.invoke({"path": last_path})
        return "我还不知道你说的“它”是哪一个文件。你可以直接说文件名，比如“打开论文初稿2”。"

    location_request = re.match(r"^(桌面|文档|下载|项目)(?:上|里|中的)?(?:的)?\s*(.+)$", target)
    if location_request:
        location = location_request.group(1).strip()
        keyword = location_request.group(2).strip()
        file_result = find_and_read_file.invoke({"location": location, "keyword": keyword})
        path_match = FILE_PATH_PATTERN.search(file_result)
        if path_match:
            return open_local_file.invoke({"path": path_match.group(0)})
        return file_result

    for location in ("桌面", "文档", "下载", "项目"):
        file_result = find_and_read_file.invoke({"location": location, "keyword": target})
        path_match = FILE_PATH_PATTERN.search(file_result)
        if path_match:
            return open_local_file.invoke({"path": path_match.group(0)})
    return None


def _try_handle_direct_command(history: list[tuple[str, str]], user_input: str) -> str | None:
    if _match_identity(user_input):
        return "阿尼亚就是阿尼亚呀，哇库哇库，很高兴陪你说话 (*^▽^*)"

    if _match_time_query(user_input):
        return _get_local_time_text()

    if _match_date_query(user_input):
        return _get_local_date_text()

    if _match_weekday_query(user_input):
        return _get_local_weekday_text()

    if _match_daypart_query(user_input):
        return _get_local_daypart_text()

    if _should_read_last_file(user_input):
        return _try_read_last_file(history)

    site_search_request = _extract_site_search_request(user_input)
    if site_search_request is not None:
        site, query = site_search_request
        return search_website.invoke({"site": site, "query": query})

    search_query = _extract_search_query(user_input)
    if search_query is not None:
        return search_web.invoke({"query": search_query})

    target = _extract_open_target(user_input)
    if target is not None:
        if not target:
            return "你想让我打开哪个网站呀？可以直接说“打开百度”，或者给我网址。"

        website_result = open_website.invoke({"target": target})
        if "已经帮你打开" in website_result:
            return website_result

        file_result = _try_open_local_file(history, target)
        if file_result is not None:
            return file_result
        return website_result

    file_request = _extract_file_request(user_input)
    if file_request is not None:
        location, keyword = file_request
        if not keyword:
            return f"你想让我读{location}里的哪个文件呀？"
        return find_and_read_file.invoke({"location": location, "keyword": keyword})

    return None


async def _achat_once(history: list[tuple[str, str]], user_input: str) -> str:
    weather_city = _extract_weather_city(user_input)
    if weather_city is not None:
        if not weather_city:
            return "你想查哪个城市的天气呀？告诉我地名就好啦。"
        return await _answer_weather(weather_city)

    followup_weather_city = _should_answer_about_weather(history, user_input)
    if followup_weather_city is not None:
        return await _answer_weather_followup(followup_weather_city, user_input)

    direct_result = _try_handle_direct_command(history, user_input)
    if direct_result is not None:
        return direct_result

    if _should_answer_about_last_file(user_input):
        return await _answer_about_last_file(history, user_input)

    result = await pet_agent.ainvoke({"messages": _build_messages(history, user_input)})
    messages = result["messages"]

    for message in reversed(messages):
        if getattr(message, "type", "") == "ai":
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                return "".join(text_parts).strip()

    return "我刚刚有点走神了，你再说一次好吗？"


def chat_once(history: list[tuple[str, str]], user_input: str) -> str:
    return asyncio.run(_achat_once(history, user_input))

