import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget
from .config import Config
from .engine import BoostEngine
from .game_detector import GameDetector
from .logger import log

STYLE = """
QWidget#menu{background:#101113;border:1px solid #26272b;border-radius:8px}
QLabel{background:transparent;color:#ffffff;font-family:'Segoe UI';font-size:18px;font-weight:600}
QPushButton{background:#1b1c1f;color:#ffffff;border:1px solid #232428;border-radius:6px;
            font-family:'Segoe UI';font-size:15px}
QPushButton:hover{background:#26272b}
QPushButton[on="true"]{border:1px solid #19e6a7;color:#19e6a7}
QPushButton#close{background:transparent;border:none;font-size:15px;color:#e6e6e6}
QPushButton#close:hover{color:#ff5c6c}
"""

class MenuWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("menu")
        self.setWindowTitle("saf1rka_boost")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(250, 160); self.setStyleSheet(STYLE)
        self.cfg = Config(); self.engine = BoostEngine(self.cfg); self.detector = GameDetector(self.cfg)
        self._drag, self._prompted = None, None

        title = QLabel("saf1rka_boost"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        x = QPushButton("X"); x.setObjectName("close"); x.setFixedSize(26, 26); x.clicked.connect(self.close)
        top = QHBoxLayout(); top.addSpacing(26); top.addWidget(title, 1); top.addWidget(x)
        self.btn = QPushButton("Performance Mode"); self.btn.setFixedHeight(54); self.btn.clicked.connect(self.toggle)
        root = QVBoxLayout(self); root.setContentsMargins(22, 12, 22, 22); root.setSpacing(20)
        root.addLayout(top); root.addWidget(self.btn); root.addStretch()

        self.timer = QTimer(self); self.timer.timeout.connect(self._check); self.timer.start(2000)
        self._state(); log.info("saf1rka_boost: меню запущено")

    def toggle(self):
        self.engine.disable() if self.engine.enabled else self.engine.enable()
        self._state()

    def _state(self):
        on = self.engine.enabled
        self.btn.setText("Performance Mode  •  ON" if on else "Performance Mode")
        self.btn.setProperty("on", on)
        self.btn.style().unpolish(self.btn); self.btn.style().polish(self.btn)

    def _check(self):
        try:
            g = self.engine.game
            if g:
                try:
                    alive = g.proc.is_running()
                except psutil.Error:
                    alive = False
                if not alive:
                    log.info("Игра закрыта: %s", g.name)
                    self.engine.game = None; self._prompted = None
                    if self.engine.enabled:
                        self.engine.disable(); self._state()
                return
            f = self.detector.find()
            if not f:
                return
            self.engine.attach_game(f); log.info("Обнаружена игра: %s (%s)", f.name, f.source)
            if self.engine.enabled:
                return
            if self.cfg["auto_enable"]:
                self.engine.enable(); self._state()
            elif self.cfg["ask_on_game"] and self._prompted != f.pid:
                self._prompted = f.pid
                if QMessageBox.question(self, "saf1rka_boost", f"Обнаружена игра {f.name}.\nВключить Performance Mode?") == QMessageBox.StandardButton.Yes:
                    self.engine.enable(); self._state()
        except Exception:
            log.exception("Ошибка проверки игры")

    # перетаскивание окна за любое место
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def closeEvent(self, e):
        self.timer.stop(); self.engine.disable(); log.info("saf1rka_boost закрыт"); e.accept()
