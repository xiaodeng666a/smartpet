from pathlib import Path

from langchain.tools import tool

from src.tools.file_check_tools import check_file_path_result


MAX_CHARS = 6000


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def format_file_content(path: Path, content: str) -> str:
    cleaned = content.strip()
    if not cleaned:
        return f"文件 `{path.name}` 是空的。"

    if len(cleaned) > MAX_CHARS:
        cleaned = cleaned[:MAX_CHARS] + "\n\n[内容过长，已截断]"

    return (
        f"文件名: {path.name}\n"
        f"路径: {path}\n"
        f"内容:\n{cleaned}"
    )


@tool
def read_markdown(path: str) -> str:
    """Read a markdown or text file from allowed folders and return its content."""
    check_result = check_file_path_result(path)
    if not check_result.valid or not check_result.resolved_path:
        return f"读取失败：{check_result.error}"

    resolved = Path(check_result.resolved_path)
    content = read_text_file(resolved)
    return format_file_content(resolved, content)
