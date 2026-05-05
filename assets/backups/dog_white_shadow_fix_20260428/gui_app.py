import sys
from pathlib import Path

from src.agent.pet_agent import chat_once, key_loaded

try:
    from PySide6.QtCore import QEvent, QPoint, QThread, QTimer, Qt, Signal
    from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QTextBrowser,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:  # pragma: no cover
    print("当前没有安装 PySide6，无法启动桌宠界面。")
    print("请先运行: python -m pip install PySide6")
    print(f"导入错误: {exc}")
    raise SystemExit(1)


ASSET_DIR = Path(__file__).resolve().parent / "assets"
PET_FRAMES_DIR = ASSET_DIR / "anya_pet_frames"
DOG_FRAMES_DIR = ASSET_DIR / "anya_dog_frames"
STATIC_IMAGE_PATH = ASSET_DIR / "anya_cutout.png"
# A hand-picked low-bounce run loop for the 12-frame pet sheet.
# Repeated support poses were making the front-left leg "double swing" before landing,
# so this sequence keeps a single pass through the cleaner stride poses.
MANUAL_RUN_SEQUENCE_12 = [4, 5, 6, 7, 11, 10, 9, 8]
FRAME_INTERVAL_DEFAULT = 84
# Keep the run loop even; too much per-frame holding makes the landing feel like a pause.
FRAME_INTERVALS_12 = {}
# Fine-tune the apparent anchor of a couple of airborne/pre-landing frames so the
# rider does not appear to drift backward right before contact.
FRAME_OFFSETS_12 = {
    11: (-4, 0),
    10: (-2, 0),
}

CHAT_BG = "#fffafc"
CHAT_PANEL = "#fffdf8"
CHAT_ACCENT = "#f4bfd0"
TEXT_DARK = "#5a2b42"
TEXT_SOFT = "#8a5a70"
USER_COLOR = "#1d5d9b"
ASSISTANT_COLOR = "#a63d67"


class ChatWorker(QThread):
    finished_reply = Signal(str, str)
    failed = Signal(str)

    def __init__(self, history: list[tuple[str, str]], user_input: str) -> None:
        super().__init__()
        self.history = list(history)
        self.user_input = user_input

    def run(self) -> None:
        try:
            reply = chat_once(self.history, self.user_input)
            self.finished_reply.emit(self.user_input, reply)
        except Exception as exc:  # pragma: no cover
            self.failed.emit(f"出错啦：{exc}")


class ChatWindow(QMainWindow):
    send_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("阿尼亚聊天框")
        self.setMinimumSize(520, 460)

        root = QWidget()
        root.setStyleSheet(f"background:{CHAT_BG};")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QFrame()
        header.setStyleSheet(f"background:{CHAT_ACCENT}; border-radius:12px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("阿尼亚聊天框")
        title.setStyleSheet(f"color:{TEXT_DARK}; font-weight:700;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("收起")
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet(
            f"background:{CHAT_ACCENT}; color:{TEXT_DARK}; border:none; padding:4px 10px;"
        )
        header_layout.addWidget(close_btn)
        layout.addWidget(header)

        self.status_label = QLabel("阿尼亚准备好啦，哇库哇库。")
        self.status_label.setStyleSheet(f"color:{TEXT_SOFT}; padding-left:6px;")
        layout.addWidget(self.status_label)

        self.chat_box = QTextBrowser()
        self.chat_box.setStyleSheet(
            f"background:{CHAT_PANEL}; color:{TEXT_DARK}; border:none; border-radius:12px; padding:8px;"
        )
        layout.addWidget(self.chat_box, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("和阿尼亚说点什么吧...")
        self.input_box.setFixedHeight(92)
        self.input_box.installEventFilter(self)
        self.input_box.setStyleSheet(
            "background:white; border:none; border-radius:12px; padding:8px;"
        )
        bottom.addWidget(self.input_box, 1)

        button_col = QVBoxLayout()
        button_col.setSpacing(8)

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self._emit_send)
        self.send_button.setStyleSheet(
            f"background:#f2b8c6; color:{TEXT_DARK}; border:none; border-radius:10px; padding:10px 14px; font-weight:700;"
        )
        button_col.addWidget(self.send_button)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_chat)
        clear_btn.setStyleSheet(
            f"background:#ffe4ec; color:{TEXT_DARK}; border:none; border-radius:10px; padding:10px 14px;"
        )
        button_col.addWidget(clear_btn)
        button_col.addStretch()

        bottom.addLayout(button_col)
        layout.addLayout(bottom)

        tip = QLabel("Enter 发送，Shift+Enter 换行")
        tip.setStyleSheet(f"color:{TEXT_SOFT};")
        layout.addWidget(tip)

        self.append_message("system", "阿尼亚来啦，可以开始聊天啦。")

    def eventFilter(self, obj, event):  # noqa: N802
        if obj is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
                event.modifiers() & Qt.ShiftModifier
            ):
                self._emit_send()
                return True
        return super().eventFilter(obj, event)

    def _emit_send(self) -> None:
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self.send_requested.emit(text)

    def append_message(self, role: str, content: str) -> None:
        if role == "user":
            prefix = "你："
            color = USER_COLOR
        elif role == "assistant":
            prefix = "阿尼亚："
            color = ASSISTANT_COLOR
        else:
            prefix = "系统："
            color = TEXT_SOFT
        self.chat_box.append(
            f'<span style="color:{color};"><b>{prefix}</b>{content}</span><br>'
        )

    def clear_chat(self) -> None:
        self.chat_box.clear()
        self.append_message("system", "聊天记录已经清空啦，可以重新开始。")

    def set_busy(self, busy: bool) -> None:
        self.send_button.setDisabled(busy)
        self.input_box.setDisabled(busy)
        if not busy:
            self.input_box.setFocus()


class PetWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("阿尼亚桌宠")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.history: list[tuple[str, str]] = []
        self.drag_offset: QPoint | None = None
        self.press_global_pos: QPoint | None = None
        self.drag_started = False
        self.chat_worker: ChatWorker | None = None
        self.is_busy = False

        self.frames = self._load_frames()
        self.current_frame = 0
        self.frame_index = 0
        self.play_sequence = self._build_play_sequence(len(self.frames))

        self._build_ui()
        self._fit_to_frame()
        self._start_timers()

        self.chat_window = ChatWindow()
        self.chat_window.send_requested.connect(self._send_message)

        if not key_loaded():
            QMessageBox.warning(
                self,
                "API Key 未加载",
                "当前没有读取到模型 API Key，聊天功能可能无法正常使用。",
            )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.pet_label = QLabel()
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setStyleSheet("background: transparent;")
        self.pet_label.installEventFilter(self)
        root.addWidget(self.pet_label)
        self._render_frame()

    def _fit_to_frame(self) -> None:
        pix = self.frames[0]
        self.resize(pix.width(), pix.height())
        self.pet_label.setFixedSize(pix.size())

    def _load_frames(self) -> list[QPixmap]:
        for frame_dir in (PET_FRAMES_DIR, DOG_FRAMES_DIR):
            frame_files = sorted(frame_dir.glob("frame_*.png"))
            if frame_files:
                frames = []
                for path in frame_files:
                    pix = QPixmap(str(path))
                    if not pix.isNull():
                        frames.append(pix)
                if frames:
                    return frames

        if STATIC_IMAGE_PATH.exists():
            pix = QPixmap(str(STATIC_IMAGE_PATH))
            if not pix.isNull():
                return [pix]

        fallback = QPixmap(220, 280)
        fallback.fill(Qt.transparent)
        painter = QPainter(fallback)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#ffe9f1"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(35, 35, 150, 150)
        painter.setPen(QColor(TEXT_DARK))
        painter.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        painter.drawText(fallback.rect(), Qt.AlignCenter, "阿尼亚")
        painter.end()
        return [fallback]

    def _start_timers(self) -> None:
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._tick_frames)
        self.frame_timer.start(FRAME_INTERVAL_DEFAULT)

    def _build_play_sequence(self, frame_count: int) -> list[int]:
        if frame_count <= 1:
            return [0]
        if frame_count >= 36:
            return list(range(frame_count))
        if frame_count >= 24:
            seq = list(range(0, frame_count, 2))
            return seq if seq else list(range(frame_count))
        if frame_count >= 12:
            seq = [i for i in MANUAL_RUN_SEQUENCE_12 if i < frame_count]
            return seq if seq else list(range(frame_count))
        return list(range(frame_count))

    def _render_frame(self) -> None:
        frame = self.frames[self.current_frame]
        if len(self.frames) >= 12 and self.current_frame in FRAME_OFFSETS_12:
            dx, dy = FRAME_OFFSETS_12[self.current_frame]
            canvas = QPixmap(self.pet_label.width(), self.pet_label.height())
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(dx, dy, frame)
            painter.end()
            self.pet_label.setPixmap(canvas)
            return
        self.pet_label.setPixmap(frame)

    def _tick_frames(self) -> None:
        if len(self.frames) <= 1:
            return
        self.frame_index = (self.frame_index + 1) % len(self.play_sequence)
        self.current_frame = self.play_sequence[self.frame_index]
        self._render_frame()
        if len(self.frames) >= 12:
            self.frame_timer.setInterval(
                FRAME_INTERVALS_12.get(self.current_frame, FRAME_INTERVAL_DEFAULT)
            )
        if self.chat_window.isVisible():
            self._position_chat_window()

    def _restart_animation(self) -> None:
        self.frame_index = 0
        self.current_frame = self.play_sequence[0]
        self._render_frame()

    def _toggle_chat(self) -> None:
        if self.chat_window.isVisible():
            self.chat_window.hide()
        else:
            self._position_chat_window()
            self.chat_window.show()
            self.chat_window.raise_()
            self.chat_window.activateWindow()

    def _position_chat_window(self) -> None:
        x = self.x() + self.width() + 20
        y = self.y() + 30
        self.chat_window.move(x, y)

    def _show_menu(self, global_pos) -> None:
        menu = QMenu(self)
        open_chat = QAction("打开聊天框", self)
        open_chat.triggered.connect(
            lambda: (self._position_chat_window(), self.chat_window.show())
        )
        menu.addAction(open_chat)

        hide_chat = QAction("隐藏聊天框", self)
        hide_chat.triggered.connect(self.chat_window.hide)
        menu.addAction(hide_chat)
        menu.addSeparator()

        replay = QAction("重新播放动作", self)
        replay.triggered.connect(self._restart_animation)
        menu.addAction(replay)
        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        menu.exec(global_pos)

    def _send_message(self, user_input: str) -> None:
        if self.is_busy:
            return

        self.chat_window.append_message("user", user_input)
        self.chat_window.status_label.setText("阿尼亚正在思考中...")
        self.chat_window.set_busy(True)
        self.is_busy = True

        self.chat_worker = ChatWorker(self.history, user_input)
        self.chat_worker.finished_reply.connect(self._handle_reply)
        self.chat_worker.failed.connect(self._handle_error)
        self.chat_worker.start()

    def _handle_reply(self, user_input: str, reply: str) -> None:
        self.history.append(("human", user_input))
        self.history.append(("ai", reply))
        self.chat_window.append_message("assistant", reply)
        self.chat_window.status_label.setText("阿尼亚准备好继续聊天啦。")
        self.chat_window.set_busy(False)
        self.is_busy = False

    def _handle_error(self, message: str) -> None:
        self.chat_window.append_message("assistant", message)
        self.chat_window.status_label.setText("刚才出错啦，再试一次吧。")
        self.chat_window.set_busy(False)
        self.is_busy = False

    def eventFilter(self, obj, event):  # noqa: N802
        if obj is self.pet_label:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drag_offset = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                self.press_global_pos = event.globalPosition().toPoint()
                self.drag_started = False
                return True

            if event.type() == QEvent.MouseMove and self.drag_offset and event.buttons() & Qt.LeftButton:
                current = event.globalPosition().toPoint()
                if self.press_global_pos and (current - self.press_global_pos).manhattanLength() > 6:
                    self.drag_started = True
                self.move(current - self.drag_offset)
                if self.chat_window.isVisible():
                    self._position_chat_window()
                return True

            if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                was_dragging = self.drag_started
                self.drag_offset = None
                self.press_global_pos = None
                self.drag_started = False
                if not was_dragging:
                    self._toggle_chat()
                return True

            if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                self._restart_animation()
                return True

            if event.type() == QEvent.ContextMenu:
                self._show_menu(event.globalPos())
                return True

        return super().eventFilter(obj, event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = PetWindow()
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
