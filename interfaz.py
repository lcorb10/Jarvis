# interfaz.py
import threading
import tkinter as tk
from tkinter import scrolledtext
import math
import time
import sys
import os

# Colores estilo Jarvis
BG_DARK    = "#0a0a0f"
BG_PANEL   = "#0d1117"
CYAN       = "#00d4ff"
CYAN_DIM   = "#004d5c"
BLUE       = "#0066ff"
WHITE      = "#e0f0ff"
GRAY       = "#334455"
RED        = "#ff3355"
GREEN      = "#00ff88"
YELLOW     = "#ffcc00"

class InterfazJarvis:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("900x650")
        self.root.resizable(False, False)

        self.estado_actual = "esperando"
        self.jarvis = None
        self._construir_ui()
        self._iniciar_animacion()

    def _construir_ui(self):
        # Título
        titulo = tk.Label(
            self.root,
            text="◈  J.A.R.V.I.S  ◈",
            font=("Courier New", 20, "bold"),
            fg=CYAN, bg=BG_DARK
        )
        titulo.pack(pady=(15, 5))

        subtitulo = tk.Label(
            self.root,
            text="Just A Rather Very Intelligent System",
            font=("Courier New", 9),
            fg=CYAN_DIM, bg=BG_DARK
        )
        subtitulo.pack(pady=(0, 10))

        # Frame principal
        main_frame = tk.Frame(self.root, bg=BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Panel izquierdo
        left = tk.Frame(main_frame, bg=BG_DARK, width=260)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left.pack_propagate(False)

        # Indicador de estado
        estado_frame = tk.Frame(left, bg=BG_PANEL, bd=1, relief=tk.FLAT,
                                highlightbackground=CYAN_DIM, highlightthickness=1)
        estado_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(estado_frame, text="ESTADO DEL SISTEMA",
                 font=("Courier New", 8, "bold"),
                 fg=CYAN_DIM, bg=BG_PANEL).pack(pady=(8, 4))

        self.estado_label = tk.Label(
            estado_frame,
            text="● ESPERANDO",
            font=("Courier New", 12, "bold"),
            fg=YELLOW, bg=BG_PANEL
        )
        self.estado_label.pack(pady=(0, 8))

        # Canvas animación
        self.canvas = tk.Canvas(left, width=240, height=240,
                                bg=BG_DARK, highlightthickness=0)
        self.canvas.pack(pady=10)

        # Botón activar
        self.btn_activar = tk.Button(
            left,
            text="⚡  ACTIVAR JARVIS",
            font=("Courier New", 11, "bold"),
            fg=BG_DARK, bg=CYAN,
            activebackground=BLUE,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._activar_manual,
            pady=10
        )
        self.btn_activar.pack(fill=tk.X, pady=(10, 5))

        # Botón modo silencioso
        self.silencioso_var = tk.BooleanVar(value=False)
        self.btn_silencioso = tk.Button(
            left,
            text="🔊  VOZ ACTIVA",
            font=("Courier New", 9),
            fg=GREEN, bg=BG_PANEL,
            activebackground=GRAY,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._toggle_silencioso,
            pady=6,
            highlightbackground=GREEN,
            highlightthickness=1
        )
        self.btn_silencioso.pack(fill=tk.X, pady=5)

        # Panel derecho — chat
        right = tk.Frame(main_frame, bg=BG_DARK)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(right, text="CONSOLA DE INTERACCIÓN",
                 font=("Courier New", 8, "bold"),
                 fg=CYAN_DIM, bg=BG_DARK).pack(anchor=tk.W, pady=(0, 5))

        # Chat scrollable
        self.chat = scrolledtext.ScrolledText(
            right,
            bg=BG_PANEL, fg=WHITE,
            font=("Courier New", 10),
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD,
            padx=10, pady=10
        )
        self.chat.pack(fill=tk.BOTH, expand=True)

        # Tags de color para el chat
        self.chat.tag_config("usuario", foreground=CYAN)
        self.chat.tag_config("jarvis", foreground=GREEN)
        self.chat.tag_config("sistema", foreground=YELLOW)
        self.chat.tag_config("error", foreground=RED)

        # Barra inferior
        bottom = tk.Frame(self.root, bg=BG_DARK)
        bottom.pack(fill=tk.X, padx=20, pady=10)

        self.label_version = tk.Label(
            bottom,
            text="JARVIS v1.0  |  Ollama + Vosk + Python",
            font=("Courier New", 8),
            fg=CYAN_DIM, bg=BG_DARK
        )
        self.label_version.pack(side=tk.LEFT)

        self.label_hora = tk.Label(
            bottom, text="",
            font=("Courier New", 8),
            fg=CYAN_DIM, bg=BG_DARK
        )
        self.label_hora.pack(side=tk.RIGHT)
        self._actualizar_hora()

    def _actualizar_hora(self):
        import datetime
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.label_hora.config(text=hora)
        self.root.after(1000, self._actualizar_hora)

    def _iniciar_animacion(self):
        self.angulo = 0
        self.pulso = 0
        self._animar()

    def _animar(self):
        self.canvas.delete("all")
        cx, cy, r = 120, 120, 90

        # Círculos de fondo
        for i in range(3):
            radio = r - i * 20
            color = CYAN_DIM if i > 0 else CYAN
            self.canvas.create_oval(
                cx - radio, cy - radio,
                cx + radio, cy + radio,
                outline=color, width=1
            )

        # Arco giratorio
        estado = self.estado_actual
        color_arco = {
            "esperando": YELLOW,
            "escuchando": GREEN,
            "hablando": CYAN,
            "procesando": BLUE
        }.get(estado, CYAN)

        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=self.angulo, extent=120,
            style=tk.ARC, outline=color_arco, width=3
        )
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=self.angulo + 180, extent=60,
            style=tk.ARC, outline=color_arco, width=2
        )

        # Puntos giratorios
        for i in range(6):
            ang_rad = math.radians(self.angulo + i * 60)
            px = cx + r * math.cos(ang_rad)
            py = cy + r * math.sin(ang_rad)
            tam = 4 if i == 0 else 2
            self.canvas.create_oval(
                px - tam, py - tam,
                px + tam, py + tam,
                fill=color_arco, outline=""
            )

        # Texto central
        texto_estado = {
            "esperando": "STAND BY",
            "escuchando": "LISTENING",
            "hablando": "SPEAKING",
            "procesando": "PROCESSING"
        }.get(estado, "ONLINE")

        self.canvas.create_text(
            cx, cy - 10,
            text="◈",
            font=("Courier New", 20, "bold"),
            fill=color_arco
        )
        self.canvas.create_text(
            cx, cy + 18,
            text=texto_estado,
            font=("Courier New", 7, "bold"),
            fill=color_arco
        )

        self.angulo = (self.angulo + 3) % 360
        self.root.after(50, self._animar)

    def _activar_manual(self):
        if self.jarvis and not self.jarvis.en_conversacion:
            hilo = threading.Thread(target=self.jarvis.activar, daemon=True)
            hilo.start()

    def _toggle_silencioso(self):
        if self.jarvis:
            if self.silencioso_var.get():
                self.jarvis.tts.desactivar_silencioso()
                self.silencioso_var.set(False)
                self.btn_silencioso.config(text="🔊  VOZ ACTIVA", fg=GREEN,
                                           highlightbackground=GREEN)
            else:
                self.jarvis.tts.activar_silencioso()
                self.silencioso_var.set(True)
                self.btn_silencioso.config(text="🔇  MODO SILENCIOSO", fg=GRAY,
                                           highlightbackground=GRAY)

    # Callbacks para que Jarvis actualice la GUI
    def on_user_speech(self, texto):
        self.root.after(0, self._agregar_chat, f"TÚ: {texto}", "usuario")
        self.root.after(0, self._cambiar_estado, "procesando")

    def on_jarvis_response(self, texto):
        self.root.after(0, self._agregar_chat, f"JARVIS: {texto}", "jarvis")

    def on_state_change(self, estado):
        self.root.after(0, self._cambiar_estado, estado)

    def on_sistema(self, texto):
        self.root.after(0, self._agregar_chat, f"[SYS] {texto}", "sistema")

    def _agregar_chat(self, texto, tag=""):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, texto + "\n", tag)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def _cambiar_estado(self, estado):
        self.estado_actual = estado
        configs = {
            "esperando":   ("● ESPERANDO",   YELLOW),
            "escuchando":  ("● ESCUCHANDO",  GREEN),
            "hablando":    ("● HABLANDO",    CYAN),
            "procesando":  ("● PROCESANDO",  BLUE),
        }
        texto, color = configs.get(estado, ("● ONLINE", WHITE))
        self.estado_label.config(text=texto, fg=color)

    def conectar_jarvis(self, jarvis_instance):
        self.jarvis = jarvis_instance

    def iniciar(self):
        self.root.mainloop()