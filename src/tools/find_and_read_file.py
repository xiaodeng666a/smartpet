from pathlib import Path

from langchain.tools import tool

from src.tools.file_check_tools import (
    DESKTOP_ROOT,
    DOCUMENTS_ROOT,
    DOWNLOADS_ROOT,
    PROJECT_ROOT,
    SEARCHABLE_EXTENSIONS,
)
from src.tools.read_markdown import format_file_content, read_text_file
from src.tools.read_pdf import read_pdf_file


LOCATION_MAP = {
    "桌面": DESKTOP_ROOT,
    "文档": DOCUMENTS_ROOT,
    "下载": DOWNLOADS_ROOT,
    "项目": PROJECT_ROOT,
}


def _resolve_search_root(location: str) -> Path | None:
    return LOCATION_MAP.get(location)


def _find_candidate_files(root: Path, keyword: str) -> list[Path]:
    keyword_lower = keyword.lower().strip()
    matches: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SEARCHABLE_EXTENSIONS:
            continue

        stem = path.stem.lower()
        name = path.name.lower()
        if keyword_lower in stem or keyword_lower in name:
            matches.append(path)

    return matches


def read_file_by_path(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".md", ".markdown", ".txt"}:
        content = read_text_file(path)
        return format_file_content(path, content)

    if suffix == ".pdf":
        return read_pdf_file(path)

    return (
        f"我找到了文件：{path}\n"
        f"不过它是 `{suffix}` 类型，我现在还不能直接读取内容。"
    )


def _format_candidates(location: str, matches: list[Path]) -> str:
    if not matches:
        return f"我没有在{location}里找到匹配的文件。"

    if len(matches) > 1:
        lines = [f"我在{location}里找到了多个匹配文件，请你说得更具体一点：", ""]
        for path in matches[:10]:
            lines.append(f"- {path}")
        if len(matches) > 10:
            lines.append(f"- 还有 {len(matches) - 10} 个结果没有展示")
        return "\n".join(lines)

    return read_file_by_path(matches[0])


@tool
def find_and_read_file(location: str, keyword: str) -> str:
    """Find a supported file by keyword in a known folder and read it when possible."""
    root = _resolve_search_root(location)
    if root is None:
        return "暂时只支持在桌面、文档、下载或项目目录里找文件。"

    if not keyword.strip():
        return "请告诉我你想找的文件名关键词。"

    matches = _find_candidate_files(root, keyword)
    return _format_candidates(location, matches)
