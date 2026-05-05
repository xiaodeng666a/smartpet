import sys

from src.agent.pet_agent import chat_once, key_loaded


def _configure_console_encoding() -> None:
    """Best-effort UTF-8 console setup for Windows terminals."""
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main() -> None:
    _configure_console_encoding()
    print("KEY loaded:", key_loaded())
    print("桌宠助手已启动，输入 exit 退出。")

    history: list[tuple[str, str]] = []

    while True:
        user_input = input("你：").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("桌宠助手：下次再见。")
            break

        reply = chat_once(history, user_input)
        history.append(("human", user_input))
        history.append(("ai", reply))
        print("桌宠助手：", reply)


if __name__ == "__main__":
    main()
