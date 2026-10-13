# interfaz.py — Jarvis MK2 GUI (PySide6)
import sys
import math
import json
import os
import threading
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect, QLineEdit, QScrollArea, QDialog,
    QFormLayout, QComboBox, QCheckBox, QSlider, QTabWidget,
    QDialogButtonBox, QSpinBox,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QObject, QPropertyAnimation,
    QEasingCurve, QPoint, QSize, Property,
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient,
    QFont, QFontDatabase, QIcon, QPainterPath, QRadialGradient,
    QTextCursor, QKeySequence, QShortcut,
)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

# ── Paleta de colores ──────────────────────────────────────────────────────────
C = {
    "bg":         "#060810",
    "bg2":        "#0a0e1a",
    "panel":      "#0d1220",
    "panel2":     "#111828",
    "cyan":       "#00c8ff",
    "cyan_dim":   "#003d52",
    "cyan_glow":  "#00a8d4",
    "blue":       "#0055ff",
    "blue_dim":   "#001540",
    "green":      "#00ff88",
    "green_dim":  "#003322",
    "yellow":     "#ffcc00",
    "red":        "#ff3355",
    "white":      "#d4e8f0",
    "gray":       "#2a3a4a",
    "gray2":      "#1a2535",
    "text":       "#8ab4c8",
    "text2":      "#4a6a7a",
}

QSS = f"""
QMainWindow, QWidget#root {{
    background: {C['bg']};
}}
QWidget {{
    color: {C['white']};
    font-family: 'Consolas', 'Courier New', monospace;
}}
QTextEdit {{
    background: {C['panel']};
    border: 1px solid {C['cyan_dim']};
    border-radius: 8px;
    color: {C['white']};
    font-size: 12px;
    padding: 8px;
    selection-background-color: {C['cyan_dim']};
}}
QLineEdit {{
    background: {C['panel2']};
    border: 1px solid {C['cyan_dim']};
    border-radius: 6px;
    color: {C['white']};
    font-size: 13px;
    padding: 8px 12px;
    selection-background-color: {C['cyan_dim']};
}}
QLineEdit:focus {{
    border: 1px solid {C['cyan']};
}}
QPushButton {{
    background: {C['panel2']};
    border: 1px solid {C['cyan_dim']};
    border-radius: 6px;
    color: {C['cyan']};
    font-size: 12px;
    font-weight: bold;
    padding: 8px 16px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background: {C['cyan_dim']};
    border: 1px solid {C['cyan']};
}}
QPushButton:pressed {{
    background: {C['blue_dim']};
}}
QPushButton#btn_activar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #003866, stop:1 #005a8a);
    border: 1px solid {C['cyan']};
    border-radius: 8px;
    color: {C['cyan']};
    font-size: 14px;
    font-weight: bold;
    padding: 12px;
    letter-spacing: 2px;
}}
QPushButton#btn_activar:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['cyan_dim']}, stop:1 #006688);
    border: 1px solid {C['cyan_glow']};
}}
QScrollBar:vertical {{
    background: {C['bg2']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C['cyan_dim']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C['cyan']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QLabel#titulo {{
    color: {C['cyan']};
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 6px;
}}
QLabel#subtitulo {{
    color: {C['text2']};
    font-size: 9px;
    letter-spacing: 3px;
}}
QLabel#estado_label {{
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
}}
QFrame#separator {{
    background: {C['cyan_dim']};
    max-height: 1px;
}}
QFrame#panel_frame {{
    background: {C['panel']};
    border: 1px solid {C['cyan_dim']};
    border-radius: 10px;
}}
QTabWidget::pane {{
    border: 1px solid {C['cyan_dim']};
    border-radius: 6px;
    background: {C['panel']};
}}
QTabBar::tab {{
    background: {C['panel2']};
    color: {C['text2']};
    padding: 6px 14px;
    border: 1px solid {C['cyan_dim']};
    border-bottom: none;
    font-size: 10px;
    letter-spacing: 1px;
}}
QTabBar::tab:selected {{
    background: {C['panel']};
    color: {C['cyan']};
    border-color: {C['cyan_dim']};
}}
QDialog {{
    background: {C['bg2']};
}}
QComboBox {{
    background: {C['panel2']};
    border: 1px solid {C['cyan_dim']};
    border-radius: 4px;
    color: {C['white']};
    padding: 4px 8px;
}}
QComboBox::drop-down {{
    border: none;
}}
QCheckBox {{
    color: {C['white']};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {C['cyan_dim']};
    border-radius: 3px;
    background: {C['panel2']};
}}
QCheckBox::indicator:checked {{
    background: {C['cyan_dim']};
    border-color: {C['cyan']};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: {C['gray']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px; height: 12px;
    background: {C['cyan']};
    border-radius: 6px;
    margin: -4px 0;
}}
QSlider::sub-page:horizontal {{
    background: {C['cyan_dim']};
    border-radius: 2px;
}}
"""


# ── Widget de esfera animada ───────────────────────────────────────────────────
class EsferaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._angulo = 0
        self._pulso = 0.0
        self._pulso_dir = 1
        self._estado = "esperando"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_estado(self, estado: str):
        self._estado = estado
        self.update()

    def _tick(self):
        self._angulo = (self._angulo + 2) % 360
        self._pulso += 0.03 * self._pulso_dir
        if self._pulso >= 1.0 or self._pulso <= 0.0:
            self._pulso_dir *= -1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() // 2, self.height() // 2
        r = 85

        colores = {
            "esperando":  QColor(C["yellow"]),
            "escuchando": QColor(C["green"]),
            "hablando":   QColor(C["cyan"]),
            "procesando": QColor(C["blue"]),
            "pensando":   QColor("#aa44ff"),
        }
        color = colores.get(self._estado, QColor(C["cyan"]))

        glow_alpha = int(30 + 20 * self._pulso)
        glow_color = QColor(color)
        glow_color.setAlpha(glow_alpha)
        for gr in range(3):
            gpen = QPen(glow_color, 3 - gr)
            p.setPen(gpen)
            p.drawEllipse(cx - r - gr*6, cy - r - gr*6,
                          (r + gr*6)*2, (r + gr*6)*2)

        for i, radio in enumerate([r, r - 18, r - 36]):
            alpha = 180 if i == 0 else 80 - i * 20
            c2 = QColor(color)
            c2.setAlpha(alpha)
            pen = QPen(c2, 1.0 if i > 0 else 1.5)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx - radio, cy - radio, radio * 2, radio * 2)

        pen_arc = QPen(color, 2.5)
        pen_arc.setCapStyle(Qt.RoundCap)
        p.setPen(pen_arc)
        rect_arc = (cx - r + 2, cy - r + 2, (r - 2) * 2, (r - 2) * 2)
        p.drawArc(*rect_arc, int(self._angulo * 16), int(110 * 16))
        p.drawArc(*rect_arc, int((self._angulo + 180) * 16), int(50 * 16))

        pen2 = QPen(color, 1.2)
        pen2.setCapStyle(Qt.RoundCap)
        c3 = QColor(color)
        c3.setAlpha(120)
        pen2.setColor(c3)
        p.setPen(pen2)
        p.drawArc(*rect_arc, int((self._angulo + 90) * 16), int(70 * 16))

        for i in range(6):
            ang_rad = math.radians(self._angulo + i * 60)
            px = cx + r * math.cos(ang_rad)
            py = cy + r * math.sin(ang_rad)
            tam = 4 if i == 0 else 2
            p.setPen(Qt.NoPen)
            dot_color = QColor(color)
            dot_color.setAlpha(255 if i == 0 else 140)
            p.setBrush(QBrush(dot_color))
            p.drawEllipse(int(px - tam), int(py - tam), tam * 2, tam * 2)

        p.setPen(QPen(color, 1))
        font = QFont("Consolas", 18, QFont.Bold)
        p.setFont(font)
        p.drawText(cx - 15, cy - 18, 30, 30, Qt.AlignCenter, "◈")

        estados_texto = {
            "esperando":  "STAND BY",
            "escuchando": "LISTENING",
            "hablando":   "SPEAKING",
            "procesando": "PROCESSING",
            "pensando":   "THINKING",
        }
        txt = estados_texto.get(self._estado, "ONLINE")
        font2 = QFont("Consolas", 7, QFont.Bold)
        p.setFont(font2)
        txt_color = QColor(color)
        txt_color.setAlpha(200)
        p.setPen(QPen(txt_color))
        p.drawText(cx - 40, cy + 22, 80, 16, Qt.AlignCenter, txt)
        p.end()


# ── Señales thread-safe ────────────────────────────────────────────────────────
class JarvisSignals(QObject):
    user_speech    = Signal(str)
    user_partial   = Signal(str)   # texto parcial mientras el usuario habla
    jarvis_resp    = Signal(str)
    state_change   = Signal(str)
    vosk_state     = Signal(str)   # loading | ready | listening | off
    sistema        = Signal(str)
    log_line       = Signal(str, str)
    tasks_updated  = Signal()
    show_window    = Signal()      # restaurar la ventana desde tray / segundo lanzamiento


# ── Diálogo de configuración ──────────────────────────────────────────────────
class DialogConfig(QDialog):
    def __init__(self, jarvis_ref, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración — Jarvis MK2")
        self.setFixedSize(520, 480)
        self.setStyleSheet(QSS)
        self._jarvis = jarvis_ref
        self._cfg = self._load_config()
        self._build_ui()

    def _load_config(self) -> dict:
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        try:
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self._cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.addTab(self._tab_ia(), "IA")
        tabs.addTab(self._tab_voz(), "VOZ")
        tabs.addTab(self._tab_gui(), "INTERFAZ")
        tabs.addTab(self._tab_apis(), "APIs")
        layout.addWidget(tabs)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.setStyleSheet(f"color: {C['cyan']};")
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    # ── Tab IA ────────────────────────────────────────────────────────────────
    def _tab_ia(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        self._cmb_motor = QComboBox()
        self._cmb_motor.addItems(["ollama", "gemini"])
        self._cmb_motor.setCurrentText(
            self._cfg.get("orquestador", {}).get("default", "ollama")
        )
        form.addRow("Motor por defecto:", self._cmb_motor)

        self._inp_ollama_modelo = QLineEdit(
            self._cfg.get("ollama", {}).get("modelo", "mistral")
        )
        form.addRow("Modelo Ollama:", self._inp_ollama_modelo)

        self._inp_ollama_url = QLineEdit(
            self._cfg.get("ollama", {}).get("url", "http://localhost:11434/api/chat")
        )
        form.addRow("URL Ollama:", self._inp_ollama_url)

        self._cmb_gemini_chat = QComboBox()
        gemini_models = [
            "gemini-2.5-flash",       # rápido, recomendado
            "gemini-2.5-flash-lite",  # más ligero, menor cuota
            "gemini-2.5-pro",         # más capaz, más lento
        ]
        self._cmb_gemini_chat.addItems(gemini_models)
        self._cmb_gemini_chat.setCurrentText(
            self._cfg.get("gemini", {}).get("modelo_chat", "gemini-2.5-flash")
        )
        form.addRow("Modelo Gemini:", self._cmb_gemini_chat)

        self._spin_umbral = QSpinBox()
        self._spin_umbral.setRange(1, 10)
        self._spin_umbral.setValue(
            self._cfg.get("orquestador", {}).get("umbral_complejidad", 6)
        )
        self._spin_umbral.setStyleSheet(f"background:{C['panel2']}; color:{C['white']}; border:1px solid {C['cyan_dim']};")
        form.addRow("Umbral complejidad (1-10):", self._spin_umbral)

        return w

    # ── Tab Voz ───────────────────────────────────────────────────────────────
    def _tab_voz(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        # Selector unificado: una sola voz de Edge/Gemini/pyttsx3
        from modulos.sintesis_voz import VOCES_DISPONIBLES
        self._cmb_voz = QComboBox()
        for v in VOCES_DISPONIBLES:
            self._cmb_voz.addItem(v["label"], v["id"])
        voz_id_actual = self._cfg.get("voz", {}).get("voz_id", "edge_gonzalo")
        for i in range(self._cmb_voz.count()):
            if self._cmb_voz.itemData(i) == voz_id_actual:
                self._cmb_voz.setCurrentIndex(i)
                break
        form.addRow("Voz de Jarvis:", self._cmb_voz)

        lbl_info = QLabel(
            "Edge: rápido, sin cuota.  Gemini: mejor calidad pero usa cuota API.\n"
            "pyttsx3: offline, voces de Windows."
        )
        lbl_info.setStyleSheet(f"color: {C['text2']}; font-size: 9px;")
        form.addRow("", lbl_info)

        self._chk_silencioso = QCheckBox("Modo silencioso al iniciar")
        self._chk_silencioso.setChecked(
            self._cfg.get("voz", {}).get("modo_silencioso", False)
        )
        form.addRow("", self._chk_silencioso)

        return w

    # ── Tab Interfaz ──────────────────────────────────────────────────────────
    def _tab_gui(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        self._sld_opacidad = QSlider(Qt.Horizontal)
        self._sld_opacidad.setRange(50, 100)
        self._sld_opacidad.setValue(
            int(self._cfg.get("gui", {}).get("opacidad", 0.97) * 100)
        )
        form.addRow("Opacidad ventana:", self._sld_opacidad)

        self._chk_encima = QCheckBox("Siempre encima")
        self._chk_encima.setChecked(
            self._cfg.get("gui", {}).get("siempre_encima", False)
        )
        form.addRow("", self._chk_encima)

        lbl_info = QLabel("Los cambios de interfaz se aplican al reiniciar.")
        lbl_info.setStyleSheet(f"color: {C['text2']}; font-size: 9px;")
        form.addRow("", lbl_info)

        return w

    # ── Tab APIs ──────────────────────────────────────────────────────────────
    def _tab_apis(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        import os as _os
        gemini_key = _os.getenv("GEMINI_API_KEY", "")
        self._inp_gemini_key = QLineEdit(gemini_key)
        self._inp_gemini_key.setEchoMode(QLineEdit.Password)
        self._inp_gemini_key.setPlaceholderText("sk-... (se guarda en .env)")
        form.addRow("Gemini API Key:", self._inp_gemini_key)

        weather_key = _os.getenv("WEATHER_API_KEY", "")
        self._inp_weather_key = QLineEdit(weather_key)
        self._inp_weather_key.setEchoMode(QLineEdit.Password)
        self._inp_weather_key.setPlaceholderText("OpenWeatherMap key")
        form.addRow("Weather API Key:", self._inp_weather_key)

        lbl_env = QLabel("Las API keys se guardan en el archivo .env")
        lbl_env.setStyleSheet(f"color: {C['text2']}; font-size: 9px;")
        form.addRow("", lbl_env)

        return w

    # ── Guardar ───────────────────────────────────────────────────────────────
    def _on_save(self):
        # ── Recoger valores del formulario ──────────────────────────────────
        motor      = self._cmb_motor.currentText()
        ol_modelo  = self._inp_ollama_modelo.text().strip()
        ol_url     = self._inp_ollama_url.text().strip()
        gm_modelo  = self._cmb_gemini_chat.currentText()
        voz_id     = self._cmb_voz.currentData()
        silencioso = self._chk_silencioso.isChecked()
        opacidad   = self._sld_opacidad.value() / 100
        siempre_encima = self._chk_encima.isChecked()

        # ── Persistir en config.json ─────────────────────────────────────────
        self._cfg.setdefault("orquestador", {})["default"] = motor
        self._cfg.setdefault("ollama", {})["modelo"] = ol_modelo
        self._cfg.setdefault("ollama", {})["url"] = ol_url
        self._cfg.setdefault("gemini", {})["modelo_chat"] = gm_modelo
        self._cfg.setdefault("voz", {})["voz_id"] = voz_id
        self._cfg.setdefault("voz", {})["modo_silencioso"] = silencioso
        self._cfg.setdefault("gui", {})["opacidad"] = opacidad
        self._cfg.setdefault("gui", {})["siempre_encima"] = siempre_encima
        self._save_config()

        # ── Persistir API keys en .env ───────────────────────────────────────
        self._update_env()

        # ── Aplicar EN VIVO a Jarvis sin reiniciar ───────────────────────────
        if self._jarvis:
            ja = self._jarvis

            # Motor IA y modelo
            ja.ia.motor = motor
            if ol_modelo and ol_modelo != ja.ia.modelo_ollama:
                ja.ia.modelo_ollama = ol_modelo
                log.info(f"[Config] Modelo Ollama → {ol_modelo}")
            if gm_modelo and gm_modelo != ja.ia.modelo_gemini:
                ja.ia.modelo_gemini = gm_modelo
                log.info(f"[Config] Modelo Gemini → {gm_modelo}")

            # URL Ollama
            if ol_url:
                ja.ia.url_ollama = ol_url

            # Voz TTS unificada
            if voz_id:
                ja.tts.set_voz(voz_id)

            # Silencioso
            if silencioso:
                ja.tts.activar_silencioso()
            else:
                ja.tts.desactivar_silencioso()

            # Reset GeminiManager para releer API key nueva
            try:
                from modulos.gemini_manager import gemini as _gm_acc
                _gm_acc().resetear()
                ja.ia.gemini_key = _gm_acc().api_key
                ja.ia.gemini_ok = bool(ja.ia.gemini_key)
            except Exception:
                pass

        self.accept()

    def _update_env(self):
        env_path = os.path.join(os.path.dirname(_CONFIG_PATH), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                lines = f.readlines()

        def _set_key(lines, key, value):
            if not value:
                return lines
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    return lines
            lines.append(f"{key}={value}\n")
            return lines

        gemini_val = self._inp_gemini_key.text().strip()
        weather_val = self._inp_weather_key.text().strip()
        lines = _set_key(lines, "GEMINI_API_KEY", gemini_val)
        lines = _set_key(lines, "WEATHER_API_KEY", weather_val)

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)


# ── Panel de tareas del agente ─────────────────────────────────────────────────
class PanelTareas(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel_frame")
        self.setFixedHeight(150)
        self._jarvis = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        lbl_titulo = QLabel("TAREAS DEL AGENTE")
        lbl_titulo.setStyleSheet(f"color: {C['text2']}; font-size: 8px; letter-spacing: 2px;")
        layout.addWidget(lbl_titulo)

        self._lista = QTextEdit()
        self._lista.setReadOnly(True)
        self._lista.setStyleSheet(
            f"background: {C['bg2']}; border: none; font-size: 10px; padding: 2px;"
        )
        layout.addWidget(self._lista)

        btn_row = QHBoxLayout()
        self._btn_cancelar = QPushButton("CANCELAR ÚLTIMA")
        self._btn_cancelar.setFixedHeight(24)
        self._btn_cancelar.setStyleSheet(
            f"font-size: 9px; padding: 2px 8px; color: {C['red']}; border-color: {C['red']};"
        )
        self._btn_cancelar.clicked.connect(self._cancelar_ultima)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_cancelar)
        layout.addLayout(btn_row)

    def conectar_jarvis(self, jarvis):
        self._jarvis = jarvis

    def actualizar(self):
        if not self._jarvis:
            return
        tareas = self._jarvis.task_queue.get_all()
        if not tareas:
            self._lista.setPlainText("Sin tareas activas.")
            return

        colores_estado = {
            "pending":   C["yellow"],
            "running":   C["cyan"],
            "completed": C["green"],
            "failed":    C["red"],
            "cancelled": C["gray"],
        }
        html = ""
        for t in tareas[-6:]:  # últimas 6
            color = colores_estado.get(t["status"], C["white"])
            estado = t["status"].upper()
            goal = t["goal"][:45]
            html += (
                f'<span style="color:{color};">[{estado}]</span> '
                f'<span style="color:{C["white"]};">{goal}</span><br>'
            )
        self._lista.setHtml(html)

    def _cancelar_ultima(self):
        if not self._jarvis:
            return
        tareas = self._jarvis.task_queue.get_all()
        for t in reversed(tareas):
            if t["status"] in ("pending", "running"):
                self._jarvis.task_queue.cancel(t["task_id"])
                break


# ── Ventana principal ──────────────────────────────────────────────────────────
class InterfazJarvis(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S  MK2")
        self.setFixedSize(1000, 700)
        self.setStyleSheet(QSS)

        self._jarvis = None
        self._signals = JarvisSignals()
        self._signals.user_speech.connect(self._on_user_speech)
        self._signals.user_partial.connect(self._on_user_partial)
        self._signals.jarvis_resp.connect(self._on_jarvis_response)
        self._signals.state_change.connect(self._on_state_change)
        self._signals.vosk_state.connect(self._on_vosk_state)
        self._signals.sistema.connect(self._on_sistema)
        self._signals.show_window.connect(self._tray_show)
        self._signals.log_line.connect(self._append_chat)
        self._signals.tasks_updated.connect(self._actualizar_tareas)

        self._estado_actual = "esperando"
        self._silencioso = False
        self._partial_active = False  # hay un bloque de partial visible en chat

        self._build_ui()
        self._timer_hora = QTimer(self)
        self._timer_hora.timeout.connect(self._update_hora)
        self._timer_hora.start(1000)
        self._update_hora()

        self._timer_tareas = QTimer(self)
        self._timer_tareas.timeout.connect(self._actualizar_tareas)
        self._timer_tareas.start(2000)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background: {C['bg2']}; border-bottom: 1px solid {C['cyan_dim']};")
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(24, 0, 24, 0)

        lbl_titulo = QLabel("◈  J.A.R.V.I.S  ◈")
        lbl_titulo.setObjectName("titulo")
        hlay.addWidget(lbl_titulo)

        hlay.addStretch()

        lbl_sub = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM  ·  MK2")
        lbl_sub.setObjectName("subtitulo")
        lbl_sub.setStyleSheet(f"color: {C['text2']}; font-size: 8px; letter-spacing: 3px;")
        hlay.addWidget(lbl_sub)

        hlay.addStretch()

        self._lbl_hora = QLabel()
        self._lbl_hora.setStyleSheet(f"color: {C['text2']}; font-size: 10px; letter-spacing: 1px;")
        hlay.addWidget(self._lbl_hora)

        root_layout.addWidget(header)

        # ── Body ─────────────────────────────────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)

        # ── Panel izquierdo ───────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(260)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Estado
        estado_frame = QFrame()
        estado_frame.setObjectName("panel_frame")
        estado_frame.setFixedHeight(56)
        ef_lay = QVBoxLayout(estado_frame)
        ef_lay.setContentsMargins(12, 6, 12, 6)
        ef_lay.setSpacing(2)
        lbl_est_titulo = QLabel("ESTADO DEL SISTEMA")
        lbl_est_titulo.setAlignment(Qt.AlignCenter)
        lbl_est_titulo.setStyleSheet(f"color: {C['text2']}; font-size: 8px; letter-spacing: 2px;")
        ef_lay.addWidget(lbl_est_titulo)
        self._lbl_estado = QLabel("● ESPERANDO")
        self._lbl_estado.setObjectName("estado_label")
        self._lbl_estado.setAlignment(Qt.AlignCenter)
        self._lbl_estado.setStyleSheet(f"color: {C['yellow']};")
        ef_lay.addWidget(self._lbl_estado)
        left_layout.addWidget(estado_frame)

        # Esfera
        esfera_container = QWidget()
        esfera_lay = QHBoxLayout(esfera_container)
        esfera_lay.setContentsMargins(0, 0, 0, 0)
        self._esfera = EsferaWidget()
        esfera_lay.addWidget(self._esfera, alignment=Qt.AlignCenter)
        left_layout.addWidget(esfera_container)

        # Motor IA activo
        motor_frame = QFrame()
        motor_frame.setObjectName("panel_frame")
        motor_frame.setFixedHeight(40)
        mf_lay = QHBoxLayout(motor_frame)
        mf_lay.setContentsMargins(12, 0, 12, 0)
        lbl_motor_t = QLabel("MOTOR IA:")
        lbl_motor_t.setStyleSheet(f"color: {C['text2']}; font-size: 9px;")
        mf_lay.addWidget(lbl_motor_t)
        self._lbl_motor = QLabel("OLLAMA")
        self._lbl_motor.setStyleSheet(f"color: {C['green']}; font-size: 10px; font-weight: bold;")
        mf_lay.addStretch()
        mf_lay.addWidget(self._lbl_motor)
        left_layout.addWidget(motor_frame)

        # Indicador Vosk (micrófono / STT)
        vosk_frame = QFrame()
        vosk_frame.setObjectName("panel_frame")
        vosk_frame.setFixedHeight(40)
        vf_lay = QHBoxLayout(vosk_frame)
        vf_lay.setContentsMargins(12, 0, 12, 0)
        lbl_vosk_t = QLabel("MICRÓFONO:")
        lbl_vosk_t.setStyleSheet(f"color: {C['text2']}; font-size: 9px;")
        vf_lay.addWidget(lbl_vosk_t)
        vf_lay.addStretch()
        self._lbl_vosk = QLabel("● APAGADO")
        self._lbl_vosk.setStyleSheet(f"color: {C['text2']}; font-size: 10px; font-weight: bold;")
        vf_lay.addWidget(self._lbl_vosk)
        left_layout.addWidget(vosk_frame)

        # Botón activar
        self._btn_activar = QPushButton("⚡  ACTIVAR JARVIS")
        self._btn_activar.setObjectName("btn_activar")
        self._btn_activar.setFixedHeight(46)
        self._btn_activar.clicked.connect(self._activar_manual)
        left_layout.addWidget(self._btn_activar)

        # Fila botones secundarios
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self._btn_silencioso = QPushButton("🔊 VOZ")
        self._btn_silencioso.setFixedHeight(32)
        self._btn_silencioso.clicked.connect(self._toggle_silencioso)
        row1.addWidget(self._btn_silencioso)

        self._btn_motor = QPushButton("🤖 GEMINI")
        self._btn_motor.setFixedHeight(32)
        self._btn_motor.clicked.connect(self._toggle_motor)
        row1.addWidget(self._btn_motor)
        left_layout.addLayout(row1)

        # Botón configuración
        btn_config = QPushButton("⚙  CONFIGURACIÓN")
        btn_config.setFixedHeight(32)
        btn_config.clicked.connect(self._abrir_config)
        left_layout.addWidget(btn_config)

        left_layout.addStretch()

        # Panel de tareas
        self._panel_tareas = PanelTareas()
        left_layout.addWidget(self._panel_tareas)

        body_layout.addWidget(left)

        # ── Panel derecho (chat) ───────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        lbl_consola = QLabel("CONSOLA DE INTERACCIÓN")
        lbl_consola.setStyleSheet(f"color: {C['text2']}; font-size: 8px; letter-spacing: 2px;")
        right_layout.addWidget(lbl_consola)

        self._chat = QTextEdit()
        self._chat.setReadOnly(True)
        self._chat.setLineWrapMode(QTextEdit.WidgetWidth)
        right_layout.addWidget(self._chat)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._txt_input = QLineEdit()
        self._txt_input.setPlaceholderText("Escribe un comando o presiona Enter para enviar...")
        self._txt_input.setFixedHeight(38)
        self._txt_input.returnPressed.connect(self._enviar_texto)
        input_row.addWidget(self._txt_input)

        btn_send = QPushButton("ENVIAR")
        btn_send.setFixedSize(80, 38)
        btn_send.clicked.connect(self._enviar_texto)
        input_row.addWidget(btn_send)

        btn_clear = QPushButton("LIMPIAR")
        btn_clear.setFixedSize(80, 38)
        btn_clear.clicked.connect(self._limpiar_chat)
        input_row.addWidget(btn_clear)

        right_layout.addLayout(input_row)
        body_layout.addWidget(right)
        root_layout.addWidget(body)

    # ── Slots GUI ──────────────────────────────────────────────────────────────
    def _append_chat(self, texto: str, tipo: str = ""):
        colores_tipo = {
            "usuario": C["cyan"],
            "jarvis":  C["green"],
            "sistema": C["yellow"],
            "error":   C["red"],
            "agente":  "#aa44ff",
        }
        color = colores_tipo.get(tipo, C["white"])
        self._chat.moveCursor(QTextCursor.End)
        self._chat.insertHtml(
            f'<span style="color:{color}; font-family:Consolas; font-size:12px;">'
            f'{texto}</span><br>'
        )
        self._chat.moveCursor(QTextCursor.End)

    def _on_user_partial(self, texto: str):
        """Muestra el texto parcial mientras el usuario habla, reemplazando la línea anterior."""
        if not texto:
            return
        self._chat.moveCursor(QTextCursor.End)
        if self._partial_active:
            # Borrar la última línea (el partial anterior)
            cursor = self._chat.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # quita el <br> previo
        color = C.get("text2", "#4a6a7a")
        self._chat.moveCursor(QTextCursor.End)
        self._chat.insertHtml(
            f'<span style="color:{color}; font-style:italic; font-family:Consolas; font-size:12px;">'
            f'TÚ (escuchando): {texto}…</span><br>'
        )
        self._chat.moveCursor(QTextCursor.End)
        self._partial_active = True

    def _clear_partial(self):
        if not self._partial_active:
            return
        cursor = self._chat.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self._partial_active = False

    def _on_user_speech(self, texto: str):
        # Si había un partial vivo, reemplazarlo por el texto final
        self._clear_partial()
        self._append_chat(f"TÚ: {texto}", "usuario")
        self._on_state_change("procesando")

    def _on_jarvis_response(self, texto: str):
        self._clear_partial()
        self._append_chat(f"JARVIS: {texto}", "jarvis")

    def _on_state_change(self, estado: str):
        self._estado_actual = estado
        self._esfera.set_estado(estado)
        configs = {
            "esperando":  ("● ESPERANDO",   C["yellow"]),
            "escuchando": ("● ESCUCHANDO",  C["green"]),
            "hablando":   ("● HABLANDO",    C["cyan"]),
            "procesando": ("● PROCESANDO",  C["blue"]),
            "pensando":   ("● PENSANDO",    "#aa44ff"),
        }
        txt, color = configs.get(estado, ("● ONLINE", C["white"]))
        self._lbl_estado.setText(txt)
        self._lbl_estado.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: bold; letter-spacing: 2px;"
        )

    def _on_vosk_state(self, estado: str):
        """Actualiza el indicador de Vosk: loading | ready | listening | off"""
        configs = {
            "loading":   ("● ENCENDIENDO", C["yellow"]),
            "ready":     ("● LISTO",       C["cyan"]),
            "listening": ("● ESCUCHANDO",  C["green"]),
            "off":       ("● APAGADO",     C["text2"]),
        }
        txt, color = configs.get(estado, ("● ?", C["text2"]))
        self._lbl_vosk.setText(txt)
        self._lbl_vosk.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: bold;"
        )

    def _on_sistema(self, texto: str):
        self._append_chat(f"[SYS] {texto}", "sistema")

    def _update_hora(self):
        hora = datetime.datetime.now().strftime("%H:%M:%S  ·  %d/%m/%Y")
        self._lbl_hora.setText(hora)

    def _actualizar_tareas(self):
        self._panel_tareas.actualizar()

    def _activar_manual(self):
        if self._jarvis and not self._jarvis.en_conversacion:
            hilo = threading.Thread(target=self._jarvis.activar, daemon=True)
            hilo.start()

    def _toggle_silencioso(self):
        if self._jarvis:
            self._silencioso = not self._silencioso
            if self._silencioso:
                self._jarvis.tts.activar_silencioso()
                self._btn_silencioso.setText("🔇 MUDO")
                self._btn_silencioso.setStyleSheet(f"color: {C['gray']}; border-color: {C['gray']};")
            else:
                self._jarvis.tts.desactivar_silencioso()
                self._btn_silencioso.setText("🔊 VOZ")
                self._btn_silencioso.setStyleSheet("")

    def _toggle_motor(self):
        if self._jarvis:
            if self._jarvis.ia.motor == "ollama":
                self._jarvis.ia.motor = "gemini"
                self._lbl_motor.setText("GEMINI")
                self._lbl_motor.setStyleSheet(
                    f"color: {C['cyan']}; font-size: 10px; font-weight: bold;"
                )
                self._btn_motor.setText("🤖 OLLAMA")
            else:
                self._jarvis.ia.motor = "ollama"
                self._lbl_motor.setText("OLLAMA")
                self._lbl_motor.setStyleSheet(
                    f"color: {C['green']}; font-size: 10px; font-weight: bold;"
                )
                self._btn_motor.setText("🤖 GEMINI")

    def _abrir_config(self):
        dlg = DialogConfig(self._jarvis, parent=self)
        if dlg.exec():
            self._on_sistema("Configuración guardada.")

    def _enviar_texto(self):
        texto = self._txt_input.text().strip()
        if not texto or not self._jarvis:
            return
        self._txt_input.clear()
        self._on_user_speech(texto)
        def _ejecutar():
            self._on_state_change("procesando")
            resp = self._jarvis._ejecutar_comando(texto)
            if resp:
                self._signals.jarvis_resp.emit(resp)
                self._jarvis.hablar(resp)
            self._on_state_change("esperando")
        threading.Thread(target=_ejecutar, daemon=True).start()

    def _limpiar_chat(self):
        self._chat.clear()

    # ── API pública ────────────────────────────────────────────────────────────
    def conectar_jarvis(self, jarvis_instance):
        self._jarvis = jarvis_instance
        self._panel_tareas.conectar_jarvis(jarvis_instance)
        # Notificar que la GUI ya está visible al arrancar (Jarvis ya está creado)
        try:
            jarvis_instance.set_gui_visible(True)
        except Exception:
            pass

    def get_callbacks(self) -> dict:
        return {
            "on_user_speech":     lambda t: self._signals.user_speech.emit(t),
            "on_user_partial":    lambda t: self._signals.user_partial.emit(t),
            "on_jarvis_response": lambda t: self._signals.jarvis_resp.emit(t),
            "on_state_change":    lambda s: self._signals.state_change.emit(s),
            "on_vosk_state":      lambda s: self._signals.vosk_state.emit(s),
            "on_sistema":         lambda t: self._signals.sistema.emit(t),
            "on_show_window":     lambda: self._signals.show_window.emit(),
        }

    # ── System tray: cerrar oculta, no mata el proceso ────────────────────────
    def _setup_tray(self):
        # Buscar icono real; si no existe, usar uno estándar de Qt (siempre visible)
        candidates = [
            os.path.join(os.path.dirname(__file__), "jarvis.ico"),
            os.path.join(os.path.dirname(__file__), "icon.ico"),
            os.path.join(os.path.dirname(__file__), "icon.png"),
            os.path.join(os.path.dirname(__file__), "dist", "JarvisMK2", "jarvis.ico"),
        ]
        icon = None
        for c in candidates:
            if os.path.exists(c):
                icon = QIcon(c)
                break
        if icon is None or icon.isNull():
            from PySide6.QtWidgets import QStyle
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip("Jarvis MK2")
        menu = QMenu()
        act_show = menu.addAction("Mostrar Jarvis")
        act_show.triggered.connect(self._tray_show)
        menu.addSeparator()
        act_quit = menu.addAction("Salir")
        act_quit.triggered.connect(self._tray_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

    def _tray_show(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason):
        # Click izquierdo en el icono → restaurar
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self._tray_show()

    def _tray_quit(self):
        self._really_quit = True
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Cerrar la ventana solo la oculta. Para salir, usar el menú del tray."""
        if getattr(self, "_really_quit", False):
            event.accept()
            return
        event.ignore()
        self.hide()
        if self._jarvis is not None:
            try:
                self._jarvis.set_gui_visible(False)
            except Exception:
                pass
        if hasattr(self, "_tray"):
            self._tray.showMessage(
                "Jarvis MK2",
                "Jarvis sigue corriendo en segundo plano. Click derecho en el icono para salir.",
                QSystemTrayIcon.Information,
                3000,
            )

    def showEvent(self, event):
        super().showEvent(event)
        if self._jarvis is not None:
            try:
                self._jarvis.set_gui_visible(True)
            except Exception:
                pass

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._jarvis is not None:
            try:
                self._jarvis.set_gui_visible(False)
            except Exception:
                pass

    def iniciar(self):
        self._setup_tray()
        self.show()
        QApplication.instance().setQuitOnLastWindowClosed(False)
        QApplication.instance().exec()
