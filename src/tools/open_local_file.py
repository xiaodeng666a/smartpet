import os
from pathlib import Path

from langchain.tools import tool

from src.tools.file_check_tools import check_any_file_path_result


def open_local_file_path(path: Path) -> str:
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception as exc:
        return f"打开文件失败：{exc}"

    return f"已经帮你打开文件：{path}"


@tool
def open_local_file(path: str) -> str:
    """Open a local file from allowed folders with the system default application."""
    check_result = check_any_file_path_result(path)
    if not check_result.valid or not check_result.resolved_path:
        return f"打开文件失败：{check_result.error}"
    return open_local_file_path(Path(check_result.resolved_path))
