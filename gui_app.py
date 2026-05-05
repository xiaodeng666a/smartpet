import sys
import ctypes
import random
from pathlib import Path

from src.agent.pet_agent import chat_once, key_loaded

try:
    from PySide6.QtCore import QEvent, QPoint, QRect, QSize, QThread, QTimer, Qt, Signal
    from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QTransform
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QMenu,
        QMessageBox,
        QPushButton,
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
WATER_FRAMES_DIR = ASSET_DIR / "anya_water_frames"
SLEEP_FRAMES_DIR = ASSET_DIR / "anya_sleep_frames"
MOVIE_FRAMES_DIR = ASSET_DIR / "anya_movie_frames"
SEDENTARY_FRAMES_DIR = ASSET_DIR / "anya_sedentary_frames"
STATIC_IMAGE_PATH = ASSET_DIR / "anya_cutout.png"

MANUAL_RUN_SEQUENCE_12 = [4, 5, 6, 7, 11, 10, 9, 8]
FRAME_INTERVAL_DEFAULT = 84
FRAME_INTERVALS_12 = {}
FRAME_INTERVALS_10 = {
    0: 108,
    1: 92,
    2: 86,
    3: 84,
    4: 84,
    5: 88,
    6: 96,
    7: 104,
    8: 112,
    9: 118,
}
CHASE_INTERVAL_MS = 24
CHASE_STOP_DISTANCE = 24
CHASE_STEP_MIN = 3
CHASE_STEP_MAX = 26
FLIP_DECISION_THRESHOLD = 8
CURSOR_TARGET_OFFSET_X = 100
CURSOR_TARGET_OFFSET_Y = 200
REMINDER_INTERVAL_MS = 30 * 60 * 1000
REMINDER_RETRY_MS = 5 * 1000
WATER_FRAME_INTERVAL_MS = 180
WATER_FINAL_HOLD_MS = 1400
SEDENTARY_REMINDER_INTERVAL_MS = 50 * 60 * 1000
SEDENTARY_RETRY_MS = 5 * 60 * 1000
SEDENTARY_FRAME_INTERVAL_MS = 145
SEDENTARY_FINAL_HOLD_MS = 1900
SEDENTARY_HEART_PHASES = (
    (0, 0, 0, 0, 0, 0),
    (-2, -2, 10, 0, 0, 0),
    (-8, -12, 14, 8, -22, 8),
    (-12, -24, 16, 4, -36, 10),
    (-16, -34, 18, 0, -48, 12),
)
IDLE_CHAT_INTERVAL_MIN_MS = 8 * 60 * 1000
IDLE_CHAT_INTERVAL_MAX_MS = 15 * 60 * 1000
MOVIE_FRAME_INTERVAL_MS = 210
SCREEN_POLL_INTERVAL_MS = 2200
MOVIE_ENTER_STABLE_TICKS = 1
MOVIE_EXIT_STABLE_TICKS = 1
SLEEP_FRAME_INTERVAL_MS = 130
SLEEP_Z_INTERVAL_MS = 320
SLEEP_BREATH_PATCH_RECT = (96, 118, 104, 72)
SLEEP_BREATH_PHASES = (0, 4, 8, 4)
SLEEP_Z_PHASES = (
    ((146, 18, 16),),
    ((146, 18, 16), (168, 4, 19)),
    ((146, 18, 16), (168, 4, 19), (191, -10, 22)),
    (),
)
VK_F5 = 0x74
FRAME_OFFSETS_12 = {
    11: (-4, 0),
    10: (-2, 0),
}
FRAME_OFFSETS_10 = {
    0: (0, 0),
    1: (40, 0),
    2: (34, 0),
    3: (11, 0),
    4: (41, 0),
    5: (38, 0),
    6: (2, 0),
    7: (40, 0),
    8: (32, 0),
    9: (51, 0),
}
MOVIE_FRAME_OFFSETS = {
    0: (5, 0),
    1: (5, 0),
    2: (5, 0),
    3: (5, 0),
    4: (5, 0),
    5: (5, 0),
}
SEDENTARY_FRAME_OFFSETS = {
    0: (1, 0),
    1: (0, 0),
    2: (22, 0),
    3: (10, 0),
    4: (23, 0),
}
SEDENTARY_PLAY_SEQUENCE = [0, 1, 1, 2, 2, 3, 3, 3, 3, 4]

TEXT_DARK = "#5a2b42"
DEFAULT_SCALE_PERCENT = 40
CHAT_TAIL_TIP_X = 11
CHAT_TAIL_TIP_Y = 2
CHAT_ANCHOR_BASE_X = 300
CHAT_ANCHOR_BASE_Y = 44
CHAT_VERTICAL_LIFT = -26
CHAT_VERTICAL_NUDGE_PX = 15
VIDEO_TITLE_KEYWORDS = (
    "bilibili",
    "douyu",
    "douyu.com",
    "live.douyu.com",
    "douyutv",
    "huya",
    "huya.com",
    "www.huya.com",
    "huya live",
    "斗鱼直播",
    "虎牙直播",
    "直播间",
    "正在直播",
    "主播",
    "douyin",
    "twitch",
    "live",
    "livestream",
    "live room",
    "stream",
    "哔哩哔哩",
    "youtube",
    "netflix",
    "iqiyi",
    "爱奇艺",
    "腾讯视频",
    "youku",
    "优酷",
    "芒果tv",
    "potplayer",
    "vlc",
    "movie",
    "video",
    "影片",
    "电影",
    "电视剧",
    "番剧",
    "动画",
)
VIDEO_PROCESS_KEYWORDS = (
    "potplayer",
    "vlc",
    "mpc-hc",
    "mpc-be",
    "qqvideo",
    "qqlive",
    "youku",
    "iqiyi",
    "bilibili",
    "douyu",
    "douyutv",
    "huya",
    "huya.com",
    "douyin",
    "twitch",
    "douyu",
    "huya",
)
BROWSER_PROCESS_NAMES = ("chrome", "msedge", "firefox", "opera", "brave")
BROWSER_LIVE_HINTS = (
    "douyu",
    "douyu.com",
    "huya",
    "huya.com",
    "twitch",
    "直播",
    "直播间",
    "虎牙直播",
    "斗鱼直播",
)
IDLE_CHAT_LINES = (
    "阿尼亚在这里哦，哇库哇库。",
    "主人现在在忙什么呀？",
    "阿尼亚觉得今天也会很有意思。",
    "有阿尼亚陪着，不会无聊哦。",
    "诶嘿，阿尼亚冒出来一下。",
    "主人要是累了，就休息一下吧。",
)


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
            self.failed.emit(f"阿尼亚刚刚走神了，回复失败：{exc}")


class TailBubbleLabel(QLabel):
    def __init__(self, text: str, fill: str, border: str, parent=None) -> None:
        super().__init__(text, parent)
        self.fill = fill
        self.border = border
        self.setWordWrap(True)
        self.setTextFormat(Qt.PlainText)
        self.setContentsMargins(12, 8, 12, 16)
        self.setStyleSheet("background:transparent; color:#5a2b42;")

    def sizeHint(self):  # noqa: N802
        hint = super().sizeHint()
        hint.setHeight(hint.height() + 10)
        hint.setWidth(hint.width() + 8)
        return hint

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(self.border))
        painter.setBrush(QColor(self.fill))

        rect = self.rect().adjusted(1, 1, -1, -11)
        bubble = QPainterPath()
        bubble.addRoundedRect(rect, 16, 16)

        tail = QPainterPath()
        tail.moveTo(rect.left() + 24, rect.bottom() - 2)
        tail.lineTo(rect.left() + 10, rect.bottom() + 10)
        tail.lineTo(rect.left() + 34, rect.bottom() + 2)
        tail.closeSubpath()

        painter.drawPath(bubble.united(tail))
        super().paintEvent(event)


class TailBubbleReply(QWidget):
    action_clicked = Signal()

    def __init__(self, fill: str, border: str, parent=None) -> None:
        super().__init__(parent)
        self.fill = fill
        self.border = border
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 16)
        layout.setSpacing(6)

        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setStyleSheet("background:transparent; color:#5a2b42;")
        layout.addWidget(self.label)

        self.action_button = QPushButton("")
        self.action_button.hide()
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.setStyleSheet(
            """
            QPushButton {
                background:#ffcadf;
                color:#5a2b42;
                border:1px solid #f0cada;
                border-radius:12px;
                padding:4px 12px;
                font: 9pt "Microsoft YaHei UI";
            }
            QPushButton:hover {
                background:#ffb9d4;
            }
            """
        )
        self.action_button.clicked.connect(self.action_clicked.emit)
        layout.addWidget(self.action_button, 0, Qt.AlignLeft)

    def setText(self, text: str) -> None:  # noqa: N802
        self.label.setText(text)

    def text(self) -> str:
        return self.label.text()

    def show_action_button(self, button_text: str, action_name: str) -> None:
        self.action_button.setProperty("action_name", action_name)
        self.action_button.setText(button_text)
        self.action_button.adjustSize()
        self.action_button.show()
        self.updateGeometry()

    def hide_action_button(self) -> None:
        self.action_button.hide()
        self.action_button.setProperty("action_name", None)
        self.updateGeometry()

    def sizeHint(self):  # noqa: N802
        hint = super().sizeHint()
        hint.setHeight(hint.height() + 10)
        hint.setWidth(hint.width() + 8)
        return hint

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(self.border))
        painter.setBrush(QColor(self.fill))

        rect = self.rect().adjusted(1, 1, -1, -11)
        bubble = QPainterPath()
        bubble.addRoundedRect(rect, 16, 16)

        tail = QPainterPath()
        tail.moveTo(rect.left() + 24, rect.bottom() - 2)
        tail.lineTo(rect.left() + 10, rect.bottom() + 10)
        tail.lineTo(rect.left() + 34, rect.bottom() + 2)
        tail.closeSubpath()

        painter.drawPath(bubble.united(tail))
        super().paintEvent(event)


class TailBubbleInput(QWidget):
    def __init__(self, placeholder: str, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedHeight(62)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 16)
        layout.setSpacing(0)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(placeholder)
        self.editor.setFrameStyle(0)
        self.editor.setAcceptRichText(False)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setStyleSheet(
            "background:transparent; color:#5a2b42; border:none; padding:0px;"
        )
        layout.addWidget(self.editor)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#f0cada"))
        painter.setBrush(QColor("#ffe5ee"))

        rect = self.rect().adjusted(1, 1, -1, -11)
        bubble = QPainterPath()
        bubble.addRoundedRect(rect, 16, 16)

        tail = QPainterPath()
        tail.moveTo(rect.left() + 24, rect.bottom() - 2)
        tail.lineTo(rect.left() + 10, rect.bottom() + 10)
        tail.lineTo(rect.left() + 34, rect.bottom() + 2)
        tail.closeSubpath()

        painter.drawPath(bubble.united(tail))
        super().paintEvent(event)


class BubbleChatWindow(QWidget):
    send_requested = Signal(str)
    geometry_changed = Signal()
    action_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("阿尼亚聊天框")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(232, 88)
        self.setMinimumHeight(88)
        self.reply_restore_input = True

        self.reply_timer = QTimer(self)
        self.reply_timer.setSingleShot(True)
        self.reply_timer.timeout.connect(self._handle_reply_timeout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input_shell = TailBubbleInput("和阿尼亚说点什么吧...")
        self.input_box = self.input_shell.editor
        self.input_box.setFixedHeight(34)
        self.input_box.installEventFilter(self)
        layout.addWidget(self.input_shell)

        self.reply_bubble = TailBubbleReply("#ffe5ee", "#f0cada")
        self.reply_bubble.setMaximumWidth(196)
        self.reply_bubble.hide()
        layout.addWidget(self.reply_bubble)
        self.reply_bubble.action_clicked.connect(self._handle_action_button)

        self.send_button = QPushButton("发送")
        self.send_button.hide()

        self._refresh_window_height()

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
        self.reply_timer.stop()
        self.input_box.clear()
        self.send_requested.emit(text)

    def _refresh_window_height(self) -> None:
        old_size = self.size()
        if self.input_shell.isVisible():
            target_width = 208
            target_height = 88
        else:
            hint = self.reply_bubble.sizeHint()
            target_width = max(132, min(hint.width(), 196))
            target_height = max(76, min(hint.height(), 164))
        self.setFixedSize(target_width, target_height)
        if self.size() != old_size:
            self.geometry_changed.emit()

    def _handle_reply_timeout(self) -> None:
        if self.reply_restore_input:
            self.show_input_mode()
            return
        self.reply_bubble.hide()
        self.reply_bubble.hide_action_button()
        self._refresh_window_height()
        self.hide()

    def show_input_mode(self) -> None:
        self.reply_timer.stop()
        self.reply_restore_input = True
        self.reply_bubble.hide()
        self.reply_bubble.hide_action_button()
        self.input_shell.show()
        self.input_box.setDisabled(False)
        self._refresh_window_height()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_box.setFocus()

    def begin_thinking(self) -> None:
        self.reply_timer.stop()
        self.reply_restore_input = True
        self.input_shell.hide()
        self.reply_bubble.hide()
        self.reply_bubble.hide_action_button()
        self._refresh_window_height()
        self.hide()

    def show_reply_mode(self, content: str, restore_input: bool = True) -> None:
        self.reply_restore_input = restore_input
        self.input_shell.hide()
        self.reply_bubble.hide_action_button()
        self.reply_bubble.setText(content)
        self.reply_bubble.show()
        self._refresh_window_height()
        self.show()
        self.raise_()
        self.activateWindow()
        self.reply_timer.start(5000)

    def show_action_reply_mode(
        self,
        content: str,
        button_text: str,
        action_name: str,
        *,
        restore_input: bool = False,
    ) -> None:
        self.reply_timer.stop()
        self.reply_restore_input = restore_input
        self.input_shell.hide()
        self.reply_bubble.setText(content)
        self.reply_bubble.show_action_button(button_text, action_name)
        self.reply_bubble.show()
        self._refresh_window_height()
        self.show()
        self.raise_()
        self.activateWindow()

    def set_busy(self, busy: bool) -> None:
        self.input_box.setDisabled(busy)

    def _handle_action_button(self) -> None:
        action_name = self.reply_bubble.action_button.property("action_name")
        if action_name:
            self.action_clicked.emit(str(action_name))


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
        self.chat_window: BubbleChatWindow | None = None
        self.is_busy = False
        self.resize_anchor_mode = "bottom"
        self.scale_percent = DEFAULT_SCALE_PERCENT
        self.chase_enabled = False
        self.menu_open = False
        self.facing_right = False
        self.f5_was_down = False
        self.water_reminder_active = False
        self.water_ack_pending = False
        self.water_manual_mode = False
        self.water_frame_index = 0
        self.sedentary_reminder_active = False
        self.sedentary_ack_pending = False
        self.sedentary_manual_mode = False
        self.sedentary_frame_index = 0
        self.movie_action_active = False
        self.movie_frame_index = 0
        self.movie_manual_override = False
        self.movie_detect_hits = 0
        self.movie_detect_misses = 0
        self.sleep_action_active = False
        self.sleep_frame_index = 0
        self.sleep_z_phase = 0
        self.idle_chat_enabled = True

        self.frames = self._load_frames()
        self.water_frames = self._load_optional_frames(WATER_FRAMES_DIR)
        self.sedentary_frames = self._load_optional_frames(SEDENTARY_FRAMES_DIR)
        self.movie_frames = self._load_optional_frames(MOVIE_FRAMES_DIR)
        self.sleep_frames = self._load_optional_frames(SLEEP_FRAMES_DIR)
        self.current_frame = 0
        self.frame_index = 0
        self.play_sequence = self._build_play_sequence(len(self.frames))

        self._build_ui()
        self._fit_to_frame()

        self.chat_window = BubbleChatWindow()
        self.chat_window.send_requested.connect(self._send_message)
        self.chat_window.geometry_changed.connect(self._position_chat_window)
        self.chat_window.action_clicked.connect(self._handle_chat_action)
        QApplication.instance().installEventFilter(self)

        self._start_timers()

        if not key_loaded():
            QMessageBox.warning(
                self,
                "API Key 未配置",
                "还没有检测到可用的 API Key，聊天功能可能无法正常回复。",
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
        width, height = self._scaled_dimensions(pix.width(), pix.height())
        self._set_display_size(width, height)

    def _set_display_size(self, width: int, height: int) -> None:
        if self.width() == width and self.height() == height:
            return
        old_x = self.x()
        old_y = self.y()
        old_bottom = self.y() + self.height()
        self.resize(width, height)
        self.pet_label.setFixedSize(width, height)
        if old_bottom > 0:
            if self.resize_anchor_mode == "top":
                self.move(old_x, old_y)
            else:
                self.move(old_x, old_bottom - height)
            if self._chat_window_visible():
                self._position_chat_window()
        self.resize_anchor_mode = "bottom"

    def _scaled_dimensions(self, width: int, height: int) -> tuple[int, int]:
        scale = self.scale_percent / 100.0
        return max(1, round(width * scale)), max(1, round(height * scale))

    def _scaled_pixmap(self, pixmap: QPixmap) -> QPixmap:
        width, height = self._scaled_dimensions(pixmap.width(), pixmap.height())
        if width == pixmap.width() and height == pixmap.height():
            return pixmap
        return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _chat_window_visible(self) -> bool:
        return bool(self.chat_window and self.chat_window.isVisible())

    def _chat_input_focused(self) -> bool:
        return bool(self.chat_window and self.chat_window.input_box.hasFocus())

    def _load_frames(self) -> list[QPixmap]:
        for frame_dir in (PET_FRAMES_DIR, DOG_FRAMES_DIR):
            frame_files = sorted(frame_dir.glob("frame_*.png"))
            if not frame_files:
                continue
            frames: list[QPixmap] = []
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

    def _load_optional_frames(self, frame_dir: Path) -> list[QPixmap]:
        frame_files = sorted(frame_dir.glob("frame_*.png"))
        frames: list[QPixmap] = []
        for path in frame_files:
            pix = QPixmap(str(path))
            if not pix.isNull():
                frames.append(pix)
        return frames

    def _start_timers(self) -> None:
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._tick_frames)
        self.frame_timer.start(FRAME_INTERVAL_DEFAULT)

        self.chase_timer = QTimer(self)
        self.chase_timer.timeout.connect(self._tick_chase)
        self.chase_timer.start(CHASE_INTERVAL_MS)

        self.hotkey_timer = QTimer(self)
        self.hotkey_timer.timeout.connect(self._poll_hotkeys)
        self.hotkey_timer.start(30)

        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self._maybe_show_water_reminder)
        self.reminder_timer.start(REMINDER_INTERVAL_MS)

        self.reminder_retry_timer = QTimer(self)
        self.reminder_retry_timer.setSingleShot(True)
        self.reminder_retry_timer.timeout.connect(self._maybe_show_water_reminder)

        self.sedentary_reminder_timer = QTimer(self)
        self.sedentary_reminder_timer.timeout.connect(self._maybe_show_sedentary_reminder)
        self.sedentary_reminder_timer.start(SEDENTARY_REMINDER_INTERVAL_MS)

        self.sedentary_retry_timer = QTimer(self)
        self.sedentary_retry_timer.setSingleShot(True)
        self.sedentary_retry_timer.timeout.connect(self._maybe_show_sedentary_reminder)

        self.idle_chat_timer = QTimer(self)
        self.idle_chat_timer.setSingleShot(True)
        self.idle_chat_timer.timeout.connect(self._maybe_show_idle_chat)
        self._schedule_idle_chat()

        self.screen_state_timer = QTimer(self)
        self.screen_state_timer.timeout.connect(self._poll_screen_activity)
        self.screen_state_timer.start(SCREEN_POLL_INTERVAL_MS)

        self.water_pose_timer = QTimer(self)
        self.water_pose_timer.setSingleShot(True)
        self.water_pose_timer.timeout.connect(self._finish_water_animation)

        self.sedentary_pose_timer = QTimer(self)
        self.sedentary_pose_timer.setSingleShot(True)
        self.sedentary_pose_timer.timeout.connect(self._finish_sedentary_animation)

        self.sleep_pose_timer = QTimer(self)
        self.sleep_pose_timer.setSingleShot(True)
        self.sleep_pose_timer.timeout.connect(self._finish_sleep_animation)

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
        if self.sleep_action_active and self.sleep_frames:
            frame_to_draw = min(self.sleep_frame_index, len(self.sleep_frames) - 1)
            source_frame = self._scaled_pixmap(self.sleep_frames[frame_to_draw])
            if frame_to_draw == len(self.sleep_frames) - 1:
                source_frame = self._prepare_sleep_final_frame(source_frame)
            frame_offsets: dict[int, tuple[int, int]] = {}
        elif self.sedentary_reminder_active and self.sedentary_frames:
            sequence_index = min(
                self.sedentary_frame_index, len(SEDENTARY_PLAY_SEQUENCE) - 1
            )
            frame_to_draw = min(
                SEDENTARY_PLAY_SEQUENCE[sequence_index], len(self.sedentary_frames) - 1
            )
            source_frame = self._scaled_pixmap(self.sedentary_frames[frame_to_draw])
            frame_offsets: dict[int, tuple[int, int]] = SEDENTARY_FRAME_OFFSETS
        elif self.movie_action_active and self.movie_frames:
            frame_to_draw = min(self.movie_frame_index, len(self.movie_frames) - 1)
            source_frame = self._scaled_pixmap(self.movie_frames[frame_to_draw])
            frame_offsets: dict[int, tuple[int, int]] = MOVIE_FRAME_OFFSETS
        elif self.water_reminder_active and self.water_frames:
            frame_to_draw = min(self.water_frame_index, len(self.water_frames) - 1)
            source_frame = self._scaled_pixmap(self.water_frames[frame_to_draw])
            frame_offsets: dict[int, tuple[int, int]] = {}
        else:
            frame_to_draw = self.current_frame
            source_frame = self._scaled_pixmap(self.frames[frame_to_draw])
            frame_offsets: dict[int, tuple[int, int]] = {}
            if len(self.frames) >= 12:
                frame_offsets = FRAME_OFFSETS_12
            elif len(self.frames) == 10:
                frame_offsets = FRAME_OFFSETS_10

        dx = 0
        dy = 0
        if not self.water_reminder_active and frame_to_draw in frame_offsets:
            raw_dx, raw_dy = frame_offsets[frame_to_draw]
            scale = self.scale_percent / 100.0
            dx = round(raw_dx * scale)
            dy = round(raw_dy * scale)

        self._set_display_size(source_frame.width(), source_frame.height())
        canvas = QPixmap(self.pet_label.width(), self.pet_label.height())
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.facing_right:
            mirrored = source_frame.transformed(QTransform().scale(-1, 1), Qt.SmoothTransformation)
            draw_x = canvas.width() - mirrored.width() - dx
            painter.drawPixmap(draw_x, dy, mirrored)
            draw_width = mirrored.width()
        else:
            painter.drawPixmap(dx, dy, source_frame)
            draw_x = dx
            draw_width = source_frame.width()

        if (
            self.sleep_action_active
            and self.sleep_frames
            and frame_to_draw == len(self.sleep_frames) - 1
        ):
            self._draw_sleep_z_overlay(
                painter,
                draw_x,
                dy,
                draw_width,
                self.facing_right,
            )
        elif self.sedentary_reminder_active and frame_to_draw == 3:
            self._draw_sedentary_heart_overlay(
                painter,
                draw_x,
                dy,
                draw_width,
                min(self.sedentary_frame_index, len(SEDENTARY_PLAY_SEQUENCE) - 1),
            )

        painter.end()
        self.pet_label.setPixmap(canvas)

    def _tick_frames(self) -> None:
        if self.sleep_action_active:
            if not self.sleep_frames:
                return
            if self.sleep_frame_index < len(self.sleep_frames) - 1:
                self.sleep_frame_index += 1
                if self.sleep_frame_index == len(self.sleep_frames) - 1:
                    self.sleep_z_phase = 0
                    self.frame_timer.setInterval(SLEEP_Z_INTERVAL_MS)
            else:
                self.sleep_z_phase = (self.sleep_z_phase + 1) % len(SLEEP_Z_PHASES)
            self._render_frame()
            return

        if self.sedentary_reminder_active:
            if not self.sedentary_frames:
                return
            if self.sedentary_frame_index < len(SEDENTARY_PLAY_SEQUENCE) - 1:
                self.sedentary_frame_index += 1
            elif not self.sedentary_ack_pending and not self.sedentary_pose_timer.isActive():
                self.sedentary_pose_timer.start(SEDENTARY_FINAL_HOLD_MS)
            self._render_frame()
            return

        if self.water_reminder_active:
            if not self.water_frames:
                return
            if self.water_ack_pending:
                self.water_frame_index = (self.water_frame_index + 1) % len(self.water_frames)
            elif self.water_frame_index < len(self.water_frames) - 1:
                self.water_frame_index += 1
            elif not self.water_pose_timer.isActive():
                self.water_pose_timer.start(WATER_FINAL_HOLD_MS)
            self._render_frame()
            return

        if self.movie_action_active:
            if not self.movie_frames:
                return
            self.movie_frame_index = (self.movie_frame_index + 1) % len(self.movie_frames)
            self._render_frame()
            self.frame_timer.setInterval(MOVIE_FRAME_INTERVAL_MS)
            return

        if len(self.frames) <= 1:
            return
        self.frame_index = (self.frame_index + 1) % len(self.play_sequence)
        self.current_frame = self.play_sequence[self.frame_index]
        self._render_frame()
        if len(self.frames) >= 12:
            self.frame_timer.setInterval(
                FRAME_INTERVALS_12.get(self.current_frame, FRAME_INTERVAL_DEFAULT)
            )
        elif len(self.frames) == 10:
            self.frame_timer.setInterval(
                FRAME_INTERVALS_10.get(self.current_frame, FRAME_INTERVAL_DEFAULT)
            )

    def _restart_animation(self) -> None:
        self._clear_special_actions()
        self.frame_index = 0
        self.current_frame = self.play_sequence[0]
        self.frame_timer.setInterval(FRAME_INTERVAL_DEFAULT)
        self._render_frame()

    def _toggle_chase(self) -> None:
        self.chase_enabled = not self.chase_enabled

    def _show_movie_animation(self, manual_override: bool = False) -> None:
        if not self.movie_frames:
            return
        self.movie_manual_override = manual_override
        self.movie_action_active = True
        self.movie_detect_hits = 0
        self.movie_detect_misses = 0
        self.movie_frame_index = 0
        self.frame_timer.setInterval(MOVIE_FRAME_INTERVAL_MS)
        self._render_frame()

    def _finish_movie_animation(self) -> None:
        self.movie_action_active = False
        self.movie_frame_index = 0
        self.movie_manual_override = False
        self.movie_detect_hits = 0
        self.movie_detect_misses = 0
        self.frame_timer.setInterval(FRAME_INTERVAL_DEFAULT)
        self._render_frame()

    def _clear_special_actions(self) -> None:
        self.water_pose_timer.stop()
        self.sedentary_pose_timer.stop()
        self.sleep_pose_timer.stop()
        self.water_reminder_active = False
        self.water_ack_pending = False
        self.water_manual_mode = False
        self.water_frame_index = 0
        self.sedentary_reminder_active = False
        self.sedentary_ack_pending = False
        self.sedentary_manual_mode = False
        self.sedentary_frame_index = 0
        self.movie_action_active = False
        self.movie_frame_index = 0
        self.movie_manual_override = False
        self.movie_detect_hits = 0
        self.movie_detect_misses = 0
        self.sleep_action_active = False
        self.sleep_frame_index = 0
        self.sleep_z_phase = 0

    def _show_water_animation(self, *, require_ack: bool) -> None:
        if not self.water_frames:
            return
        self.water_reminder_active = True
        self.water_ack_pending = require_ack
        self.water_manual_mode = not require_ack
        self.water_frame_index = 0
        self.frame_timer.setInterval(WATER_FRAME_INTERVAL_MS)
        self._render_frame()

    def _finish_water_animation(self) -> None:
        self.water_reminder_active = False
        self.water_ack_pending = False
        self.water_manual_mode = False
        self.water_frame_index = 0
        self.frame_timer.setInterval(FRAME_INTERVAL_DEFAULT)
        self._render_frame()
        self._schedule_idle_chat()

    def _show_sedentary_animation(self, *, require_ack: bool) -> None:
        if not self.sedentary_frames:
            return
        self.sedentary_reminder_active = True
        self.sedentary_ack_pending = require_ack
        self.sedentary_manual_mode = not require_ack
        self.sedentary_frame_index = 0
        self.frame_timer.setInterval(SEDENTARY_FRAME_INTERVAL_MS)
        self._render_frame()

    def _finish_sedentary_animation(self) -> None:
        self.sedentary_pose_timer.stop()
        self.sedentary_reminder_active = False
        self.sedentary_ack_pending = False
        self.sedentary_manual_mode = False
        self.sedentary_frame_index = 0
        self.frame_timer.setInterval(FRAME_INTERVAL_DEFAULT)
        self._render_frame()
        self._schedule_idle_chat()

    def _schedule_idle_chat(self) -> None:
        if not self.idle_chat_enabled:
            return
        self.idle_chat_timer.start(
            random.randint(IDLE_CHAT_INTERVAL_MIN_MS, IDLE_CHAT_INTERVAL_MAX_MS)
        )

    def _maybe_show_idle_chat(self) -> None:
        if (
            self.is_busy
            or self.menu_open
            or self.drag_offset
            or self.sedentary_reminder_active
            or self.water_reminder_active
            or self.sleep_action_active
            or self.movie_action_active
            or self._chat_window_visible()
            or self._chat_input_focused()
        ):
            self._schedule_idle_chat()
            return

        if not self.chat_window:
            self._schedule_idle_chat()
            return

        self.chat_window.show_reply_mode(random.choice(IDLE_CHAT_LINES), restore_input=False)
        self._position_chat_window()
        self._schedule_idle_chat()

    def _handle_chat_action(self, action_name: str) -> None:
        if action_name == "water_ack":
            self._acknowledge_water_reminder()
        elif action_name == "sedentary_ack":
            self._acknowledge_sedentary_reminder()

    def _acknowledge_water_reminder(self) -> None:
        if not self.water_reminder_active or not self.water_ack_pending:
            return
        self.chat_window.hide()
        self._finish_water_animation()

    def _activate_water_reminder(self, show_prompt: bool = True) -> None:
        self.reminder_retry_timer.stop()
        self._clear_special_actions()
        self._show_water_animation(require_ack=True)
        if show_prompt and self.chat_window:
            self.chat_window.show_action_reply_mode(
                "主人，记得喝水哦。",
                "收到~",
                "water_ack",
                restore_input=False,
            )
            self._position_chat_window()

    def _acknowledge_sedentary_reminder(self) -> None:
        if not self.sedentary_reminder_active or not self.sedentary_ack_pending:
            return
        self.chat_window.hide()
        self._finish_sedentary_animation()

    def _activate_sedentary_reminder(self, show_prompt: bool = True) -> None:
        self.sedentary_retry_timer.stop()
        self._clear_special_actions()
        self._show_sedentary_animation(require_ack=True)
        if show_prompt and self.chat_window:
            self.chat_window.show_action_reply_mode(
                "已经坐很久啦，站起来伸个懒腰吧。",
                "这就起来",
                "sedentary_ack",
                restore_input=False,
            )
            self._position_chat_window()

    def _show_sleep_animation(self) -> None:
        if not self.sleep_frames:
            return
        self.sleep_pose_timer.stop()
        self.sleep_action_active = True
        self.sleep_frame_index = len(self.sleep_frames) - 1
        self.sleep_z_phase = 0
        self.frame_timer.setInterval(SLEEP_Z_INTERVAL_MS)
        self._render_frame()

    def _finish_sleep_animation(self) -> None:
        self.sleep_pose_timer.stop()
        self.sleep_action_active = False
        self.sleep_frame_index = 0
        self.sleep_z_phase = 0
        self.frame_timer.setInterval(FRAME_INTERVAL_DEFAULT)
        self._render_frame()

    def _prepare_sleep_final_frame(self, source_frame: QPixmap) -> QPixmap:
        composed = source_frame.copy()
        scale = self.scale_percent / 100.0

        breath_amount = round(SLEEP_BREATH_PHASES[self.sleep_z_phase] * scale)
        if breath_amount <= 0:
            return composed

        patch_x, patch_y, patch_w, patch_h = SLEEP_BREATH_PATCH_RECT
        src_rect = QRect(
            round(patch_x * scale),
            round(patch_y * scale),
            round(patch_w * scale),
            round(patch_h * scale),
        )
        quilt_patch = composed.copy(src_rect)
        dest_rect = QRect(
            src_rect.x(),
            src_rect.y() - max(1, breath_amount // 2),
            src_rect.width(),
            src_rect.height() + breath_amount,
        )
        painter = QPainter(composed)
        try:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            clip_path = QPainterPath()
            clip_path.addEllipse(dest_rect)
            painter.setClipPath(clip_path)
            painter.drawPixmap(dest_rect, quilt_patch, quilt_patch.rect())
        finally:
            painter.end()
        return composed

    def _draw_sleep_z_overlay(
        self,
        painter: QPainter,
        draw_x: int,
        draw_y: int,
        frame_width: int,
        mirrored: bool,
    ) -> None:
        scale = self.scale_percent / 100.0
        z_color = QColor("#8ec7ff")
        for base_x, base_y, font_size in SLEEP_Z_PHASES[self.sleep_z_phase]:
            scaled_x = round(base_x * scale)
            scaled_y = round(base_y * scale)
            scaled_font = max(11, round(font_size * scale))
            font = QFont("Comic Sans MS", scaled_font, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance("Z")

            if mirrored:
                text_x = draw_x + frame_width - scaled_x - text_width
            else:
                text_x = draw_x + scaled_x

            painter.setPen(z_color)
            painter.drawText(text_x, draw_y + scaled_y + metrics.ascent(), "Z")

    def _draw_sedentary_heart_overlay(
        self,
        painter: QPainter,
        draw_x: int,
        draw_y: int,
        frame_width: int,
        sequence_index: int,
    ) -> None:
        stretch_phase = min(
            max(0, sequence_index - 5),
            len(SEDENTARY_HEART_PHASES) - 1,
        )
        offset_x, offset_y, size, small_dx, small_dy, small_size = SEDENTARY_HEART_PHASES[stretch_phase]
        if size <= 0 and small_size <= 0:
            return

        scale = self.scale_percent / 100.0
        base_x = draw_x + round(94 * scale)
        base_y = draw_y + round(122 * scale)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        def draw_heart(cx: int, cy: int, heart_size: int, alpha: int) -> None:
            if heart_size <= 0:
                return
            half_w = heart_size
            half_h = max(4, int(heart_size * 0.9))
            path = QPainterPath()
            path.moveTo(cx, cy + half_h)
            path.cubicTo(
                cx - half_w,
                cy + half_h * 0.4,
                cx - half_w * 1.1,
                cy - half_h * 0.35,
                cx,
                cy - half_h * 0.05,
            )
            path.cubicTo(
                cx + half_w * 1.1,
                cy - half_h * 0.35,
                cx + half_w,
                cy + half_h * 0.4,
                cx,
                cy + half_h,
            )
            painter.setPen(QPen(QColor(173, 115, 132, alpha), max(1, round(1.6 * scale))))
            painter.setBrush(QColor(244, 164, 182, alpha))
            painter.drawPath(path)

        draw_heart(
            base_x + round(offset_x * scale),
            base_y + round(offset_y * scale),
            max(4, round(size * scale)),
            220,
        )
        draw_heart(
            base_x + round(small_dx * scale),
            base_y + round(small_dy * scale),
            max(0, round(small_size * scale)),
            190,
        )
        painter.restore()

    def _maybe_show_water_reminder(self) -> None:
        if self.water_reminder_active:
            return
        self._activate_water_reminder(show_prompt=True)

    def _maybe_show_sedentary_reminder(self) -> None:
        if self.sedentary_reminder_active or not self.sedentary_frames:
            return
        if (
            self.is_busy
            or self.menu_open
            or self.drag_offset
            or self.water_reminder_active
            or self.sleep_action_active
            or self.movie_action_active
            or self._chat_window_visible()
            or self._chat_input_focused()
        ):
            self.sedentary_retry_timer.start(SEDENTARY_RETRY_MS)
            return
        self._activate_sedentary_reminder(show_prompt=True)

    def _poll_hotkeys(self) -> None:
        try:
            key_down = bool(ctypes.windll.user32.GetAsyncKeyState(VK_F5) & 0x8000)
        except Exception:
            return

        if key_down and not self.f5_was_down:
            if not self._chat_input_focused():
                self._toggle_chase()
        self.f5_was_down = key_down

    def _poll_screen_activity(self) -> None:
        if (
            self.movie_manual_override
            or self.sleep_action_active
            or self.water_reminder_active
            or self.sedentary_reminder_active
        ):
            return
        detected = self._foreground_looks_like_video()
        if detected:
            self.movie_detect_hits += 1
            self.movie_detect_misses = 0
            if (
                not self.movie_action_active
                and self.movie_detect_hits >= MOVIE_ENTER_STABLE_TICKS
            ):
                self._show_movie_animation(manual_override=False)
            return

        self.movie_detect_misses += 1
        self.movie_detect_hits = 0
        if (
            self.movie_action_active
            and self.movie_detect_misses >= MOVIE_EXIT_STABLE_TICKS
        ):
            self._finish_movie_animation()

    def _foreground_looks_like_video(self) -> bool:
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False

            title_length = user32.GetWindowTextLengthW(hwnd)
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)
            title = title_buffer.value.strip().lower()

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = self._process_name_from_pid(pid.value).lower()
        except Exception:
            return False

        if not title and not process_name:
            return False
        if any(keyword in process_name for keyword in VIDEO_PROCESS_KEYWORDS):
            return True
        if any(keyword in title for keyword in VIDEO_TITLE_KEYWORDS):
            return True
        if any(browser in process_name for browser in BROWSER_PROCESS_NAMES):
            return any(keyword in title for keyword in VIDEO_TITLE_KEYWORDS) or any(
                keyword in title for keyword in BROWSER_LIVE_HINTS
            )
        return False

    def _process_name_from_pid(self, pid: int) -> str:
        if not pid:
            return ""
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if not handle:
            return ""
        try:
            buffer_len = ctypes.c_ulong(260)
            buffer = ctypes.create_unicode_buffer(buffer_len.value)
            ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(buffer_len),
            )
            if not ok:
                return ""
            return Path(buffer.value).stem
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    def _tick_chase(self) -> None:
        if self.sleep_action_active or self.sedentary_reminder_active:
            return
        if not self.chase_enabled or self.drag_offset or self.menu_open:
            return

        cursor_pos = QCursor.pos()
        target_x = cursor_pos.x() + CURSOR_TARGET_OFFSET_X
        target_y = cursor_pos.y() + CURSOR_TARGET_OFFSET_Y
        current_center = self.frameGeometry().center()
        dx = target_x - current_center.x()
        dy = target_y - current_center.y()
        if dx > FLIP_DECISION_THRESHOLD and not self.facing_right:
            self.facing_right = True
            self._render_frame()
        elif dx < -FLIP_DECISION_THRESHOLD and self.facing_right:
            self.facing_right = False
            self._render_frame()
        distance_sq = dx * dx + dy * dy
        if distance_sq <= CHASE_STOP_DISTANCE * CHASE_STOP_DISTANCE:
            return

        distance = distance_sq ** 0.5
        step = max(CHASE_STEP_MIN, min(CHASE_STEP_MAX, int(distance * 0.18)))
        move_x = round(dx / distance * step)
        move_y = round(dy / distance * step)
        self.move(self.x() + move_x, self.y() + move_y)
        if self._chat_window_visible():
            self._position_chat_window()

    def _toggle_chat(self) -> None:
        if not self.chat_window:
            return
        if self._chat_window_visible():
            self.chat_window.hide()
            return
        if not self.is_busy:
            self.chat_window.show_input_mode()
        self._position_chat_window()

    def _position_chat_window(self) -> None:
        if not self.chat_window:
            return
        scale = self.scale_percent / 100.0
        anchor_x = self.x() + round(CHAT_ANCHOR_BASE_X * scale)
        anchor_y = self.y() + round(CHAT_ANCHOR_BASE_Y * scale)
        x = anchor_x - CHAT_TAIL_TIP_X
        y = anchor_y - self.chat_window.height() + CHAT_TAIL_TIP_Y - round(
            CHAT_VERTICAL_LIFT * scale
        ) + CHAT_VERTICAL_NUDGE_PX
        self.chat_window.move(x, y)

    def _make_menu_icon(self, kind: str) -> QIcon:
        pix = QPixmap(18, 18)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        stroke = QPen(QColor("#7b4b62"))
        stroke.setWidth(2)
        stroke.setCapStyle(Qt.RoundCap)
        stroke.setJoinStyle(Qt.RoundJoin)
        painter.setPen(stroke)

        if kind == "dog":
            painter.setBrush(QColor("#fffdf8"))
            left_ear = QPainterPath()
            left_ear.moveTo(5, 6)
            left_ear.lineTo(3, 2)
            left_ear.lineTo(7, 4)
            left_ear.closeSubpath()
            right_ear = QPainterPath()
            right_ear.moveTo(11, 4)
            right_ear.lineTo(16, 2)
            right_ear.lineTo(13, 7)
            right_ear.closeSubpath()
            painter.drawPath(left_ear)
            painter.drawPath(right_ear)

            painter.drawRoundedRect(4, 4, 10, 10, 5, 5)
            painter.setPen(QPen(QColor("#7b4b62"), 1.0))
            painter.drawArc(6, 7, 2, 2, 200 * 16, 140 * 16)
            painter.drawArc(10, 7, 2, 2, 200 * 16, 140 * 16)
            painter.setBrush(QColor("#2c2527"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(8, 9, 2, 2)
            painter.setPen(QPen(QColor("#7b4b62"), 0.9))
            painter.drawLine(9, 11, 9, 14)
        elif kind == "water":
            painter.setBrush(QColor("#d9f0ff"))
            painter.drawRoundedRect(5, 4, 8, 11, 3, 3)
            painter.fillRect(6, 8, 6, 5, QColor("#8fd4ff"))
            painter.drawLine(13, 6, 15, 8)
        elif kind == "movie":
            painter.setBrush(QColor("#fff6fb"))
            painter.drawRoundedRect(3, 3, 12, 9, 2, 2)
            painter.setBrush(QColor("#9fd8ff"))
            painter.drawRoundedRect(5, 5, 8, 5, 1, 1)
        elif kind == "sleep":
            painter.setBrush(QColor("#fff1c7"))
            moon = QPainterPath()
            moon.addEllipse(4, 3, 9, 9)
            cut = QPainterPath()
            cut.addEllipse(7, 2, 9, 9)
            painter.drawPath(moon.subtracted(cut))
            painter.setPen(QPen(QColor("#7b4b62"), 1))
            painter.drawPoint(13, 5)
            painter.drawPoint(14, 8)
            painter.drawPoint(11, 3)
        elif kind == "stand":
            painter.setBrush(QColor("#f7adc0"))
            painter.drawRoundedRect(8, 3, 5, 7, 2, 2)
            painter.drawRoundedRect(5, 10, 9, 4, 2, 2)
            painter.drawLine(9, 14, 9, 16)
            painter.drawLine(10, 14, 10, 16)
            painter.drawLine(11, 14, 11, 16)
            painter.drawLine(10, 16, 6, 17)
            painter.drawLine(10, 16, 14, 17)
            painter.drawLine(10, 16, 8, 18)
            painter.drawLine(10, 16, 12, 18)

        painter.end()
        return QIcon(pix)

    def _trigger_water_action(self) -> None:
        if self.chat_window:
            self.chat_window.hide()
        self._clear_special_actions()
        self._show_water_animation(require_ack=False)

    def _trigger_movie_action(self) -> None:
        self._clear_special_actions()
        self._show_movie_animation(manual_override=True)

    def _trigger_sleep_action(self) -> None:
        if self.movie_action_active:
            self.resize_anchor_mode = "top"
        self._clear_special_actions()
        self._show_sleep_animation()

    def _trigger_sedentary_action(self) -> None:
        if self.chat_window:
            self.chat_window.hide()
        self.sedentary_retry_timer.stop()
        self._clear_special_actions()
        self._show_sedentary_animation(require_ack=False)

    def _show_menu(self, global_pos) -> None:
        self.menu_open = True
        menu = QMenu(self)
        menu.setObjectName("petContextMenu")
        menu.setFont(QFont("Microsoft YaHei UI", 9))
        menu.setAttribute(Qt.WA_TranslucentBackground, True)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setStyleSheet(
            """
            QMenu#petContextMenu {
                background: #fff8fb;
                border: 1px solid #f3c7d8;
                border-radius: 18px;
                padding: 6px;
            }
            QMenu#petContextMenu::item {
                color: #5a2b42;
                background: transparent;
                border-radius: 12px;
                padding: 6px 12px 6px 8px;
                margin: 1px 0;
            }
            QMenu#petContextMenu::item:selected {
                background: #ffe0ec;
                color: #5a2b42;
            }
            QMenu#petContextMenu::separator {
                height: 1px;
                background: #f3d5e0;
                margin: 5px 10px;
            }
            """
        )

        open_chat = QAction("聊天", self)
        open_chat.triggered.connect(self._open_chat_from_menu)
        menu.addAction(open_chat)

        hide_chat = QAction("收起聊天", self)
        hide_chat.triggered.connect(self.chat_window.hide)
        menu.addAction(hide_chat)
        menu.addSeparator()

        replay = QAction("趴狗狗", self)
        replay.setIcon(self._make_menu_icon("dog"))
        replay.triggered.connect(self._restart_animation)
        menu.addAction(replay)

        water_action = QAction("喝水", self)
        water_action.setIcon(self._make_menu_icon("water"))
        water_action.triggered.connect(self._trigger_water_action)
        menu.addAction(water_action)

        movie_action = QAction("看电影", self)
        movie_action.setIcon(self._make_menu_icon("movie"))
        movie_action.triggered.connect(self._trigger_movie_action)
        menu.addAction(movie_action)

        sedentary_action = QAction("伸懒腰", self)
        sedentary_action.setIcon(self._make_menu_icon("stand"))
        sedentary_action.triggered.connect(self._trigger_sedentary_action)
        menu.addAction(sedentary_action)

        sleep_action = QAction("睡觉", self)
        sleep_action.setIcon(self._make_menu_icon("sleep"))
        sleep_action.triggered.connect(self._trigger_sleep_action)
        menu.addAction(sleep_action)
        menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        menu.exec(global_pos)
        self.menu_open = False

    def _open_chat_from_menu(self) -> None:
        if not self.is_busy:
            self.chat_window.show_input_mode()
        self._position_chat_window()

    def _send_message(self, user_input: str) -> None:
        if self.is_busy:
            return

        self.chat_window.begin_thinking()
        self.chat_window.set_busy(True)
        self.is_busy = True

        self.chat_worker = ChatWorker(self.history, user_input)
        self.chat_worker.finished_reply.connect(self._handle_reply)
        self.chat_worker.failed.connect(self._handle_error)
        self.chat_worker.start()

    def _handle_reply(self, user_input: str, reply: str) -> None:
        self.history.append(("human", user_input))
        self.history.append(("ai", reply))
        self.chat_window.show_reply_mode(reply)
        self._position_chat_window()
        self.chat_window.set_busy(False)
        self.is_busy = False

    def _handle_error(self, message: str) -> None:
        self.chat_window.show_reply_mode(message)
        self._position_chat_window()
        self.chat_window.set_busy(False)
        self.is_busy = False

    def eventFilter(self, obj, event):  # noqa: N802
        if obj is self.pet_label:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.press_global_pos = event.globalPosition().toPoint()
                self.drag_started = False
                return True

            if event.type() == QEvent.MouseMove and self.drag_offset and event.buttons() & Qt.LeftButton:
                current = event.globalPosition().toPoint()
                if self.press_global_pos and (current - self.press_global_pos).manhattanLength() > 6:
                    self.drag_started = True
                self.move(current - self.drag_offset)
                if self._chat_window_visible():
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
