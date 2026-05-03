from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QDialogButtonBox, QVBoxLayout, QGroupBox,
    QLabel, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt
from dms.session import SessionData
from dms.settings_manager import SettingsManager


class SessionDialog(QDialog):
    def __init__(
        self,
        settings: SettingsManager,
        parent=None,
        initial_session: SessionData | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Headphone Metadata")
        self.setMinimumWidth(480)
        self._settings = settings
        self._initial_session = initial_session
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        outer.addWidget(QLabel(
            "<b>Enter headphone / test setup info before measuring.</b>"
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        form = QFormLayout(inner)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def line(placeholder="") -> QLineEdit:
            w = QLineEdit()
            w.setPlaceholderText(placeholder)
            return w

        self._rig = line("e.g. B&K 5128")
        self._brand = line("e.g. Sennheiser")
        self._model = line("e.g. HD 800 S")
        self._model_number = line("optional")
        self._asset_tag = line("optional internal tag")
        self._firmware = line("optional")

        self._eq = QCheckBox("EQ applied")
        self._anc = QCheckBox("ANC / transparency active")
        self._anc_name = line("mode name if applicable")

        self._form_factor = QComboBox()
        self._form_factor.addItems(["over-ear", "on-ear", "in-ear"])

        self._open_back = QComboBox()
        self._open_back.addItems(["open back", "closed back", "semi-open"])

        self._pads = line("e.g. foam tips size M")
        self._connection = QComboBox()
        self._connection.addItems([
            "wired analog",
            "wired USB",
            "bluetooth",
            "wireless dongle",
            "other",
        ])

        form.addRow("Rig *", self._rig)
        form.addRow("Brand *", self._brand)
        form.addRow("Model *", self._model)
        form.addRow("Model Number", self._model_number)
        form.addRow("Asset Tag", self._asset_tag)
        form.addRow("Firmware", self._firmware)
        form.addRow("", self._eq)
        form.addRow("", self._anc)
        form.addRow("ANC Mode Name", self._anc_name)
        form.addRow("Form Factor", self._form_factor)
        form.addRow("Acoustic Type", self._open_back)
        form.addRow("Pads / Tips Notes", self._pads)
        form.addRow("Connection", self._connection)
        self._load_initial_values()

        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #ff6666;")
        outer.addWidget(self._status)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        outer.addWidget(btns)

    def _validate_and_accept(self) -> None:
        missing = []
        if not self._rig.text().strip():
            missing.append("Rig")
        if not self._brand.text().strip():
            missing.append("Brand")
        if not self._model.text().strip():
            missing.append("Model")
        if missing:
            self._status.setText(f"Required: {', '.join(missing)}")
            return
        self.accept()

    def _load_initial_values(self) -> None:
        if self._initial_session is None:
            return

        s = self._initial_session
        self._rig.setText(s.rig)
        self._brand.setText(s.brand)
        self._model.setText(s.model)
        self._model_number.setText(s.model_number)
        self._asset_tag.setText(s.asset_tag)
        self._firmware.setText(s.firmware)
        self._eq.setChecked(s.eq_applied)
        self._anc.setChecked(s.anc_mode)
        self._anc_name.setText(s.anc_mode_name)
        self._form_factor.setCurrentText(s.form_factor)
        self._open_back.setCurrentText("open back" if s.open_back else "closed back")
        self._pads.setText(s.pads_notes)
        self._connection.setCurrentText(s.connection)

    def session_data(self) -> SessionData:
        return SessionData(
            rig=self._rig.text().strip(),
            brand=self._brand.text().strip(),
            model=self._model.text().strip(),
            model_number=self._model_number.text().strip(),
            asset_tag=self._asset_tag.text().strip(),
            firmware=self._firmware.text().strip(),
            eq_applied=self._eq.isChecked(),
            anc_mode=self._anc.isChecked(),
            anc_mode_name=self._anc_name.text().strip(),
            form_factor=self._form_factor.currentText(),
            open_back=self._open_back.currentText() == "open back",
            pads_notes=self._pads.text().strip(),
            connection=self._connection.currentText(),
        )
