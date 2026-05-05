from pathlib import Path

from langchain.tools import tool

from src.tools.read_markdown import MAX_CHARS


def read_pdf_file(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return (
            f"我找到了 PDF 文件：{path}\n"
            "不过当前环境还没安装 `pypdf`，所以暂时不能读取内容。"
        )

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        return f"读取 PDF 失败：{exc}"

    parts: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append(f"[第 {index} 页]\n{text.strip()}")

    content = "\n\n".join(parts).strip()
    if not content:
        return f"我找到了 PDF 文件：{path}\n但没有成功提取到可读文本。"

    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "\n\n[内容过长，已截断]"

    return (
        f"文件名: {path.name}\n"
        f"路径: {path}\n"
        f"内容:\n{content}"
    )


@tool
def read_pdf(path: str) -> str:
    """Read a PDF file from a given path."""
    return read_pdf_file(Path(path))
