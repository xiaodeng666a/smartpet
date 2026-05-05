from pathlib import Path

from langchain.tools import tool

from src.tools.file_check_tools import PROJECT_ROOT, READABLE_EXTENSIONS


DEFAULT_LIMIT = 30


def _collect_files(root: Path, limit: int) -> list[Path]:
    files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in READABLE_EXTENSIONS:
            continue

        files.append(path)
        if len(files) >= limit:
            break

    return files


def _format_file_list(files: list[Path], limit: int) -> str:
    if not files:
        return "当前项目里没有找到可读取的 Markdown 或 TXT 文件。"

    lines = [f"已找到 {len(files)} 个可读取文件（最多展示 {limit} 个）：", ""]
    for file_path in files:
        relative = file_path.relative_to(PROJECT_ROOT)
        lines.append(f"- {relative}")
    return "\n".join(lines)


@tool
def list_project_files(limit: int = DEFAULT_LIMIT) -> str:
    """List readable markdown and text files inside the current project."""
    limit = max(1, min(limit, 100))
    files = _collect_files(PROJECT_ROOT, limit)
    return _format_file_list(files, limit)
