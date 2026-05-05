from dataclasses import dataclass
from pathlib import Path

from langchain.tools import tool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
USER_HOME = Path.home()
DESKTOP_ROOT = (USER_HOME / "Desktop").resolve()
DOCUMENTS_ROOT = (USER_HOME / "Documents").resolve()
DOWNLOADS_ROOT = (USER_HOME / "Downloads").resolve()

ALLOWED_ROOTS = [
    PROJECT_ROOT.resolve(),
    DESKTOP_ROOT,
    DOCUMENTS_ROOT,
    DOWNLOADS_ROOT,
]

READABLE_EXTENSIONS = {".md", ".markdown", ".txt"}
SEARCHABLE_EXTENSIONS = READABLE_EXTENSIONS | {".docx", ".pdf"}


@dataclass
class FileCheckResult:
    path: str
    valid: bool
    resolved_path: str | None = None
    error: str | None = None


def _normalize_path(path: str) -> Path:
    candidate = Path(path.strip().strip('"').strip("'"))
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _is_within_allowed_roots(path: Path) -> bool:
    resolved = path.resolve()
    for root in ALLOWED_ROOTS:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def allowed_roots_description() -> str:
    return "项目目录、桌面、文档、下载"


def check_any_file_path_result(path: str) -> FileCheckResult:
    candidate = _normalize_path(path)

    if not _is_within_allowed_roots(candidate):
        return FileCheckResult(
            path=path,
            valid=False,
            error=f"只能读取这些位置里的文件：{allowed_roots_description()}。",
        )

    if not candidate.exists():
        return FileCheckResult(
            path=path,
            valid=False,
            resolved_path=str(candidate),
            error="文件不存在。",
        )

    if not candidate.is_file():
        return FileCheckResult(
            path=path,
            valid=False,
            resolved_path=str(candidate),
            error="这不是一个文件。",
        )

    return FileCheckResult(
        path=path,
        valid=True,
        resolved_path=str(candidate.resolve()),
    )


def check_file_path_result(path: str) -> FileCheckResult:
    result = check_any_file_path_result(path)
    if not result.valid or not result.resolved_path:
        return result

    resolved = Path(result.resolved_path)
    if resolved.suffix.lower() not in READABLE_EXTENSIONS:
        allowed = ", ".join(sorted(READABLE_EXTENSIONS))
        return FileCheckResult(
            path=path,
            valid=False,
            resolved_path=result.resolved_path,
            error=f"暂时只能直接读取这些类型：{allowed}",
        )

    return result


@tool
def check_file_path(path: str) -> str:
    """Check whether a local markdown or text file can be read safely."""
    result = check_file_path_result(path)
    if not result.valid:
        return f"文件检查失败：{result.error}"
    return f"文件检查通过：{result.resolved_path}"
