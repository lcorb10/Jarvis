"""Genera informe PDF profesional de Jarvis MK2 con ReportLab + Matplotlib."""
import io, os, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = Path("C:/Users/Sebastian/Desktop/jarvis_mk2/Jarvis_MK2_Informe_Tecnico.pdf")

# ── Colores ───────────────────────────────────────────────────────────────────
DARK      = colors.HexColor("#060810")
DARK2     = colors.HexColor("#0a0e1a")
PANEL     = colors.HexColor("#0d1220")
CYAN      = colors.HexColor("#00C8FF")
CYAN2     = colors.HexColor("#00a8d4")
BLUE      = colors.HexColor("#0055FF")
BLUE2     = colors.HexColor("#003399")
GREEN     = colors.HexColor("#00FF88")
GREEN2    = colors.HexColor("#00cc66")
YELLOW    = colors.HexColor("#FFD700")
RED       = colors.HexColor("#FF3355")
WHITE     = colors.HexColor("#FFFFFF")
GRAY      = colors.HexColor("#8ab4c8")
LIGHTBG   = colors.HexColor("#F0F6FF")
ACCENT    = colors.HexColor("#E8F4FD")

W, H = A4

# ══════════════════════════════════════════════════════════════════════════════
# Flowables personalizados
# ══════════════════════════════════════════════════════════════════════════════

class GlowLine(Flowable):
    def __init__(self, width=None, color=CYAN, thickness=2):
        super().__init__()
        self._width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness + 4

    def wrap(self, aw, ah):
        self._aw = aw
        return (self._width or aw, self.height)

    def draw(self):
        w = self._width or self._aw
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height/2, w, self.height/2)


class SectionHeader(Flowable):
    def __init__(self, number, title, subtitle=""):
        super().__init__()
        self.number = number
        self.title = title
        self.subtitle = subtitle
        self.height = 52

    def wrap(self, aw, ah):
        self._aw = aw
        return (aw, self.height)

    def draw(self):
        c = self.canv
        w = self._aw
        # Fondo degradado simulado
        c.setFillColor(DARK)
        c.rect(0, 0, w, self.height, fill=1, stroke=0)
        c.setFillColor(PANEL)
        c.rect(0, 0, w*0.6, self.height, fill=1, stroke=0)
        # Línea izquierda cyan
        c.setFillColor(CYAN)
        c.rect(0, 0, 5, self.height, fill=1, stroke=0)
        # Número de sección
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(14, self.height-30, self.number)
        # Título
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(14 + c.stringWidth(self.number, "Helvetica-Bold", 22) + 8, self.height-30, self.title)
        # Subtítulo
        if self.subtitle:
            c.setFillColor(CYAN)
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(16, 8, self.subtitle)
        # Línea inferior
        c.setStrokeColor(CYAN)
        c.setLineWidth(1)
        c.line(0, 0, w, 0)


class MetricCard(Flowable):
    def __init__(self, value, label, color=CYAN, width=3.5*cm, height=2.2*cm):
        super().__init__()
        self.value = value
        self.label = label
        self.color = color
        self._w = width
        self.height = height

    def wrap(self, aw, ah):
        return (self._w, self.height)

    def draw(self):
        c = self.canv
        w, h = self._w, self.height
        # Fondo
        c.setFillColor(DARK)
        c.roundRect(0, 0, w, h, 6, fill=1, stroke=0)
        # Borde
        c.setStrokeColor(self.color)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, w, h, 6, fill=0, stroke=1)
        # Barra superior de color
        c.setFillColor(self.color)
        c.roundRect(0, h-6, w, 6, 3, fill=1, stroke=0)
        # Valor
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 14)
        vw = c.stringWidth(self.value, "Helvetica-Bold", 14)
        c.drawString((w-vw)/2, h*0.42, self.value)
        # Label
        c.setFillColor(self.color)
        c.setFont("Helvetica", 7)
        lw = c.stringWidth(self.label, "Helvetica", 7)
        c.drawString((w-lw)/2, h*0.18, self.label)


# ══════════════════════════════════════════════════════════════════════════════
# Estilos de texto
# ══════════════════════════════════════════════════════════════════════════════
def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle("cover_title",
        fontName="Helvetica-Bold", fontSize=38, textColor=CYAN,
        alignment=TA_CENTER, spaceAfter=6, leading=44)

    styles["cover_sub"] = ParagraphStyle("cover_sub",
        fontName="Helvetica", fontSize=14, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=4)

    styles["cover_meta"] = ParagraphStyle("cover_meta",
        fontName="Helvetica", fontSize=10, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=3)

    styles["body"] = ParagraphStyle("body",
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#1a1a2e"),
        leading=15, spaceAfter=6, alignment=TA_JUSTIFY)

    styles["body_white"] = ParagraphStyle("body_white",
        fontName="Helvetica", fontSize=10, textColor=WHITE,
        leading=15, spaceAfter=6)

    styles["h2"] = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=13, textColor=BLUE,
        spaceBefore=14, spaceAfter=6)

    styles["h3"] = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=11, textColor=BLUE2,
        spaceBefore=10, spaceAfter=4)

    styles["bullet"] = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#1a1a2e"),
        leftIndent=16, leading=14, spaceAfter=3,
        bulletIndent=6, bulletFontName="Helvetica", bulletFontSize=10)

    styles["code"] = ParagraphStyle("code",
        fontName="Courier", fontSize=8, textColor=colors.HexColor("#1a1a2e"),
        backColor=colors.HexColor("#EEF4FF"), leading=12,
        leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=4,
        borderColor=BLUE, borderWidth=0.5, borderPadding=6)

    styles["tag"] = ParagraphStyle("tag",
        fontName="Helvetica-Bold", fontSize=8, textColor=WHITE,
        backColor=BLUE, leading=10, alignment=TA_CENTER)

    styles["caption"] = ParagraphStyle("caption",
        fontName="Helvetica-Oblique", fontSize=8, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=8)

    styles["table_header"] = ParagraphStyle("table_header",
        fontName="Helvetica-Bold", fontSize=9, textColor=WHITE)

    styles["table_cell"] = ParagraphStyle("table_cell",
        fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#1a1a2e"), leading=12)

    styles["table_cell_code"] = ParagraphStyle("table_cell_code",
        fontName="Courier", fontSize=8, textColor=BLUE2, leading=11)

    styles["highlight"] = ParagraphStyle("highlight",
        fontName="Helvetica-Bold", fontSize=11, textColor=DARK,
        backColor=CYAN, leading=14, leftIndent=10, rightIndent=10,
        spaceBefore=8, spaceAfter=8, borderPadding=8)

    return styles

# ══════════════════════════════════════════════════════════════════════════════
# Gráficas Matplotlib
# ══════════════════════════════════════════════════════════════════════════════
def make_arch_diagram():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor("#060810")
    ax.set_facecolor("#060810")

    layers = [
        ("CAPA DE ACCESO", "GUI PySide6  •  Telegram Bot  •  Doble Aplauso", "#00C8FF", 0.72),
        ("ORQUESTACIÓN", "jarvis_core.py  •  Bridge HTTP :18790", "#0055FF", 0.54),
        ("MOTOR IA", "Gemini 2.5 Flash (primario)  •  Ollama/Mistral (fallback)", "#003399", 0.36),
        ("HERRAMIENTAS", "Sistema  •  APIs  •  Archivos  •  Web  •  Visión (16 tools)", "#002266", 0.18),
        ("PERSISTENCIA", "Memoria JSON  •  Logs diarios  •  Config hot-reload", "#00FF88", 0.02),
    ]

    for label, desc, color, y in layers:
        rect = mpatches.FancyBboxPatch((0.03, y), 0.94, 0.14,
            boxstyle="round,pad=0.01", facecolor=color+"22",
            edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(0.06, y+0.09, label, color=color, fontsize=11,
                fontweight="bold", va="center", fontfamily="monospace")
        ax.text(0.06, y+0.04, desc, color="white", fontsize=8.5,
                va="center", alpha=0.85)
        # Flecha entre capas
        if y > 0.02:
            ax.annotate("", xy=(0.5, y), xytext=(0.5, y+0.14),
                arrowprops=dict(arrowstyle="-|>", color=color+"99", lw=1.5))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Arquitectura en Capas — Jarvis MK2", color="#00C8FF",
                 fontsize=14, fontweight="bold", pad=12)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#060810", edgecolor="none")
    plt.close()
    buf.seek(0)
    return buf


def make_bigo_chart():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("#060810")

    n = np.linspace(1, 50, 300)

    # Gráfica 1 — Complejidad temporal de componentes
    ax = axes[0]
    ax.set_facecolor("#0a0e1a")
    ax.set_title("Complejidad Temporal — Componentes Clave", color="#00C8FF",
                 fontsize=10, fontweight="bold", pad=8)

    funcs = [
        (np.ones_like(n),         "O(1) — Detector aplausos",   "#00FF88", 2.5),
        (np.log2(n),              "O(log n) — Búsqueda memoria", "#00C8FF", 2),
        (n,                       "O(n) — Búsqueda archivos",    "#FFD700", 2),
        (n * np.log2(np.clip(n,1,None)), "O(n log n) — Aprendizaje", "#FF9900", 1.5),
        (n**2 / 25,               "O(n²) — Análisis logs completo", "#FF3355", 1.5),
    ]
    for y, label, color, lw in funcs:
        ax.plot(n, np.clip(y, 0, 80), label=label, color=color, linewidth=lw)

    ax.set_xlabel("Tamaño de entrada (n)", color="#8ab4c8", fontsize=8)
    ax.set_ylabel("Operaciones", color="#8ab4c8", fontsize=8)
    ax.tick_params(colors="#8ab4c8", labelsize=7)
    ax.spines[:].set_color("#2A3A4A")
    ax.set_ylim(0, 80)
    ax.legend(fontsize=6.5, loc="upper left",
              facecolor="#0d1220", edgecolor="#2A3A4A", labelcolor="white")
    ax.grid(True, color="#1a2535", alpha=0.5)

    # Gráfica 2 — Latencia comparativa por motor
    ax2 = axes[1]
    ax2.set_facecolor("#0a0e1a")
    ax2.set_title("Latencia de Respuesta por Motor (ms)", color="#00C8FF",
                  fontsize=10, fontweight="bold", pad=8)

    motors = ["Gemini\n2.5 Flash", "Ollama\nMistral", "Intenciones\nlocales", "Control\nSistema", "TTS\nEdge", "TTS\nGemini"]
    latencies = [1200, 3500, 8, 15, 900, 1800]
    bar_colors = ["#00C8FF", "#8ab4c8", "#00FF88", "#00FF88", "#FFD700", "#FFD700"]

    bars = ax2.bar(motors, latencies, color=bar_colors, edgecolor="#2A3A4A",
                   linewidth=0.8, width=0.6)
    for bar, val in zip(bars, latencies):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 40,
                 f"{val}ms", ha="center", va="bottom", color="white",
                 fontsize=7, fontweight="bold")

    ax2.set_ylabel("Latencia (ms)", color="#8ab4c8", fontsize=8)
    ax2.tick_params(colors="#8ab4c8", labelsize=7)
    ax2.spines[:].set_color("#2A3A4A")
    ax2.grid(True, axis="y", color="#1a2535", alpha=0.5)

    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#060810", edgecolor="none")
    plt.close()
    buf.seek(0)
    return buf


def make_tools_chart():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fig.patch.set_facecolor("#060810")

    # Pie — distribución de tools
    ax = axes[0]
    ax.set_facecolor("#060810")
    labels = ["Control Sistema\n(open/close app)", "Búsqueda\n(web/youtube/google)", "Media\n(spotify)", "Archivos\n(CRUD)", "APIs\n(clima/noticias)", "Visión IA\n(pantalla)"]
    sizes  = [2, 3, 1, 4, 3, 1]
    explode = [0.03]*6
    palette = ["#00C8FF","#0055FF","#00FF88","#FFD700","#FF9900","#FF3355"]
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=palette,
        autopct="%1.0f%%", explode=explode, startangle=140,
        textprops={"color":"white","fontsize":7.5},
        wedgeprops={"edgecolor":"#060810","linewidth":1.5})
    for at in autotexts:
        at.set_fontsize(8); at.set_fontweight("bold")
    ax.set_title("Distribución de Herramientas (16 tools)", color="#00C8FF",
                 fontsize=10, fontweight="bold")

    # Horizontal bar — apps controladas
    ax2 = axes[1]
    ax2.set_facecolor("#0a0e1a")
    ax2.set_title("Categorías de Apps Controlables (35+)", color="#00C8FF",
                  fontsize=10, fontweight="bold", pad=8)
    cats = ["Juegos", "Productividad", "Multimedia", "Navegadores", "Comunicación", "Sistema"]
    vals = [10, 8, 6, 4, 4, 3]
    bar_colors2 = ["#FF3355","#00C8FF","#FFD700","#00FF88","#0055FF","#8ab4c8"]
    bars2 = ax2.barh(cats, vals, color=bar_colors2, edgecolor="#2A3A4A", height=0.55)
    for bar, v in zip(bars2, vals):
        ax2.text(v + 0.1, bar.get_y() + bar.get_height()/2,
                 str(v), va="center", color="white", fontsize=8, fontweight="bold")
    ax2.set_xlim(0, 13)
    ax2.tick_params(colors="#8ab4c8", labelsize=8)
    ax2.spines[:].set_color("#2A3A4A")
    ax2.grid(True, axis="x", color="#1a2535", alpha=0.5)

    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#060810", edgecolor="none")
    plt.close()
    buf.seek(0)
    return buf


def make_thread_timeline():
    fig, ax = plt.subplots(figsize=(11, 4))
    fig.patch.set_facecolor("#060810")
    ax.set_facecolor("#0a0e1a")
    ax.set_title("Modelo de Concurrencia — Threads Activos", color="#00C8FF",
                 fontsize=11, fontweight="bold", pad=10)

    threads = [
        ("detector-aplausos",  0,  24, "#00FF88",  "24/7 — monitoreo de audio"),
        ("tts-queue",          0,  24, "#FFD700",  "Worker de audio serializado"),
        ("bridge-server",      0,  24, "#0055FF",  "HTTP daemon :18790"),
        ("config-watcher",     0,  24, "#00C8FF",  "Hot-reload config.json"),
        ("aprendizaje-loop",   0,   1, "#FF9900",  "Análisis logs cada 24h"),
        ("vosk-preload",       0,   2, "#8ab4c8",  "Carga modelo al inicio"),
        ("jarvis-main",        3,  11, "#FF3355",  "Conversación activa (voz)"),
        ("task-executor",      5,   8, "#CC44FF",  "Agente multi-paso (async)"),
    ]

    colors_t = [t[3] for t in threads]
    labels_t = [t[0] for t in threads]

    for i, (name, start, end, color, desc) in enumerate(threads):
        ax.barh(i, end-start, left=start, height=0.55, color=color,
                alpha=0.85, edgecolor="#060810", linewidth=0.8)
        ax.text(end + 0.2, i, desc, va="center", color=color,
                fontsize=7, alpha=0.9)

    ax.set_yticks(range(len(threads)))
    ax.set_yticklabels(labels_t, fontsize=8, fontfamily="monospace", color="white")
    ax.set_xlabel("Tiempo de ejecución (horas desde inicio)", color="#8ab4c8", fontsize=8)
    ax.tick_params(colors="#8ab4c8", labelsize=7)
    ax.spines[:].set_color("#2A3A4A")
    ax.set_xlim(0, 28)
    ax.grid(True, axis="x", color="#1a2535", alpha=0.4)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#060810", edgecolor="none")
    plt.close()
    buf.seek(0)
    return buf


def make_memory_diagram():
    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#060810")
    ax.set_facecolor("#060810")
    ax.axis("off")
    ax.set_title("Gestión Adaptativa de Memoria RAM", color="#00C8FF",
                 fontsize=11, fontweight="bold")

    # Bloques de memoria
    blocks = [
        (0.05, 0.5, "Vosk STT\n~120 MB", "#00C8FF", "Lazy-load\nLibera: 35s idle"),
        (0.28, 0.5, "Ollama\nMistral ~4 GB", "#FFD700", "keep_alive=0\nLibera: 35s post-conv"),
        (0.51, 0.5, "Gemini API\n~0 MB local", "#00FF88", "Cloud inference\nSin RAM local"),
        (0.74, 0.5, "Pygame\nAudio Buffer", "#FF9900", "BytesIO en memoria\nSin archivos temp"),
    ]

    for x, y, text, color, policy in blocks:
        rect = mpatches.FancyBboxPatch((x, y-0.2), 0.2, 0.4,
            boxstyle="round,pad=0.02", facecolor=color+"33",
            edgecolor=color, linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x+0.1, y+0.06, text, ha="center", va="center",
                color="white", fontsize=8, fontweight="bold",
                transform=ax.transAxes, multialignment="center")
        ax.text(x+0.1, y-0.12, policy, ha="center", va="center",
                color=color, fontsize=6.5, transform=ax.transAxes,
                multialignment="center", alpha=0.9)

    # Flecha de tiempo
    ax.annotate("", xy=(0.95, 0.1), xytext=(0.05, 0.1),
        arrowprops=dict(arrowstyle="-|>", color="#8ab4c8", lw=1.5),
        transform=ax.transAxes)
    ax.text(0.5, 0.06, "Liberación diferida de recursos → menor consumo RAM en reposo",
            ha="center", color="#8ab4c8", fontsize=8,
            transform=ax.transAxes, style="italic")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#060810", edgecolor="none")
    plt.close()
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
# Portada
# ══════════════════════════════════════════════════════════════════════════════
def build_cover(canvas_obj, doc):
    c = canvas_obj
    # Fondo negro
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Círculos decorativos (HUD)
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    c.circle(W/2, H*0.62, 130, fill=0, stroke=1)
    c.setLineWidth(0.7)
    c.circle(W/2, H*0.62, 110, fill=0, stroke=1)
    c.setLineWidth(0.3)
    c.setStrokeColor(BLUE)
    c.circle(W/2, H*0.62, 155, fill=0, stroke=1)

    # Líneas radiales decorativas
    import math as _math
    c.setLineWidth(0.4)
    c.setStrokeColor(CYAN)
    for angle in range(0, 360, 45):
        rad = _math.radians(angle)
        x1 = W/2 + 110 * _math.cos(rad)
        y1 = H*0.62 + 110 * _math.sin(rad)
        x2 = W/2 + 130 * _math.cos(rad)
        y2 = H*0.62 + 130 * _math.sin(rad)
        c.line(x1, y1, x2, y2)

    # "J" central
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 72)
    jw = c.stringWidth("J", "Helvetica-Bold", 72)
    c.drawString(W/2 - jw/2, H*0.62 - 22, "J")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(CYAN)
    mw = c.stringWidth("MK2", "Helvetica-Bold", 20)
    c.drawString(W/2 - mw/2, H*0.62 - 46, "MK2")

    # Título principal
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 42)
    title = "JARVIS MK2"
    tw = c.stringWidth(title, "Helvetica-Bold", 42)
    c.drawString(W/2 - tw/2, H*0.38, title)

    # Línea decorativa
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    c.line(W*0.2, H*0.355, W*0.8, H*0.355)

    # Subtítulo
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 14)
    sub = "Asistente de Inteligencia Artificial Personal"
    sw = c.stringWidth(sub, "Helvetica", 14)
    c.drawString(W/2 - sw/2, H*0.32, sub)

    # Tipo de documento
    c.setFillColor(BLUE)
    c.roundRect(W*0.3, H*0.28, W*0.4, 0.028*H, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    doc_label = "INFORME TÉCNICO DE ARQUITECTURA Y FUNCIONAMIENTO"
    dw = c.stringWidth(doc_label, "Helvetica-Bold", 10)
    c.drawString(W/2 - dw/2, H*0.285, doc_label)

    # Metadatos
    meta = [
        ("Autor",    "Sebastian Corbris"),
        ("Versión",  "2.0 — Mayo 2026"),
        ("Motor IA", "Gemini 2.5 Flash + Ollama/Mistral"),
        ("Stack",    "Python 3.11  •  Windows 11  •  WSL2 Ubuntu"),
        ("Acceso",   "GUI + Telegram Remote"),
    ]
    y_meta = H * 0.22
    for key, val in meta:
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(W*0.28, y_meta, key + ":")
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 9)
        c.drawString(W*0.28 + 70, y_meta, val)
        y_meta -= 14

    # Footer
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 8)
    footer = "Confidencial  •  sebas.corbris@gmail.com  •  2026"
    fw = c.stringWidth(footer, "Helvetica-Oblique", 8)
    c.drawString(W/2 - fw/2, 30, footer)

    # Línea inferior
    c.setStrokeColor(BLUE)
    c.setLineWidth(3)
    c.line(0, 20, W, 20)
    c.setStrokeColor(CYAN)
    c.setLineWidth(1)
    c.line(0, 24, W, 24)


def build_header_footer(canvas_obj, doc):
    c = canvas_obj
    # Header
    c.setFillColor(DARK)
    c.rect(0, H-28, W, 28, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, H-28, 4, 28, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(14, H-18, "JARVIS MK2")
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(14+80, H-18, "Informe Técnico de Arquitectura y Funcionamiento")
    c.setFont("Helvetica", 8)
    pw = c.stringWidth("Confidencial", "Helvetica", 8)
    c.drawString(W-pw-20, H-18, "Confidencial")
    # Footer
    c.setFillColor(DARK)
    c.rect(0, 0, W, 22, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, 0, 4, 22, fill=1, stroke=0)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    c.drawString(14, 7, "sebas.corbris@gmail.com  •  2026")
    page_str = f"Página {doc.page}"
    psw = c.stringWidth(page_str, "Helvetica", 7)
    c.drawString(W - psw - 14, 7, page_str)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers de tabla
# ══════════════════════════════════════════════════════════════════════════════
def styled_table(data, col_widths, header=True):
    style = [
        ("BACKGROUND",  (0,0), (-1,0), DARK if header else LIGHTBG),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE if header else DARK),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHTBG, colors.white]),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,1), (-1,-1), 8.5),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#C0D0E0")),
        ("LINEBELOW",   (0,0), (-1,0), 1.5, CYAN),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ]
    return Table(data, colWidths=col_widths, style=TableStyle(style), repeatRows=1)


def info_box(text, color=BLUE, bg=None):
    bg = bg or colors.HexColor("#EEF6FF")
    data = [[Paragraph(text, ParagraphStyle("ib", fontName="Helvetica", fontSize=10,
                       textColor=colors.HexColor("#1a1a2e"), leading=14))]]
    t = Table(data, colWidths=[14.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("LINEAFTER",  (0,0), (0,-1), 4, color),
        ("LINEBEFORE", (0,0), (0,-1), 4, color),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING",(0,0), (-1,-1), 10),
    ]))
    return t


def bullet_item(text, s, color=BLUE):
    return Paragraph(f'<font color="#{color.hexval()[2:]}">▶</font>  {text}', s["bullet"])


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL DOCUMENTO
# ══════════════════════════════════════════════════════════════════════════════
def build_pdf():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2.8*cm, bottomMargin=2*cm,
        title="Jarvis MK2 — Informe Técnico",
        author="Sebastian Corbris",
    )

    s = make_styles()
    story = []

    # ── PORTADA ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, H*0.82))
    story.append(PageBreak())

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
    story.append(SectionHeader("01", "RESUMEN EJECUTIVO",
                               "Overview del sistema y métricas clave"))
    story.append(Spacer(1, 8))

    story.append(info_box(
        "<b>Jarvis MK2</b> es un asistente de inteligencia artificial personal de escritorio, "
        "desarrollado íntegramente en <b>Python 3.11</b>, que integra reconocimiento y síntesis de voz, "
        "modelos de lenguaje de gran escala (LLMs), control del sistema operativo, visión artificial "
        "y acceso remoto vía Telegram. El sistema opera en tiempo real sobre <b>Windows 11</b>, con "
        "activación por doble aplauso, control desde dispositivos móviles y arquitectura modular "
        "orientada a la extensibilidad."
    ))
    story.append(Spacer(1, 12))

    # Métricas en cards
    story.append(Paragraph("Métricas del Sistema", s["h2"]))
    metrics = [
        ("~5,000", "Líneas de código", CYAN),
        ("25+", "Módulos Python", BLUE),
        ("16", "Herramientas (tools)", GREEN),
        ("35+", "Apps controladas", YELLOW),
        ("6", "APIs integradas", colors.HexColor("#FF9900")),
        ("3", "Motores TTS", RED),
        ("~1.5s", "Latencia Gemini", CYAN),
        ("2", "Canales de acceso", GREEN),
    ]
    card_row = []
    for val, lbl, col in metrics:
        card_row.append(MetricCard(val, lbl, col, width=3.6*cm, height=2.0*cm))

    # Dividir en 2 filas de 4
    row1 = card_row[:4]
    row2 = card_row[4:]
    for row in [row1, row2]:
        t = Table([row], colWidths=[3.8*cm]*4)
        t.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),
                                ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                ("TOPPADDING",(0,0),(-1,-1),4),
                                ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        story.append(t)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))

    # ── ARQUITECTURA ──────────────────────────────────────────────────────────
    story.append(SectionHeader("02", "ARQUITECTURA DEL SISTEMA",
                               "Diseño en capas y componentes principales"))
    story.append(Spacer(1, 8))

    arch_buf = make_arch_diagram()
    img = Image(arch_buf, width=15*cm, height=8.3*cm)
    story.append(img)
    story.append(Paragraph("Figura 1 — Arquitectura en capas de Jarvis MK2", s["caption"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Componentes Principales", s["h2"]))
    comp_data = [
        ["Componente", "Archivo", "Responsabilidad"],
        ["Núcleo principal", "jarvis_core.py", "Orquestación completa, ciclo de voz, TTS, estado"],
        ["Motor IA", "modulos/ia_local.py", "Gemini 2.5 + Ollama, historial, tool dispatch"],
        ["Gestor Gemini", "modulos/gemini_manager.py", "Rate limit, estadísticas, singleton"],
        ["Síntesis de voz", "modulos/sintesis_voz.py", "Edge TTS, Gemini TTS, pyttsx3, cola async"],
        ["Reconoc. voz", "modulos/reconocimiento_voz.py", "Vosk offline, streaming STT parcial"],
        ["Wake word", "modulos/detector_aplausos.py", "Detección doble aplauso por energía de audio"],
        ["Bridge HTTP", "bridge_server.py", "Servidor HTTP :18790 — 6 endpoints"],
        ["GUI", "interfaz.py", "PySide6 Qt6, tema oscuro, system tray"],
        ["Agente (plan)", "modulos/agent/planner.py", "Planificación multi-paso con Gemini JSON"],
        ["Agente (exec)", "modulos/agent/executor.py", "Ejecución con reintentos y replanning"],
        ["Tool Registry", "modulos/tools/registry.py", "16 herramientas registradas"],
        ["Visión IA", "modulos/tools/screen_processor.py", "Captura pantalla + Gemini Vision"],
        ["Memoria", "modulos/memoria.py", "JSON persistente, preferencias, backups"],
        ["Aprendizaje", "modulos/aprendizaje.py", "Análisis de logs, detección de hábitos 24h"],
    ]
    story.append(styled_table(comp_data, [4.2*cm, 4.8*cm, 6.2*cm]))
    story.append(Spacer(1, 10))

    # ── MOTOR IA ───────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("03", "MOTOR DE INTELIGENCIA ARTIFICIAL",
                               "Dual-engine: Gemini 2.5 Flash + Ollama/Mistral"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Arquitectura Dual Primary/Fallback", s["h2"]))
    story.append(info_box(
        "El motor IA implementa un patrón <b>primary/fallback automático</b>: "
        "<b>Gemini 2.5 Flash</b> actúa como motor principal (latencia ~1.2s, sin RAM local, "
        "máx. 55 llamadas/min), con conmutación transparente a <b>Ollama/Mistral</b> "
        "(offline, ~3.5s) cuando Gemini falla, supera el rate limit o no hay internet.",
        color=CYAN, bg=colors.HexColor("#EEF8FF")
    ))
    story.append(Spacer(1, 10))

    bigo_buf = make_bigo_chart()
    img2 = Image(bigo_buf, width=15.5*cm, height=6.7*cm)
    story.append(img2)
    story.append(Paragraph(
        "Figura 2 — Izquierda: Complejidad temporal Big-O de los componentes clave. "
        "Derecha: Latencia de respuesta comparativa por motor (milisegundos).",
        s["caption"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Tabla de Complejidad Algorítmica", s["h2"]))
    bigo_data = [
        ["Componente", "Complejidad", "Descripción"],
        ["Detector de aplausos", "O(1)", "Cálculo RMS + comparación umbral por bloque"],
        ["Búsqueda en memoria", "O(log n)", "Dict Python con acceso hash + búsqueda lineal corta"],
        ["Búsqueda de archivos", "O(n)", "Recorrido de árbol de directorios"],
        ["Parser JSON IA", "O(k)", "k = longitud de respuesta, acotado a 800 tokens"],
        ["Aprendizaje (análisis)", "O(n log n)", "Ordenamiento de frecuencias de comandos"],
        ["Rate limiter Gemini", "O(1) amortizado", "Deque con ventana deslizante de 60s"],
        ["Tool dispatch", "O(1)", "Dict lookup en registry de tools"],
        ["TTS queue", "O(1)", "Queue.put_nowait() + worker serializado"],
    ]
    story.append(styled_table(bigo_data, [5*cm, 3.2*cm, 7*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Sistema de Prompting Dinámico", s["h2"]))
    for item in [
        "<b>Personalidad y tono:</b> Jarvis tipo Iron Man, español latinoamericano, trato de 'señor'",
        "<b>Hora actual:</b> Contexto temporal para respuestas situacionales",
        "<b>Preferencias del usuario:</b> Últimas 15 preferencias detectadas automáticamente",
        "<b>Contexto de sesión:</b> Última app usada, última acción ejecutada",
        "<b>Descripción de tools:</b> 16 herramientas con parámetros y ejemplos de uso",
        "<b>Reglas de formato:</b> JSON estricto {\"tools\":[...], \"respuesta\":\"...\"} con tolerancia a fallos en 3 niveles",
    ]:
        story.append(bullet_item(item, s))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Ejemplo de respuesta JSON del motor IA:", s["h3"]))
    story.append(Paragraph(
        '{"tools": ["open_app:discord", "volume:subir"],<br/>'
        '"respuesta": "Abriendo Discord y subiendo el volumen, señor."}',
        s["code"]
    ))

    # ── SISTEMA DE VOZ ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("04", "SISTEMA DE VOZ",
                               "STT offline + TTS multi-motor + Wake Word"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Reconocimiento de Voz — Vosk (Offline)", s["h2"]))
    stt_data = [
        ["Parámetro", "Valor", "Descripción"],
        ["Motor", "Vosk 0.3.45", "ASR offline en español, 100% privado"],
        ["Sample rate", "16,000 Hz", "Óptimo para voz humana"],
        ["Modelo", "vosk-model-es (~50 MB)", "Almacenado localmente"],
        ["Modo", "Streaming parcial", "Emite resultados mientras se habla"],
        ["Timeout por turno", "20 segundos", "Regresa a espera tras 4 timeouts"],
        ["Protección feedback", "jarvis_hablando flag", "Descarta audio durante TTS"],
        ["Gestión RAM", "Lazy-load + descarga 35s", "Libera memoria en reposo"],
    ]
    story.append(styled_table(stt_data, [3.5*cm, 4.5*cm, 7.2*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Síntesis de Voz — Multi-motor con Fallback", s["h2"]))
    tts_data = [
        ["Motor", "Tecnología", "Calidad", "Internet", "RAM local"],
        ["Gemini TTS", "Google Gemini 2.5 Flash Preview", "★★★★★", "Sí", "0 MB"],
        ["Edge TTS", "Microsoft Neural (Azure)", "★★★★☆", "Sí", "0 MB"],
        ["pyttsx3", "Windows SAPI / MSAPI", "★★★☆☆", "No", "~5 MB"],
    ]
    story.append(styled_table(tts_data, [3.2*cm, 5.5*cm, 2.5*cm, 2*cm, 2*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Wake Word — Detección de Doble Aplauso", s["h2"]))
    story.append(info_box(
        "El sistema de activación es <b>completamente local</b> — no depende de internet ni de "
        "modelos de red. Analiza energía RMS, pico máximo y cambio de energía entre frames "
        "de audio a 8 kHz en tiempo real. Al detectar 2 aplausos dentro de 1.8 segundos, "
        "activa Jarvis con un cooldown de 3 segundos para evitar re-activaciones.",
        color=GREEN, bg=colors.HexColor("#EEFFF5")
    ))
    story.append(Spacer(1, 6))
    wake_data = [
        ["Parámetro", "Valor"],
        ["Sample rate", "8,000 Hz"],
        ["Umbral energía (RMS)", "> 0.02"],
        ["Umbral pico", "> 0.10"],
        ["Cambio de energía", "> 0.05"],
        ["Ventana temporal", "1.8 segundos"],
        ["Cooldown post-activación", "3.0 segundos"],
    ]
    story.append(styled_table(wake_data, [8*cm, 7.2*cm]))

    # ── HERRAMIENTAS ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("05", "SISTEMA DE HERRAMIENTAS",
                               "16 tools registradas — control total del sistema"))
    story.append(Spacer(1, 8))

    tools_buf = make_tools_chart()
    img3 = Image(tools_buf, width=15.5*cm, height=6*cm)
    story.append(img3)
    story.append(Paragraph(
        "Figura 3 — Izquierda: Distribución de los 16 tools por categoría. "
        "Derecha: Categorías de aplicaciones controlables (35+ apps).",
        s["caption"]))
    story.append(Spacer(1, 8))

    tools_data = [
        ["Tool", "Categoría", "Descripción"],
        ["open_app", "Sistema", "Abre 35+ aplicaciones por nombre o alias"],
        ["close_app", "Sistema", "Cierra procesos activos por nombre"],
        ["youtube_search", "Media", "Abre YouTube con búsqueda en Chrome"],
        ["google_search", "Web", "Abre búsqueda de Google en Chrome"],
        ["spotify_play", "Media", "Lanza Spotify con artista/canción"],
        ["web_search", "Investigación", "Scraping web para respuestas enriquecidas"],
        ["screen_process", "Visión IA", "Captura pantalla + análisis Gemini Vision"],
        ["volume", "Sistema", "Sube / baja / mutea el volumen del sistema"],
        ["weather", "API", "Clima en tiempo real (OpenWeather)"],
        ["math", "Cálculo", "Evalúa expresiones matemáticas"],
        ["news", "API", "Últimas noticias por categoría (NewsAPI)"],
        ["translate", "API", "Traducción entre idiomas"],
        ["create_file", "Archivos", "Crea archivo con contenido en Desktop"],
        ["create_folder", "Archivos", "Crea carpeta en ubicación indicada"],
        ["read_file", "Archivos", "Lee y retorna contenido de un archivo"],
        ["list_files", "Archivos", "Lista archivos de una carpeta"],
    ]
    story.append(styled_table(tools_data, [4*cm, 3.5*cm, 7.7*cm]))

    # ── ACCESO REMOTO ──────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("06", "ACCESO REMOTO VÍA TELEGRAM",
                               "Control total desde cualquier lugar del mundo"))
    story.append(Spacer(1, 8))

    story.append(info_box(
        "Jarvis es controlable desde <b>cualquier dispositivo móvil</b> a través de Telegram. "
        "El bot opera en WSL2 (Ubuntu) y se comunica con Jarvis via HTTP bridge. "
        "Si Jarvis está activo, los comandos se procesan con TTS; si está cerrado, "
        "el bot tiene <b>fallback local completo</b> con Gemini directo.",
        color=CYAN, bg=colors.HexColor("#EEF8FF")
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Endpoints del Bridge HTTP", s["h2"]))
    bridge_data = [
        ["Endpoint", "Método", "Descripción"],
        ["GET  /health", "GET", "Estado del sistema, visibilidad GUI"],
        ["POST /command", "POST", "Ejecuta texto en Jarvis con TTS opcional"],
        ["POST /show", "POST", "Trae la ventana de Jarvis al frente"],
        ["GET  /file?path=...", "GET", "Descarga binaria de un archivo del PC"],
        ["GET  /find_file?q=...", "GET", "Busca archivos por nombre, retorna JSON"],
        ["POST /compress_and_send", "POST", "Comprime archivo ZIP y lo sirve para Telegram"],
    ]
    story.append(styled_table(bridge_data, [5.5*cm, 2.5*cm, 7.2*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Flujo de Envío de Archivos", s["h2"]))
    file_data = [
        ["Paso", "Acción", "Resultado"],
        ["1", "Usuario escribe: 'envíame apps.txt'", "Bot detecta comando de envío"],
        ["2", "Bot llama GET /find_file?q=apps.txt", "Jarvis busca en Desktop/Docs/Downloads"],
        ["3a — 1 resultado", "POST /compress_and_send con ruta", "Jarvis genera ZIP en temp"],
        ["3b — Múltiples", "Bot envía lista numerada", "Usuario responde con número"],
        ["3c — Muy grande", "ZIP > 50 MB", "Bot informa tamaño exacto, no envía"],
        ["4", "Bot descarga ZIP del bridge y envía", "Archivo ZIP en chat de Telegram"],
        ["5", "ZIP temporal eliminado", "Sin archivos residuales en disco"],
    ]
    story.append(styled_table(file_data, [2.5*cm, 6*cm, 6.7*cm]))

    # ── CONCURRENCIA ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("07", "CONCURRENCIA Y RENDIMIENTO",
                               "Modelo de threads + gestión de memoria RAM"))
    story.append(Spacer(1, 8))

    thread_buf = make_thread_timeline()
    img4 = Image(thread_buf, width=15.5*cm, height=5.8*cm)
    story.append(img4)
    story.append(Paragraph(
        "Figura 4 — Timeline de threads activos durante una sesión típica de uso.",
        s["caption"]))
    story.append(Spacer(1, 8))

    mem_buf = make_memory_diagram()
    img5 = Image(mem_buf, width=14*cm, height=5.5*cm)
    story.append(img5)
    story.append(Paragraph(
        "Figura 5 — Gestión adaptativa de memoria RAM: los recursos se liberan "
        "automáticamente tras períodos de inactividad.",
        s["caption"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Gestión de Memoria por Recurso", s["h2"]))
    mem_data = [
        ["Recurso", "Política", "Trigger de liberación"],
        ["Modelo Vosk STT (~120 MB)", "Lazy-load + descarga diferida", "35s sin actividad de voz"],
        ["Modelo Ollama/Mistral (~4 GB)", "keep_alive=0 via API", "35s post-conversación"],
        ["Gemini API (cloud)", "Sin RAM local", "N/A — inference en cloud"],
        ["Audio TTS (buffer)", "io.BytesIO en memoria", "Auto al reproducir, sin disco"],
        ["Config hot-reload", "watchdog + callback", "Cambio en config.json"],
    ]
    story.append(styled_table(mem_data, [5.5*cm, 5*cm, 4.7*cm]))

    # ── MEMORIA E INTELIGENCIA ─────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("08", "MEMORIA E INTELIGENCIA ADAPTATIVA",
                               "Aprendizaje continuo + preferencias persistentes"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Estructura de Memoria Persistente", s["h2"]))
    mem_struct = [
        ["Sección", "Tipo", "Contenido"],
        ["preferencias", "Lista JSON", "Gustos detectados automáticamente por frases clave"],
        ["comandos_personalizados", "Dict", "Triggers → acciones definidas por el usuario"],
        ["conversaciones", "Entero", "Contador histórico de interacciones"],
        ["contexto", "Dict", "Última app, última acción (sesión actual)"],
        ["memoria_larga", "Dict anidado", "Rutinas, hábitos, categorías con timestamp"],
    ]
    story.append(styled_table(mem_struct, [4.5*cm, 3*cm, 7.7*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Sistema de Aprendizaje Continuo (24h)", s["h2"]))
    for item in [
        "<b>Hora más activa:</b> Detecta patrón de uso horario → guarda en memoria_larga/rutina",
        "<b>Top 5 comandos:</b> Comandos más frecuentes de los logs → guarda en memoria_larga/habitos",
        "<b>API preferida:</b> Servicio más usado → actualiza prioridades en GestorAPIs",
        "<b>Errores repetidos:</b> Detecta fallos recurrentes para diagnóstico automático",
        "<b>Backups automáticos:</b> 5 versiones anteriores siempre disponibles en backups/",
    ]:
        story.append(bullet_item(item, s))

    story.append(Spacer(1, 8))
    story.append(info_box(
        "Ejemplo de macro personalizado por voz:<br/><br/>"
        "<font face='Courier' size=9><b>Usuario:</b> 'cuando diga modo trabajo abre vscode y chrome'</font><br/>"
        "<font face='Courier' size=9><b>Jarvis:</b> 'Entendido. Cuando diga modo trabajo lo ejecutaré.'</font><br/><br/>"
        "El trigger se almacena en memoria_jarvis.json y está disponible permanentemente.",
        color=GREEN, bg=colors.HexColor("#EEFFF5")
    ))

    # ── SEGURIDAD ──────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("09", "SEGURIDAD Y ROBUSTEZ",
                               "Manejo de errores, fallbacks y protección de datos"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Medidas de Seguridad", s["h2"]))
    sec_data = [
        ["Medida", "Implementación"],
        ["API Keys en .env", "Nunca en código fuente; en .gitignore"],
        ["Bridge HTTP sin autenticación", "Diseñado solo para red local/loopback"],
        ["Bot Telegram filtrado", "Solo responde al OWNER_ID configurado"],
        ["Confirmación de acciones críticas", "Apagado/formateo requieren 'sí' verbal"],
        ["file_controller seguro", "Operaciones validadas contra _SAFE_ROOTS"],
        ["Instancia única", "Segunda ejecución solo restaura la ventana"],
    ]
    story.append(styled_table(sec_data, [6*cm, 9.2*cm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Manejo de Errores en Cascada", s["h2"]))
    fallback_data = [
        ["Componente", "Primario", "Fallback 1", "Fallback 2"],
        ["Motor IA", "Gemini 2.5 Flash", "Ollama/Mistral", "Mensaje de error controlado"],
        ["Síntesis voz", "Gemini TTS", "Edge TTS Neural", "pyttsx3 offline"],
        ["Reconoc. voz", "Vosk (cargado)", "Recarga automática", "Error descriptivo al usuario"],
        ["Config", "config.json", "Valores por defecto", "Log de advertencia"],
        ["Memoria JSON", "Archivo principal", "Backup más reciente", "Memoria vacía nueva"],
    ]
    story.append(styled_table(fallback_data, [3.2*cm, 3.5*cm, 3.8*cm, 4.7*cm]))

    # ── APIS ──────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("10", "APIS E INTEGRACIONES",
                               "6 servicios externos + modo degradado automático"))
    story.append(Spacer(1, 8))

    api_data = [
        ["API", "Servicio", "Auth", "Uso en Jarvis"],
        ["Gemini 2.5 Flash", "Google AI Studio", "API Key", "Chat, TTS, Vision, Planning"],
        ["OpenWeatherMap", "OpenWeather", "API Key", "Clima en tiempo real"],
        ["NewsAPI", "newsapi.org", "API Key", "Noticias por categoría"],
        ["YouTube Data v3", "Google Cloud", "API Key", "Búsqueda y reproducción"],
        ["Spotify Web API", "Spotify", "SDK OAuth", "Reproducción de música"],
        ["LibreTranslate", "LibreTranslate", "Sin key", "Traducción multi-idioma"],
    ]
    story.append(styled_table(api_data, [3.8*cm, 3.2*cm, 2.5*cm, 5.7*cm]))
    story.append(Spacer(1, 8))
    story.append(info_box(
        "El sistema funciona en <b>modo degradado automático</b> si alguna API no está configurada: "
        "las APIs sin key se marcan como inactivas en GestorAPIs y son omitidas transparentemente, "
        "sin errores visibles para el usuario.",
        color=YELLOW, bg=colors.HexColor("#FFFBEE")
    ))

    # ── CASOS DE USO ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("11", "CASOS DE USO REPRESENTATIVOS",
                               "Demostraciones de capacidad del sistema"))
    story.append(Spacer(1, 8))

    uso_data = [
        ["Comando / Acción", "Tools activadas", "Resultado"],
        ["'abre discord y sube el volumen'", "open_app:discord\nvolume:subir", "Discord se abre; volumen al máximo"],
        ["'pon Bad Bunny en Spotify'", "spotify_play:bad bunny", "Spotify lanza búsqueda del artista"],
        ["'qué hay en mi pantalla'", "screen_process", "Captura + análisis Gemini + voz"],
        ["'investiga el clima y guarda resumen'", "Agente: weather\n+ create_file", "Plan 2 pasos; archivo en Desktop"],
        ["'descansa' (por voz)", "— (break del ciclo)", "Modo espera; detector reactiva"],
        ["'envíame apps.txt' (Telegram)", "/find_file\n+ /compress_and_send", "ZIP enviado por Telegram"],
        ["'modo trabajo' (macro)", "open_app:vscode\nopen_app:chrome", "Macro personalizada ejecutada"],
        ["'cuánto es 347 por 89'", "math", "30,883 — respuesta oral inmediata"],
        ["'qué hay en mi pantalla' (Telegram)", "screen_process via bridge", "Descripción textual en Telegram"],
        ["'traduce hello al español'", "translate", "'Hola' — respuesta oral"],
    ]
    story.append(styled_table(uso_data, [5*cm, 4.5*cm, 5.7*cm]))

    # ── CONCLUSIONES ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(SectionHeader("12", "CONCLUSIONES Y ROADMAP",
                               "Fortalezas del sistema y líneas de desarrollo"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Fortalezas del Sistema", s["h2"]))
    strengths = [
        "<b>Arquitectura modular:</b> Cada componente es independiente y reemplazable sin afectar el resto del sistema.",
        "<b>Resiliencia total:</b> Fallbacks en cascada garantizan respuesta incluso sin internet o con Gemini limitado.",
        "<b>Privacidad nativa:</b> STT (Vosk) y TTS de respaldo (pyttsx3) operan 100% offline sin enviar voz a la nube.",
        "<b>Extensibilidad trivial:</b> Agregar una nueva herramienta requiere solo 3 líneas de código en ToolRegistry.",
        "<b>Acceso ubicuo:</b> Control completo del PC desde cualquier lugar del mundo vía Telegram con fallback local.",
        "<b>Inteligencia adaptativa:</b> Aprende hábitos del usuario automáticamente cada 24 horas.",
        "<b>Zero-downtime config:</b> Hot-reload de configuración sin reiniciar el proceso.",
    ]
    for item in strengths:
        story.append(bullet_item(item, s))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Roadmap de Mejoras", s["h2"]))
    roadmap = [
        ["#", "Mejora", "Impacto", "Esfuerzo"],
        ["1", "Wake-on-LAN — despertar PC desde Telegram", "Alto", "Medio"],
        ["2", "Autenticación HMAC en bridge HTTP", "Alto (seguridad)", "Bajo"],
        ["3", "Historial persistente multi-sesión", "Medio", "Bajo"],
        ["4", "Plugin marketplace — tools dinámicas", "Alto", "Alto"],
        ["5", "Dashboard web de estadísticas en tiempo real", "Medio", "Medio"],
        ["6", "App nativa Android/iOS", "Alto", "Alto"],
        ["7", "Soporte multi-idioma simultáneo (EN+ES)", "Medio", "Medio"],
    ]
    story.append(styled_table(roadmap, [1*cm, 7.5*cm, 3*cm, 2.7*cm]))

    story.append(Spacer(1, 20))

    # Footer final
    story.append(GlowLine(color=CYAN, thickness=2))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Jarvis MK2</b> — Informe Técnico de Arquitectura y Funcionamiento v2.0 — Mayo 2026<br/>"
        "Desarrollado íntegramente por <b>Sebastian Corbris</b>  •  sebas.corbris@gmail.com<br/>"
        "<font color='#8ab4c8'>Este documento es confidencial y de uso exclusivo del destinatario.</font>",
        ParagraphStyle("footer_final", fontName="Helvetica", fontSize=9,
                       textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER,
                       leading=14)
    ))

    # ── BUILD ────────────────────────────────────────────────────────────────
    def first_page(c, doc):
        build_cover(c, doc)

    def later_pages(c, doc):
        build_header_footer(c, doc)

    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    print(f"PDF generado: {OUT}")


if __name__ == "__main__":
    build_pdf()
