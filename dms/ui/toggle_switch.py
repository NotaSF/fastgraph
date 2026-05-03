from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    def __init__(self, label: str = "", parent=None) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)
        self._offset = 0.0

        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(130)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.toggled.connect(self._animate_to_state)
        self._offset = 1.0 if self.isChecked() else 0.0

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(max(30, hint.height()))
        return hint

    def _animate_to_state(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, value: float) -> None:
        self._offset = max(0.0, min(1.0, float(value)))
        self.update()

    offset = pyqtProperty(float, get_offset, set_offset)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_w = 42
        track_h = 22
        margin = 6
        text_gap = 10
        y = (self.height() - track_h) / 2.0

        track_rect = QRectF(margin, y, track_w, track_h)

        off_color = QColor("#2a303b")
        on_color = QColor("#2f7f49")
        border_off = QColor("#4e5a6f")
        border_on = QColor("#47a164")

        bg = on_color if self.isChecked() else off_color
        border = border_on if self.isChecked() else border_off

        p.setPen(border)
        p.setBrush(bg)
        p.drawRoundedRect(track_rect, track_h / 2.0, track_h / 2.0)

        knob_d = 16
        knob_min_x = margin + 3
        knob_max_x = margin + track_w - knob_d - 3
        knob_x = knob_min_x + (knob_max_x - knob_min_x) * self._offset
        knob_y = y + (track_h - knob_d) / 2.0

        p.setPen(QColor("#cfd7e6"))
        p.setBrush(QColor("#e4ebf8"))
        p.drawEllipse(QRectF(knob_x, knob_y, knob_d, knob_d))

        text_rect = QRectF(margin + track_w + text_gap, 0, self.width() - (margin + track_w + text_gap), self.height())
        p.setPen(QColor("#dce6f6") if self.isEnabled() else QColor("#7f8898"))
        p.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.text())

        p.end()
