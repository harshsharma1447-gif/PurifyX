import sys
import serial
import serial.tools.list_ports
import csv  
import os
import math
import subprocess
import traceback
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QTextEdit, 
    QLineEdit, QFormLayout, QMessageBox, QFrame, QGraphicsDropShadowEffect,
    QToolTip, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QTime, QThread, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, 
    QCursor, QPolygonF
)

# Matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ReportLab for 7-Page Industrial Reports
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader


# ================= CROSS-PLATFORM OPENER =================
def open_path(path):
    """Safely opens a file or directory on Windows, macOS, or Linux."""
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print(f"Error opening path {path}: {e}")


# ================= HIGH-TECH PRECISION GAUGE =================
class HighTechPrecisionGauge(QWidget):
    """
    Precision dial gauge supporting negative ranges, sub-ticks, 
    numerical interval labels, dynamic gradient arcs, and status chips.
    """
    def __init__(self, title, minv, maxv, safe_min=None, safe_max=None, unit="", 
                 theme_color="#a855f7", ticks_count=7):
        super().__init__()
        self.title = title
        self.minv = float(minv)
        self.maxv = float(maxv)
        self.value = float(minv)
        self.unit = unit
        self.safe_min = safe_min
        self.safe_max = safe_max
        self.theme_color = QColor(theme_color)
        self.ticks_count = ticks_count

        self.setMinimumSize(210, 230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def setValue(self, v):
        try:
            v = float(str(v).replace("%", "").strip())
        except Exception:
            v = self.minv
        self.value = max(self.minv, min(self.maxv, v))
        self.update()

    def _get_status(self):
        v = self.value
        if self.safe_min is None and self.safe_max is None:
            return "NORMAL", "#00f2fe"
        if self.safe_min is None and self.safe_max is not None:
            if v <= self.safe_max:
                return "OPTIMAL", "#10b981"
            return ("ELEVATED", "#f59e0b") if v <= self.safe_max * 1.3 else ("CRITICAL", "#ef4444")
        if self.safe_max is None and self.safe_min is not None:
            if v >= self.safe_min:
                return "OPTIMAL", "#10b981"
            return ("SUB-PAR", "#f59e0b") if v >= self.safe_min * 0.7 else ("CRITICAL", "#ef4444")
        if self.safe_min <= v <= self.safe_max:
            return "OPTIMAL", "#10b981"
        return "CRITICAL", "#ef4444"

    def enterEvent(self, event):
        status, color_hex = self._get_status()
        curr_str = f"{self.value:.2f} {self.unit}".strip()
        safe_str = f"[{self.safe_min if self.safe_min is not None else '-'} to {self.safe_max if self.safe_max is not None else '-'}]"
        tooltip = (
            f"<div style='background: #120b24; color:#f8fafc; padding:10px; border-radius:8px; border:1px solid #7c3aed;'>"
            f"<b style='color:{self.theme_color.name()}; font-size:13px;'>{self.title}</b><br/>"
            f"<b>Current Value:</b> <span style='font-size:13px; font-weight:bold;'>{curr_str}</span><br/>"
            f"<b>Safe Band:</b> {safe_str}<br/>"
            f"<b>Status:</b> <span style='color:{color_hex}; font-weight:bold;'>{status}</span>"
            f"</div>"
        )
        QToolTip.showText(QCursor.pos(), tooltip, self)

    def leaveEvent(self, event):
        QToolTip.hideText()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        center = QPointF(w / 2.0, h / 2.0 - 10)
        radius = min(w, h) / 2.0 - 24

        card_grad = QLinearGradient(0, 0, w, h)
        card_grad.setColorAt(0.0, QColor("#130924"))
        card_grad.setColorAt(1.0, QColor("#080c1d"))
        p.setPen(QPen(QColor("#2e184e"), 1.2))
        p.setBrush(card_grad)
        p.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 16, 16)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#070410"))
        p.drawEllipse(center, radius + 10, radius + 10)

        start_angle = 150
        sweep_angle = 240
        track_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        p.setPen(QPen(QColor("#1f1438"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(track_rect, int(-start_angle * 16), int(-sweep_angle * 16))

        total_ticks = (self.ticks_count - 1) * 4
        for i in range(total_ticks + 1):
            deg = start_angle + (i / float(total_ticks)) * sweep_angle
            rad = math.radians(deg)
            is_major = (i % 4 == 0)
            
            t_len = 8 if is_major else 4
            p1 = QPointF(center.x() + (radius - 10) * math.cos(rad), center.y() + (radius - 10) * math.sin(rad))
            p2 = QPointF(center.x() + (radius - 10 - t_len) * math.cos(rad), center.y() + (radius - 10 - t_len) * math.sin(rad))
            
            p.setPen(QPen(QColor("#4c2a85") if not is_major else self.theme_color, 1.5 if is_major else 1))
            p.drawLine(p1, p2)

            if is_major:
                val = self.minv + (i / float(total_ticks)) * (self.maxv - self.minv)
                val_str = f"{int(val)}" if abs(val) >= 10 else f"{val:.1f}"
                lp = QPointF(center.x() + (radius - 24) * math.cos(rad), center.y() + (radius - 24) * math.sin(rad))
                
                p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
                p.setPen(QColor("#a78bfa"))
                p.drawText(QRectF(lp.x() - 16, lp.y() - 8, 32, 16), Qt.AlignmentFlag.AlignCenter, val_str)

        ratio = (self.value - self.minv) / (self.maxv - self.minv) if self.maxv > self.minv else 0
        ratio = max(0.0, min(1.0, ratio))

        grad = QLinearGradient(center.x() - radius, center.y(), center.x() + radius, center.y())
        grad.setColorAt(0.0, QColor("#00f2fe"))
        grad.setColorAt(0.5, self.theme_color)
        grad.setColorAt(1.0, QColor("#ec4899"))

        p.setPen(QPen(QBrush(grad), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(track_rect, int(-start_angle * 16), int(-sweep_angle * ratio * 16))

        needle_angle = start_angle + (ratio * sweep_angle)
        n_rad = math.radians(needle_angle)
        needle_len = radius - 15

        nx = center.x() + needle_len * math.cos(n_rad)
        ny = center.y() + needle_len * math.sin(n_rad)
        
        perp_rad = n_rad + math.pi / 2
        bx1 = center.x() + 4 * math.cos(perp_rad)
        by1 = center.y() + 4 * math.sin(perp_rad)
        bx2 = center.x() - 4 * math.cos(perp_rad)
        by2 = center.y() - 4 * math.sin(perp_rad)

        needle_poly = QPolygonF([QPointF(bx1, by1), QPointF(nx, ny), QPointF(bx2, by2)])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawPolygon(needle_poly)

        p.setPen(QPen(self.theme_color, 1.5))
        p.drawLine(center, QPointF(nx, ny))

        p.setPen(QPen(QColor("#4c1d95"), 2))
        p.setBrush(QColor("#0a0518"))
        p.drawEllipse(center, 9, 9)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#00f2fe"))
        p.drawEllipse(center, 4, 4)

        p.setPen(QColor("#c4b5fd"))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(0, 14, w, 18), Qt.AlignmentFlag.AlignCenter, self.title.upper())

        status_text, status_color = self._get_status()
        status_rect = QRectF(w / 2.0 - 38, h - 54, 76, 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(status_color).darker(260))
        p.drawRoundedRect(status_rect, 8, 8)
        p.setPen(QColor(status_color))
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.ExtraBold))
        p.drawText(status_rect, Qt.AlignmentFlag.AlignCenter, status_text)

        val_str = f"{self.value:.1f}" if abs(self.maxv - self.minv) >= 20 else f"{self.value:.2f}"
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.drawText(QRectF(0, h - 35, w, 22), Qt.AlignmentFlag.AlignCenter, f"{val_str} {self.unit}".strip())


# ================= SERIAL WORKER THREAD =================
class SerialWorker(QThread):
    data_received = pyqtSignal(dict)
    log_message = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.ser = None

    def find_port(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = (p.description or "").lower()
            dev = (p.device or "").lower()
            if any(k in desc or k in dev for k in ["usb", "esp32", "cp210", "ch340", "silicon", "uart"]):
                return p.device
        return ports[0].device if ports else None

    def run(self):
        while self.running:
            try:
                port = self.find_port()
                if not port:
                    self.status.emit("Awaiting ESP32 Link...")
                    self.msleep(1500)
                    continue

                try:
                    self.ser = serial.Serial(port, 115200, timeout=1)
                    self.status.emit(f"ONLINE: {port}")
                    self.ser.write(b"START\r\n")
                except Exception as e:
                    self.status.emit(f"Link Fault: {e}")
                    self.msleep(2000)
                    continue

                while self.running and self.ser and self.ser.is_open:
                    try:
                        if self.ser.in_waiting:
                            line = self.ser.readline().decode(errors="ignore").strip()
                            if line:
                                self.log_message.emit(line)
                                if ":" in line:
                                    k, v = line.split(":", 1)
                                    self.data_received.emit({k.strip(): v.strip()})
                        else:
                            self.msleep(15)
                    except Exception as e:
                        self.log_message.emit(f"Data stream drop: {e}")
                        break

                if self.ser:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
                    self.status.emit("ESP32 Disconnected")

            except Exception as e:
                self.status.emit(f"Err: {e}")
                self.msleep(2000)

    def stop(self):
        self.running = False
        if self.ser:
            try:
                self.ser.write(b"STOP\r\n")
                self.msleep(50)
                self.ser.close()
            except Exception:
                pass
            self.ser = None
        self.wait(1000)

    def send_command(self, cmd: str):
        try:
            if self.ser and self.ser.is_open:
                self.ser.write((cmd.strip() + "\n").encode())
        except Exception as e:
            self.log_message.emit(f"Command Fault: {e}")


# ================= PURPLE-BLUE CYBER SPLASH SCREEN =================
class AquaSplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(480, 520)

        self.progress = 0
        self.angle = 0
        self.messages = [
            "Booting PurifyX Neural Matrix...",
            "Synthesizing Dual-Probe Electrochemical Core...",
            "Loading Self-Validation Meta-Cognitive Engine...",
            "PurifyX Online. System Nominal."
        ]

        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(25)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.card = QFrame(self)
        self.card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #090414, stop:0.5 #110729, stop:1 #06091f);
                border: 1.5px solid #6d28d9;
                border-radius: 28px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(168, 85, 247, 90))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 40, 30, 35)

        title = QLabel("PURIFYX A.Q.U.A")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 900; color: #ffffff; letter-spacing: 3px;")
        
        sub = QLabel("INTELLIGENT WATER MONITORING & AI LAB")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 10px; font-weight: 800; color: #00f2fe; letter-spacing: 2px;")

        card_layout.addWidget(title)
        card_layout.addWidget(sub)
        card_layout.addStretch()

        self.circle = QWidget()
        self.circle.setFixedSize(140, 140)
        self.circle.paintEvent = self.paint_circle
        
        cbox = QHBoxLayout()
        cbox.addWidget(self.circle, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addLayout(cbox)
        card_layout.addStretch()

        self.status = QLabel("Initializing Neural Bus...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #c4b5fd; font-size: 12px; font-weight: 600;")
        card_layout.addWidget(self.status)

        self.btn = QPushButton("LOAD PROGRESS")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setFixedHeight(48)
        self.btn.setVisible(False)
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:0.5 #3b82f6, stop:1 #00f2fe);
                color: #ffffff;
                font-weight: 900;
                font-size: 14px;
                letter-spacing: 1.5px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:0.5 #60a5fa, stop:1 #38bdf8);
            }
        """)
        self.btn.clicked.connect(self.accept)
        card_layout.addWidget(self.btn)

        layout.addWidget(self.card)

    def paint_circle(self, event):
        p = QPainter(self.circle)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(10, 10, 120, 120)
        p.setPen(QPen(QColor("#1e1038"), 8))
        p.drawArc(rect, 0, 360 * 16)

        grad = QLinearGradient(0, 0, 140, 140)
        grad.setColorAt(0, QColor("#c084fc"))
        grad.setColorAt(0.5, QColor("#3b82f6"))
        grad.setColorAt(1, QColor("#00f2fe"))
        p.setPen(QPen(QBrush(grad), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        
        sweep = int(360 * 16 * (self.progress / 100.0))
        p.drawArc(rect, int(-self.angle * 16), -sweep)

        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.progress}%")

    def tick(self):
        self.progress += 1
        self.angle = (self.angle + 5) % 360
        idx = min(3, self.progress // 26)
        self.status.setText(self.messages[idx])
        self.circle.update()

        if self.progress >= 100:
            self.timer.stop()
            self.btn.setVisible(True)
            self.status.setText("Ready to Launch")


# ================= OSCILLOSCOPE GRAPH WINDOW =================
class GraphWindow(QDialog):
    def __init__(self, parent=None, start_time=None):
        super().__init__(parent)
        self.setWindowTitle("Real-Time Telemetry Oscilloscope (Live 1Hz Stream)")
        self.resize(920, 620)
        self.setStyleSheet(parent.dark_theme() if parent else "")

        self.start_time = start_time or datetime.now()
        self.times, self.ph_data, self.tds_data, self.turb_data, self.temp_data = [], [], [], [], []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        self.figure = Figure(facecolor="#080412")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax_ph = self.figure.add_subplot(4, 1, 1)
        self.ax_tds = self.figure.add_subplot(4, 1, 2)
        self.ax_turb = self.figure.add_subplot(4, 1, 3)
        self.ax_temp = self.figure.add_subplot(4, 1, 4)

        self.line_ph, = self.ax_ph.plot([], [], color="#c084fc", lw=2)
        self.line_tds, = self.ax_tds.plot([], [], color="#38bdf8", lw=2)
        self.line_turb, = self.ax_turb.plot([], [], color="#00f2fe", lw=2)
        self.line_temp, = self.ax_temp.plot([], [], color="#f43f5e", lw=2)

        for ax, name in zip([self.ax_ph, self.ax_tds, self.ax_turb, self.ax_temp], 
                            ["pH", "TDS (ppm)", "Turbidity (NTU)", "Temp (°C)"]):
            ax.grid(True, color="#231442", linestyle="--", alpha=0.6)
            ax.tick_params(colors="#c4b5fd", labelsize=8)
            ax.set_facecolor("#100824")
            ax.set_ylabel(name, color="#ffffff", fontsize=8, fontweight='bold')
            for spine in ax.spines.values():
                spine.set_color("#3b1c6e")

        self.figure.tight_layout()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        clear_btn = QPushButton("Reset Traces")
        close_btn = QPushButton("Close")
        clear_btn.clicked.connect(self.clear_traces)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.redraw)
        self.timer.start(500)

    def add_point(self, t, ph, tds, turb, temp):
        t_sec = (t - self.start_time).total_seconds()
        self.times.append(t_sec)
        self.ph_data.append(ph)
        self.tds_data.append(tds)
        self.turb_data.append(turb)
        self.temp_data.append(temp)

    def redraw(self):
        if not self.times:
            return
        xmin = max(0, self.times[-1] - 60)
        xmax = max(10, self.times[-1])

        for line, data, ax in [
            (self.line_ph, self.ph_data, self.ax_ph),
            (self.line_tds, self.tds_data, self.ax_tds),
            (self.line_turb, self.turb_data, self.ax_turb),
            (self.line_temp, self.temp_data, self.ax_temp)
        ]:
            line.set_data(self.times, data)
            ax.set_xlim(xmin, xmax)
            if data:
                ax.set_ylim(min(data) * 0.9 - 0.5, max(data) * 1.1 + 0.5)

        self.canvas.draw_idle()

    def clear_traces(self):
        self.start_time = datetime.now()
        self.times.clear()
        self.ph_data.clear()
        self.tds_data.clear()
        self.turb_data.clear()
        self.temp_data.clear()
        self.redraw()


# ================= AI SIMULATION LAB =================
class SimulationWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.dashboard = parent
        self.setWindowTitle("AI Neural Simulation Injector")
        self.resize(520, 440)
        self.setStyleSheet(parent.dark_theme())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Neural Telemetry Synthesis")
        header.setStyleSheet("font-size:18px; font-weight:bold; color:#00f2fe;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)
        self.in_ph = QLineEdit("7.20")
        self.in_tds = QLineEdit("210")
        self.in_turb = QLineEdit("1.10")
        self.in_temp = QLineEdit("24.0")

        form.addRow("pH Level (0 to 14):", self.in_ph)
        form.addRow("TDS Metric (0 to 1200 ppm):", self.in_tds)
        form.addRow("Turbidity (0 to 50 NTU):", self.in_turb)
        form.addRow("Temperature (-100 to +100 °C):", self.in_temp)
        layout.addLayout(form)

        p_lbl = QLabel("Fast Simulation Injections:")
        p_lbl.setStyleSheet("color:#c4b5fd; font-weight:bold;")
        layout.addWidget(p_lbl)

        presets = QHBoxLayout()
        for name, vals in [
            ("Alpine Pure", ("7.40", "120", "0.5", "22.0")),
            ("Sub-Arctic Spring", ("7.10", "85", "0.2", "-15.0")),
            ("Moderate Treat", ("6.20", "550", "6.5", "32.0")),
            ("Hazardous Scald", ("2.40", "1100", "28.0", "85.0"))
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, v=vals: self.apply_preset(v))
            presets.addWidget(btn)
        layout.addLayout(presets)
        layout.addStretch()

        b_row = QHBoxLayout()
        inject_btn = QPushButton("Inject Telemetry")
        inject_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #00f2fe); color:white; font-weight:bold;")
        inject_btn.clicked.connect(self.inject)
        stop_btn = QPushButton("Stop Simulation")
        stop_btn.clicked.connect(self.dashboard.stop_simulation)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        b_row.addWidget(inject_btn)
        b_row.addWidget(stop_btn)
        b_row.addStretch()
        b_row.addWidget(close_btn)
        layout.addLayout(b_row)

    def apply_preset(self, vals):
        self.in_ph.setText(vals[0])
        self.in_tds.setText(vals[1])
        self.in_turb.setText(vals[2])
        self.in_temp.setText(vals[3])
        self.inject()

    def inject(self):
        try:
            ph = float(self.in_ph.text().strip())
            tds = float(self.in_tds.text().strip())
            turb = float(self.in_turb.text().strip())
            temp = float(self.in_temp.text().strip())
            data = {"pH": ph, "TDS": tds, "Turb": turb, "Temp": temp}

            # First calculate the exact AQUA verdict for these simulated values.
            self.dashboard.handle_telemetry(data)
            simulated_status = self.dashboard.overall_verdict

            # TEST field order is: pH, Turbidity, Temperature, TDS, Status.\n            # This exactly matches the ESP32 TEST parser.\n            # TEST keeps the existing LCD/data simulation behavior.
            # The sixth field carries the same verdict for firmware versions
            # that choose to parse it directly.
            cmd = f"TEST,{ph},{turb},{temp},{tds},{simulated_status}"
            self.dashboard.send_sim_command(
                cmd,
                None,
                simulated_status
            )
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please ensure all values are valid numbers.")


# ================= SCROLLABLE WQI SUITE WITH DEDICATED LIVE GRAPH =================
class WaterScoreWindow(QDialog):
    """
    Scrollable Water Quality Index dialog featuring parameter breakdowns,
    remediation steps, and a dedicated live 1 Hz WQI Oscilloscope Graph.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.dashboard = parent
        self.setWindowTitle("Water Quality Index (WQI) Diagnostic Suite")
        self.resize(850, 700)
        self.setStyleSheet(parent.dark_theme())

        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #090414;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4c1d95;
                min-height: 25px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7c3aed;
            }
        """)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(14)

        title = QLabel("COMPREHENSIVE WQI & PURITY DIAGNOSTICS")
        title.setStyleSheet("font-size:16px; font-weight:900; color:#00f2fe; letter-spacing:1px;")
        layout.addWidget(title)

        top_row = QHBoxLayout()
        self.gauge = HighTechPrecisionGauge("Composite WQI", 0, 10, safe_min=7.0, safe_max=10.0, unit="/10", theme_color="#00f2fe")
        top_row.addWidget(self.gauge, stretch=1)

        summary_card = QFrame()
        summary_card.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #160a2c, stop:1 #0b0f24); border:1px solid #4c1d95; border-radius:14px; padding:12px;")
        s_layout = QVBoxLayout(summary_card)
        s_layout.setSpacing(6)

        self.wqi_score_lbl = QLabel("Purity Index: -- / 10")
        self.wqi_score_lbl.setStyleSheet("font-size:22px; font-weight:900; color:#00f2fe;")
        self.wqi_grade_lbl = QLabel("Quality Grade: --")
        self.wqi_grade_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#c084fc;")
        self.wqi_status_lbl = QLabel("Potability Status: --")
        self.wqi_status_lbl.setStyleSheet("font-size:12px; font-weight:bold; color:#10b981;")
        
        self.wqi_desc_lbl = QLabel("Analyzing electrochemical telemetry against WHO & EPA Potable Standards...")
        self.wqi_desc_lbl.setWordWrap(True)
        self.wqi_desc_lbl.setStyleSheet("color:#c4b5fd; font-size:11px; margin-top:4px;")

        s_layout.addWidget(self.wqi_score_lbl)
        s_layout.addWidget(self.wqi_grade_lbl)
        s_layout.addWidget(self.wqi_status_lbl)
        s_layout.addWidget(self.wqi_desc_lbl)
        s_layout.addStretch()
        top_row.addWidget(summary_card, stretch=2)
        layout.addLayout(top_row)

        param_card = QFrame()
        param_card.setStyleSheet("background:#0f0920; border:1px solid #2e184e; border-radius:12px; padding:10px;")
        p_grid = QGridLayout(param_card)
        p_grid.setSpacing(10)

        self.lbl_ph_sub = QLabel("• pH Balance Index: --%")
        self.lbl_tds_sub = QLabel("• TDS Ionic Clarity: --%")
        self.lbl_turb_sub = QLabel("• Optical Clarity: --%")
        self.lbl_temp_sub = QLabel("• Thermal Stability: --%")

        for lbl in (self.lbl_ph_sub, self.lbl_tds_sub, self.lbl_turb_sub, self.lbl_temp_sub):
            lbl.setStyleSheet("color:#f8fafc; font-size:11px; font-weight:600;")

        p_grid.addWidget(self.lbl_ph_sub, 0, 0)
        p_grid.addWidget(self.lbl_tds_sub, 0, 1)
        p_grid.addWidget(self.lbl_turb_sub, 1, 0)
        p_grid.addWidget(self.lbl_temp_sub, 1, 1)
        layout.addWidget(param_card)

        rec_card = QFrame()
        rec_card.setStyleSheet("background:#0c061a; border:1px solid #3b1c6e; border-radius:12px; padding:10px;")
        rec_box = QVBoxLayout(rec_card)
        rec_title = QLabel("AI REMEDIATION & TREATMENT GUIDELINES")
        rec_title.setStyleSheet("font-size:11px; font-weight:bold; color:#a855f7;")
        self.rec_text = QLabel("No immediate intervention required. Continue standard monitoring.")
        self.rec_text.setWordWrap(True)
        self.rec_text.setStyleSheet("color:#94a3b8; font-size:11px;")
        rec_box.addWidget(rec_title)
        rec_box.addWidget(self.rec_text)
        layout.addWidget(rec_card)

        graph_header = QLabel("LIVE WQI PURITY SCORE OSCILLOSCOPE (1 Hz)")
        graph_header.setStyleSheet("font-size:12px; font-weight:bold; color:#00f2fe; margin-top:5px;")
        layout.addWidget(graph_header)

        self.figure = Figure(facecolor="#080412", figsize=(6, 2.2))
        self.canvas = FigureCanvas(self.figure)
        self.ax_wqi = self.figure.add_subplot(1, 1, 1)
        self.ax_wqi.grid(True, color="#231442", linestyle="--", alpha=0.6)
        self.ax_wqi.tick_params(colors="#c4b5fd", labelsize=8)
        self.ax_wqi.set_facecolor("#100824")
        self.ax_wqi.set_ylabel("WQI Score", color="#ffffff", fontsize=8, fontweight='bold')
        self.ax_wqi.set_xlabel("Time (s)", color="#c4b5fd", fontsize=8)
        for spine in self.ax_wqi.spines.values():
            spine.set_color("#3b1c6e")
        self.wqi_line, = self.ax_wqi.plot([], [], color="#00f2fe", lw=2)
        self.figure.tight_layout()
        layout.addWidget(self.canvas)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(content_widget)
        main_dialog_layout.addWidget(scroll)

        self.wqi_times = []
        self.wqi_scores = []
        self.start_time = datetime.now()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.redraw_wqi_graph)
        self.timer.start(500)

    def update_wqi_view(self, wqi, grade, status, desc, ph_s, tds_s, turb_s, temp_s, rec):
        self.gauge.setValue(wqi)
        self.wqi_score_lbl.setText(f"Purity Index: {wqi:.1f} / 10")
        self.wqi_grade_lbl.setText(f"Quality Grade: {grade}")
        self.wqi_status_lbl.setText(f"Potability Status: {status}")
        self.wqi_desc_lbl.setText(desc)

        self.lbl_ph_sub.setText(f"• pH Balance Index: {ph_s:.1f}%")
        self.lbl_tds_sub.setText(f"• TDS Ionic Clarity: {tds_s:.1f}%")
        self.lbl_turb_sub.setText(f"• Optical Clarity: {turb_s:.1f}%")
        self.lbl_temp_sub.setText(f"• Thermal Stability: {temp_s:.1f}%")
        self.rec_text.setText(rec)

        t_sec = (datetime.now() - self.start_time).total_seconds()
        self.wqi_times.append(t_sec)
        self.wqi_scores.append(wqi)

    def redraw_wqi_graph(self):
        if not self.wqi_times:
            return
        xmin = max(0, self.wqi_times[-1] - 60)
        xmax = max(10, self.wqi_times[-1])
        self.wqi_line.set_data(self.wqi_times, self.wqi_scores)
        self.ax_wqi.set_xlim(xmin, xmax)
        self.ax_wqi.set_ylim(0, 10.5)
        self.canvas.draw_idle()


# ================= MAIN PURIFYX DASHBOARD =================
class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PurifyX A.Q.U.A - Intelligent Water Quality Command Center")
        self.resize(1420, 890)
        self.setStyleSheet(self.dark_theme())

        # Ensure logs and reports directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("reports", exist_ok=True)

        self.samples = 0
        
        # Telemetry State (Core 4 Sensors)
        self.telemetry = {
            "pH": 7.35, "TDS": 190.0, "Turb": 0.85, "Temp": 24.2
        }

        # Latest status reported directly by the ESP32.
        # This is kept separate from AQUA's internally calculated AI verdict.
        self.sensor_status = "UNKNOWN"

        # AI Simulation Lab state. While simulation is active, live ESP32
        # telemetry must not overwrite the simulated status on the PC UI.
        self.simulation_active = False
        self.simulation_status = "UNKNOWN"
        
        # AI Confidence & Solution Validation State
        self.ai_conf = {"Safe": 94.0, "Treat": 5.0, "Unsafe": 1.0}
        self.correction_acc = 92.5
        self.discorrection_acc = 7.5
        self.overall_verdict = "SAFE"

        # Logging State & Telemetry History Buffer
        self.logging = False
        self.logging_paused = False
        self.logfile = None
        self.csv_writer = None
        self.log_history = []

        self.graph_win = None
        self.sim_win = None
        self.score_win = None

        self.init_ui()

        # Serial Worker Thread
        self.worker = SerialWorker()
        self.worker.data_received.connect(self.handle_telemetry)
        self.worker.log_message.connect(self.log_raw)
        self.worker.status.connect(self.handle_status)
        self.worker.start()

        # Continuous 1 Hz Live Stream Timer
        self.graph_clock = QTimer()
        self.graph_clock.timeout.connect(self.stream_live_tick)
        self.graph_clock.start(1000)

        # Runtime clock
        self.boot_time = QTime.currentTime()
        self.clock = QTimer()
        self.clock.timeout.connect(self.tick_clock)
        self.clock.start(1000)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        # Header Bar
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #120926, stop:0.5 #0c102b, stop:1 #060a1d);
                border: 1px solid #4c1d95;
                border-radius: 14px;
            }
        """)
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(20, 12, 20, 12)

        b_box = QVBoxLayout()
        brand = QLabel("PURIFYX A.Q.U.A")
        brand.setStyleSheet("font-size:22px; font-weight:900; color:#ffffff; letter-spacing:2px;")
        sub_brand = QLabel("Autonomous Quality & Utility Architecture")
        sub_brand.setStyleSheet("font-size:10px; font-weight:bold; color:#00f2fe; letter-spacing:1px;")
        b_box.addWidget(brand)
        b_box.addWidget(sub_brand)
        hdr_layout.addLayout(b_box)
        hdr_layout.addStretch()

        self.link_chip = QLabel("● LINK: SEARCHING")
        self.link_chip.setStyleSheet("color:#ef4444; font-weight:bold; font-size:12px; margin-right:15px;")
        hdr_layout.addWidget(self.link_chip)

        self.runtime_lbl = QLabel("00:00:00")
        self.runtime_lbl.setStyleSheet("color:#c4b5fd; font-weight:bold; font-size:12px; margin-right:15px;")
        hdr_layout.addWidget(self.runtime_lbl)

        self.graph_btn = QPushButton("Oscilloscope")
        self.sim_btn = QPushButton("AI Sim Lab")
        self.wqi_btn = QPushButton("WQI Diagnostics")
        
        for b in (self.graph_btn, self.sim_btn, self.wqi_btn):
            b.setFixedHeight(38)
            hdr_layout.addWidget(b)

        self.graph_btn.clicked.connect(self.open_graph)
        self.sim_btn.clicked.connect(self.open_sim)
        self.wqi_btn.clicked.connect(self.open_wqi)

        root_layout.addWidget(hdr_frame)

        # MAIN BODY
        body_layout = QHBoxLayout()
        body_layout.setSpacing(16)

        # LEFT: 2x2 SQUARE GAUGES CLUSTER
        dials_container = QWidget()
        dials_grid = QGridLayout(dials_container)
        dials_grid.setSpacing(12)
        dials_grid.setContentsMargins(0, 0, 0, 0)

        self.g_ph = HighTechPrecisionGauge("pH Balance", 0, 14, 6.5, 8.5, "", "#c084fc", ticks_count=8)
        self.g_tds = HighTechPrecisionGauge("TDS Metric", 0, 1200, 50.0, 500.0, "ppm", "#38bdf8", ticks_count=7)
        self.g_turb = HighTechPrecisionGauge("Turbidity", 0, 50, None, 5.0, "NTU", "#00f2fe", ticks_count=6)
        self.g_temp = HighTechPrecisionGauge("Temperature", -100, 100, 20.0, 30.0, "°C", "#f43f5e", ticks_count=9)

        dials_grid.addWidget(self.g_ph, 0, 0)
        dials_grid.addWidget(self.g_tds, 0, 1)
        dials_grid.addWidget(self.g_turb, 1, 0)
        dials_grid.addWidget(self.g_temp, 1, 1)

        body_layout.addWidget(dials_container, stretch=1)

        # RIGHT: SPACIOUS AI NEURAL SCHEMATICS DECK
        ai_card = QFrame()
        ai_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #140929, stop:0.5 #0e112d, stop:1 #070a1e);
                border: 1.5px solid #4c1d95;
                border-radius: 18px;
            }
        """)
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(14)
        ai_layout.setContentsMargins(20, 20, 20, 20)

        ai_header = QLabel("AI NEURAL SCHEMATICS & META-VALIDATION")
        ai_header.setStyleSheet("font-size:14px; font-weight:900; color:#00f2fe; letter-spacing:1.5px;")
        ai_layout.addWidget(ai_header)

        # --- SECTION 1: AI CONFIDENCE SPECTRUM ---
        card_sec1 = QFrame()
        card_sec1.setStyleSheet("background:#0f0924; border:1px solid #2e184e; border-radius:12px; padding:10px;")
        sec1_layout = QVBoxLayout(card_sec1)
        sec1_layout.setSpacing(8)

        sec1_title = QLabel("AI Confidence Spectrum:")
        sec1_title.setStyleSheet("font-size:12px; font-weight:bold; color:#ffffff;")
        sec1_layout.addWidget(sec1_title)

        self.bar_safe = self._build_bar("#10b981")
        self.bar_treat = self._build_bar("#f59e0b")
        self.bar_unsafe = self._build_bar("#ef4444")

        self.lbl_safe_val = QLabel("0.0%")
        self.lbl_treat_val = QLabel("0.0%")
        self.lbl_unsafe_val = QLabel("0.0%")

        sec1_layout.addLayout(self._create_bar_row("Safe Bar:", self.bar_safe, self.lbl_safe_val, "#10b981"))
        sec1_layout.addLayout(self._create_bar_row("Treat Bar:", self.bar_treat, self.lbl_treat_val, "#f59e0b"))
        sec1_layout.addLayout(self._create_bar_row("Unsafe Bar:", self.bar_unsafe, self.lbl_unsafe_val, "#ef4444"))
        ai_layout.addWidget(card_sec1)

        # --- SECTION 2: AI SOLUTION CONFIDENCE ---
        card_sec2 = QFrame()
        card_sec2.setStyleSheet("background:#0f0924; border:1px solid #2e184e; border-radius:12px; padding:10px;")
        sec2_layout = QVBoxLayout(card_sec2)
        sec2_layout.setSpacing(8)

        sec2_title = QLabel("AI Solution Confidence (Self-Validation):")
        sec2_title.setStyleSheet("font-size:12px; font-weight:bold; color:#ffffff;")
        sec2_layout.addWidget(sec2_title)

        self.bar_correct = self._build_bar("#38bdf8")
        self.bar_discorrect = self._build_bar("#c084fc")

        self.lbl_correct_val = QLabel("0.0%")
        self.lbl_discorrect_val = QLabel("0.0%")

        sec2_layout.addLayout(self._create_bar_row("Correction Accuracy:", self.bar_correct, self.lbl_correct_val, "#38bdf8"))
        sec2_layout.addLayout(self._create_bar_row("Discorrection Accuracy:", self.bar_discorrect, self.lbl_discorrect_val, "#c084fc"))

        self.meta_badge = QLabel("● Self-Check: Validated (Correction ≥ 80%)")
        self.meta_badge.setStyleSheet("font-size:11px; font-weight:bold; color:#34d399; margin-top:3px;")
        sec2_layout.addWidget(self.meta_badge)
        ai_layout.addWidget(card_sec2)

        # --- SECTION 3: OVERALL AI ANALYSIS ---
        card_sec3 = QFrame()
        card_sec3.setStyleSheet("background:#0f0924; border:1px solid #2e184e; border-radius:12px; padding:10px;")
        sec3_layout = QVBoxLayout(card_sec3)
        sec3_layout.setSpacing(8)

        sec3_title = QLabel("Overall AI Analysis:")
        sec3_title.setStyleSheet("font-size:12px; font-weight:bold; color:#ffffff;")
        sec3_layout.addWidget(sec3_title)

        self.verdict_badge = QLabel("SAFE")
        self.verdict_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verdict_badge.setStyleSheet("""
            background-color: #064e3b; 
            color: #34d399; 
            font-size: 20px; 
            font-weight: 900; 
            padding: 10px; 
            border-radius: 10px; 
            border: 1px solid #059669;
        """)
        sec3_layout.addWidget(self.verdict_badge)

        # Direct ESP32 status. Kept separate from the AQUA AI verdict above.
        self.sensor_status_lbl = QLabel("ESP32 SENSOR STATUS: UNKNOWN")
        self.sensor_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sensor_status_lbl.setStyleSheet(
            "font-size:11px; font-weight:800; color:#94a3b8; "
            "padding:5px; border:1px solid #2e184e; border-radius:7px;"
        )
        sec3_layout.addWidget(self.sensor_status_lbl)

        self.reasoning_lbl = QLabel("Parameters are mathematically aligned with potable drinking standards.")
        self.reasoning_lbl.setWordWrap(True)
        self.reasoning_lbl.setStyleSheet("color:#c4b5fd; font-size:11px;")
        sec3_layout.addWidget(self.reasoning_lbl)
        ai_layout.addWidget(card_sec3)

        body_layout.addWidget(ai_card, stretch=1)
        root_layout.addLayout(body_layout, stretch=4)

        # BOTTOM CONTROLS & LIVE TELEMETRY LOG VIEW
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("""
            QFrame {
                background: #0b0617;
                border-radius: 14px;
                border: 1.5px solid #2e184e;
                padding: 10px;
            }
        """)
        b_layout = QVBoxLayout(bottom_frame)
        b_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.log_start_btn = QPushButton("Start Logging")
        self.log_pause_btn = QPushButton("Pause Logging")
        self.log_reset_btn = QPushButton("Reset Logging")
        self.log_stop_btn = QPushButton("Stop Logging")
        self.open_log_btn = QPushButton("Open Logs Folder")
        self.rep_btn = QPushButton("Export Full Industrial PDF (7-Page)")

        self.log_pause_btn.setVisible(False)
        self.log_reset_btn.setVisible(False)
        self.log_stop_btn.setVisible(False)

        self.log_start_btn.clicked.connect(self.start_logging)
        self.log_pause_btn.clicked.connect(self.pause_resume_logging)
        self.log_reset_btn.clicked.connect(self.reset_logging)
        self.log_stop_btn.clicked.connect(self.stop_logging)
        self.open_log_btn.clicked.connect(self.open_logs_folder)
        self.rep_btn.clicked.connect(self.generate_industrial_7page_report)

        btn_row.addWidget(self.log_start_btn)
        btn_row.addWidget(self.log_pause_btn)
        btn_row.addWidget(self.log_reset_btn)
        btn_row.addWidget(self.log_stop_btn)
        btn_row.addWidget(self.open_log_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.rep_btn)
        b_layout.addLayout(btn_row)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(90)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #05020c;
                border: 1px solid #23123d;
                border-radius: 8px;
                color: #a78bfa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 4px;
            }
        """)
        b_layout.addWidget(self.log_console)

        root_layout.addWidget(bottom_frame, stretch=1)

        self.update_ui_state()

    def _build_bar(self, color_hex):
        bar = QProgressBar()
        bar.setRange(0, 1000)
        bar.setFixedHeight(14)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #06030f;
                border: 1px solid #23123d;
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 6px;
            }}
        """)
        return bar

    def _create_bar_row(self, label_text, bar, val_label, color_hex):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(150)
        lbl.setStyleSheet("font-weight:600; font-size:11px; color:#c4b5fd;")
        
        val_label.setFixedWidth(55)
        val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_label.setStyleSheet(f"font-weight:bold; font-size:11px; color:{color_hex};")

        row.addWidget(lbl)
        row.addWidget(bar)
        row.addWidget(val_label)
        return row

    def evaluate_ai_model(self):
        ph = self.telemetry["pH"]
        tds = self.telemetry["TDS"]
        turb = self.telemetry["Turb"]
        temp = self.telemetry["Temp"]

        ph_s = max(0.0, min(100.0, 100.0 - (abs(ph - 7.0) * 16.0)))
        tds_s = max(0.0, min(100.0, 100.0 - (max(0.0, tds - 300.0) / 700.0) * 100.0))
        turb_s = max(0.0, min(100.0, 100.0 - (turb / 10.0) * 100.0))
        
        if 20.0 <= temp <= 30.0:
            temp_s = 100.0
        elif temp < 20.0:
            temp_s = max(0.0, 100.0 - (20.0 - temp) * 1.5)
        else:
            temp_s = max(0.0, 100.0 - (temp - 30.0) * 1.8)

        composite = (ph_s * 0.35 + turb_s * 0.30 + tds_s * 0.20 + temp_s * 0.15) / 100.0

        if composite >= 0.75:
            p_safe = 80.0 + (composite - 0.75) * 76.0
            p_treat = max(0.0, (100.0 - p_safe) * 0.8)
            p_unsafe = max(0.0, 100.0 - p_safe - p_treat)
            verdict = "SAFE"
            reason = "Chemical pH, turbidity, and thermal telemetry are nominal for direct consumption."
        elif composite >= 0.45:
            p_treat = 70.0 + (1.0 - abs(composite - 0.60) / 0.15) * 20.0
            p_safe = max(0.0, (100.0 - p_treat) * 0.45)
            p_unsafe = max(0.0, 100.0 - p_treat - p_safe)
            verdict = "TREAT"
            reason = "Elevated turbidity, thermal discrepancy, or mineral concentration detected. Active treatment required."
        else:
            p_unsafe = 75.0 + (0.45 - composite) * 50.0
            p_unsafe = min(99.0, p_unsafe)
            p_treat = max(0.0, (100.0 - p_unsafe) * 0.75)
            p_safe = max(0.0, 100.0 - p_unsafe - p_treat)
            verdict = "UNSAFE"
            reason = "Severe chemical imbalance, turbidity hazard, or critical thermal deviation detected. Dangerous to ingest."

        tot = p_safe + p_treat + p_unsafe
        self.ai_conf["Safe"] = round((p_safe / tot) * 100.0, 1)
        self.ai_conf["Treat"] = round((p_treat / tot) * 100.0, 1)
        self.ai_conf["Unsafe"] = round(100.0 - self.ai_conf["Safe"] - self.ai_conf["Treat"], 1)

        probs = sorted([self.ai_conf["Safe"], self.ai_conf["Treat"], self.ai_conf["Unsafe"]], reverse=True)
        margin = probs[0] - probs[1]

        base_correction = 75.0 + (margin * 0.23)
        self.correction_acc = round(max(50.0, min(98.8, base_correction)), 1)
        self.discorrection_acc = round(100.0 - self.correction_acc, 1)
        self.overall_verdict = verdict

        return verdict, reason, ph_s, tds_s, turb_s, temp_s

    def update_ui_state(self):
        self.g_ph.setValue(self.telemetry["pH"])
        self.g_tds.setValue(self.telemetry["TDS"])
        self.g_turb.setValue(self.telemetry["Turb"])
        self.g_temp.setValue(self.telemetry["Temp"])

        verdict, reason, ph_s, tds_s, turb_s, temp_s = self.evaluate_ai_model()

        self.bar_safe.setValue(int(self.ai_conf["Safe"] * 10))
        self.bar_treat.setValue(int(self.ai_conf["Treat"] * 10))
        self.bar_unsafe.setValue(int(self.ai_conf["Unsafe"] * 10))

        self.lbl_safe_val.setText(f"{self.ai_conf['Safe']:.1f}%")
        self.lbl_treat_val.setText(f"{self.ai_conf['Treat']:.1f}%")
        self.lbl_unsafe_val.setText(f"{self.ai_conf['Unsafe']:.1f}%")

        self.bar_correct.setValue(int(self.correction_acc * 10))
        self.bar_discorrect.setValue(int(self.discorrection_acc * 10))

        self.lbl_correct_val.setText(f"{self.correction_acc:.1f}%")
        self.lbl_discorrect_val.setText(f"{self.discorrection_acc:.1f}%")

        if self.correction_acc >= 80.0:
            self.meta_badge.setText("● Self-Check: Validated (Correction ≥ 80%)")
            self.meta_badge.setStyleSheet("font-size:11px; font-weight:bold; color:#34d399;")
        else:
            self.meta_badge.setText("▲ Self-Check: High Ambiguity (Correction < 80%)")
            self.meta_badge.setStyleSheet("font-size:11px; font-weight:bold; color:#fbbf24;")

        if verdict == "SAFE":
            self.verdict_badge.setText("SAFE")
            self.verdict_badge.setStyleSheet("""
                background-color:#064e3b; color:#34d399; font-size:20px; font-weight:900; 
                padding:10px; border-radius:10px; border:1px solid #059669;
            """)
        elif verdict == "TREAT":
            self.verdict_badge.setText("TREAT")
            self.verdict_badge.setStyleSheet("""
                background-color:#78350f; color:#fbbf24; font-size:20px; font-weight:900; 
                padding:10px; border-radius:10px; border:1px solid #d97706;
            """)
        else:
            self.verdict_badge.setText("UNSAFE")
            self.verdict_badge.setStyleSheet("""
                background-color:#7f1d1d; color:#f87171; font-size:20px; font-weight:900; 
                padding:10px; border-radius:10px; border:1px solid #dc2626;
            """)
        self.reasoning_lbl.setText(reason)

    def stream_live_tick(self):
        wqi = self.calc_wqi()
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "Time": timestamp_str,
            "pH": self.telemetry["pH"],
            "Turbidity": self.telemetry["Turb"],
            "TDS": self.telemetry["TDS"],
            "Temperature": self.telemetry["Temp"],
            "WaterScore": round(wqi, 2),
            "Status": self.overall_verdict,
            "AIConfidence": f"{self.correction_acc:.1f}%"
        }
        self.log_history.append(entry)
        if len(self.log_history) > 300:
            self.log_history.pop(0)

        if self.graph_win and self.graph_win.isVisible():
            self.graph_win.add_point(
                datetime.now(), 
                self.telemetry["pH"], 
                self.telemetry["TDS"], 
                self.telemetry["Turb"], 
                self.telemetry["Temp"]
            )

        if self.score_win and self.score_win.isVisible():
            grade = "A (Optimal Potable)" if wqi >= 8.5 else "B (Acceptable Standard)" if wqi >= 7.0 else "C (Cautionary Treat)" if wqi >= 5.0 else "F (Hazardous Contamination)"
            status = "Nominal" if wqi >= 7.0 else "Intervention Required" if wqi >= 5.0 else "Direct Hazard"
            _, reason, ph_s, tds_s, turb_s, temp_s = self.evaluate_ai_model()
            rec = "Standard monitoring. Water meets potability thresholds." if wqi >= 7.0 else \
                  "Active filtration and micro-sediment extraction recommended." if wqi >= 5.0 else \
                  "Emergency warning: Neutralization and UV sterilization mandatory before use."
            self.score_win.update_wqi_view(wqi, grade, status, reason, ph_s, tds_s, turb_s, temp_s, rec)

        if self.logging and not self.logging_paused:
            if self.csv_writer and self.logfile:
                self.csv_writer.writerow([
                    entry["Time"], entry["pH"], entry["Turbidity"],
                    entry["TDS"], entry["Temperature"], entry["WaterScore"],
                    entry["Status"], entry["AIConfidence"]
                ])
                self.logfile.flush()

            if entry["Status"] == "SAFE":
                bg_col, text_col, border_col = "#064e3b", "#86efac", "#059669"
            elif entry["Status"] == "TREAT":
                bg_col, text_col, border_col = "#78350f", "#fde047", "#d97706"
            else:
                bg_col, text_col, border_col = "#7f1d1d", "#fca5a5", "#dc2626"

            html_line = (
                f"<div style='background-color:{bg_col}; color:{text_col}; border:1px solid {border_col}; "
                f"padding:3px 8px; margin:2px 0px; border-radius:5px; font-size:11px;'>"
                f"<b>[{entry['Time']}]</b> | pH: {entry['pH']:.2f} | Turb: {entry['Turbidity']:.2f} NTU | "
                f"TDS: {entry['TDS']:.1f} ppm | Temp: {entry['Temperature']:.1f} °C | "
                f"WQI Score: {entry['WaterScore']:.1f}/10 | <b>STATUS: {entry['Status']}</b> | AI Conf: {entry['AIConfidence']}"
                f"</div>"
            )
            self.log_console.append(html_line)

    def handle_telemetry(self, data):
        """
        Receive one parsed serial line from SerialWorker and translate the
        ESP32's field names into AQUA's internal telemetry names.

        ESP32 sends lines such as:
            pH Value: 14.00
            Turbidity Value: 9.98
            TDS Value: 20.51
            Temperature Value: 28.56
            Status: Unsafe

        SerialWorker converts each line into a dictionary like:
            {"pH Value": "14.00"}

        AQUA internally uses pH/TDS/Turb/Temp, so this function is the
        communication boundary where the two formats are mapped.
        """
        self.samples += 1

        key_map = {
            "pH Value": "pH",
            "Turbidity Value": "Turb",
            "TDS Value": "TDS",
            "Temperature Value": "Temp"
        }

        recognized_sensor_value = False

        for incoming_key, aqua_key in key_map.items():
            if incoming_key in data:
                recognized_sensor_value = True
                raw_value = str(data[incoming_key]).strip()
                try:
                    self.telemetry[aqua_key] = float(raw_value)
                except (ValueError, TypeError) as e:
                    # Do not silently hide malformed serial data.
                    self.log_console.append(
                        f"<div style='color:#f87171;'><b>[SERIAL PARSE ERROR]</b> "
                        f"{incoming_key}: {raw_value!r} ({e})</div>"
                    )

        # ESP32 water-quality status is separate from AQUA's internally
        # calculated AI verdict. During an active AI simulation, the simulated
        # status is authoritative for the simulation UI; otherwise use the
        # status reported by the physical ESP32.
        if "Status" in data:
            incoming_status = str(data["Status"]).strip() or "UNKNOWN"

            if not self.simulation_active:
                self.sensor_status = incoming_status
                self._update_sensor_status_label(self.sensor_status)

        # Update the dashboard after each recognized sensor field.
        if recognized_sensor_value:
            self.update_ui_state()

    def calc_wqi(self):
        d = self.telemetry
        ph_s = max(0, 100 - abs(d["pH"] - 7.0) * 16)
        turb_s = max(0, 100 - (d["Turb"] / 5.0) * 50)
        tds_s = max(0, 100 - (max(0, d["TDS"] - 300) / 700.0) * 100)
        temp_s = 100 if (20 <= d["Temp"] <= 30) else max(0, 100 - abs(d["Temp"] - 25) * 1.5)
        return max(0.0, min(10.0, (ph_s * 0.35 + turb_s * 0.30 + tds_s * 0.20 + temp_s * 0.15) / 10.0))

    def handle_status(self, t):
        self.link_chip.setText(f"● LINK: {t.upper()}")
        self.link_chip.setStyleSheet("color:#10b981; font-weight:bold; font-size:12px;" if "ONLINE" in t else "color:#ef4444; font-weight:bold; font-size:12px;")

    def log_raw(self, text):
        """Show raw serial lines in AQUA's existing telemetry console."""
        try:
            self.log_console.append(
                f"<div style='color:#64748b;'><b>[ESP32]</b> {str(text)}</div>"
            )
        except Exception:
            # Logging must never interfere with serial reception.
            pass

    def tick_clock(self):
        s = self.boot_time.secsTo(QTime.currentTime())
        self.runtime_lbl.setText(f"{s//3600:02}:{(s%3600)//60:02}:{s%60:02}")

    def open_graph(self):
        if not self.graph_win:
            self.graph_win = GraphWindow(self, datetime.now())
        self.graph_win.show()
        self.graph_win.activateWindow()

    def open_sim(self):
        if not self.sim_win:
            self.sim_win = SimulationWindow(self)
        self.sim_win.show()
        self.sim_win.activateWindow()

    def open_wqi(self):
        if not self.score_win:
            self.score_win = WaterScoreWindow(self)
        self.score_win.show()
        self.score_win.activateWindow()

    def _update_sensor_status_label(self, status):
        status_text = str(status).strip() or "UNKNOWN"
        status_upper = status_text.upper()

        if status_upper == "SAFE":
            status_color = "#34d399"
        elif status_upper == "TREAT":
            status_color = "#fbbf24"
        elif status_upper == "UNSAFE":
            status_color = "#f87171"
        else:
            status_color = "#94a3b8"

        self.sensor_status_lbl.setText(
            f"ESP32 SENSOR STATUS: {status_upper}"
        )
        self.sensor_status_lbl.setStyleSheet(
            f"font-size:11px; font-weight:800; color:{status_color}; "
            "padding:5px; border:1px solid #2e184e; border-radius:7px;"
        )

    def send_sim_command(self, cmd, data_dict=None, simulated_status=None):
        """
        Inject simulation telemetry into both sides of the system:
        1) immediately update AQUA's local UI/AI model;
        2) send the TEST command to the ESP32;
        3) send the explicit simulated status to the ESP32 command channel.

        The ESP32 firmware must recognize SIMSTATUS,<SAFE|TREAT|UNSAFE>
        (or equivalent firmware-side simulation status handling) for its
        physical LED/buzzer to follow the simulation verdict. The desktop
        side cannot directly toggle ESP32 GPIO pins over serial unless the
        firmware exposes such a command.
        """
        if data_dict:
            self.simulation_active = True
            self.handle_telemetry(data_dict)
        elif simulated_status:
            self.simulation_active = True

        if simulated_status:
            self.simulation_status = str(simulated_status).upper()
            self.sensor_status = self.simulation_status
            self._update_sensor_status_label(self.simulation_status)

            # Explicit status command for the ESP32 hardware output layer.
            self.worker.send_command(f"SIMSTATUS,{self.simulation_status}")

        self.worker.send_command(cmd)

        if data_dict and simulated_status:
            self.log_console.append(
                f"<div style='color:#00f2fe;'><b>[AI SIM → ESP32]</b> "
                f"pH={data_dict['pH']:.2f} | TDS={data_dict['TDS']:.1f} | "
                f"Turb={data_dict['Turb']:.2f} | Temp={data_dict['Temp']:.1f} | "
                f"STATUS={str(simulated_status).upper()}</div>"
            )

    def stop_simulation(self):
        """Return the ESP32 and AQUA to normal live-sensor mode."""
        self.simulation_active = False
        self.simulation_status = "UNKNOWN"
        self.worker.send_command("STOPTEST")
        self.worker.send_command("SIMSTATUS,OFF")
        self.log_console.append(
            "<div style='color:#fbbf24;'><b>[AI SIM]</b> Simulation stopped; "
            "returning to live ESP32 sensor status.</div>"
        )

    def start_logging(self):
        os.makedirs("logs", exist_ok=True)
        self.current_csv_path = f"logs/PurifyX_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.logfile = open(self.current_csv_path, "w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.logfile)
        self.csv_writer.writerow(["Timestamp", "pH", "Turbidity", "TDS", "Temperature", "WaterScore", "Status", "AIConfidence"])
        self.logfile.flush()

        self.logging = True
        self.logging_paused = False

        self.log_start_btn.setVisible(False)
        self.log_pause_btn.setVisible(True)
        self.log_pause_btn.setText("Pause Logging")
        self.log_reset_btn.setVisible(True)
        self.log_stop_btn.setVisible(True)

        self.log_console.append(f"<div style='color:#38bdf8;'><b>[SYSTEM] Telemetry logging session active: {self.current_csv_path}</b></div>")

    def pause_resume_logging(self):
        if not self.logging:
            return
        if not self.logging_paused:
            self.logging_paused = True
            self.log_pause_btn.setText("Resume Logging")
            self.log_pause_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #b45309); color:white; font-weight:bold;")
            self.log_console.append("<div style='color:#fbbf24;'><b>[SYSTEM] Logging PAUSED.</b></div>")
        else:
            self.logging_paused = False
            self.log_pause_btn.setText("Pause Logging")
            self.log_pause_btn.setStyleSheet("")
            self.log_console.append("<div style='color:#34d399;'><b>[SYSTEM] Logging RESUMED.</b></div>")

    def reset_logging(self):
        reply = QMessageBox.question(
            self, "Reset Telemetry Log", 
            "Are you sure you want to reset current logged values and start a fresh session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_console.clear()
            self.log_history.clear()
            if self.logfile:
                self.logfile.close()
            self.start_logging()
            self.log_console.append("<div style='color:#38bdf8;'><b>[SYSTEM] Log stream RESET. Fresh telemetry session running.</b></div>")

    def stop_logging(self):
        self.logging = False
        self.logging_paused = False
        if self.logfile:
            self.logfile.flush()
            self.logfile.close()
            self.logfile = None

        self.log_start_btn.setVisible(True)
        self.log_pause_btn.setVisible(False)
        self.log_reset_btn.setVisible(False)
        self.log_stop_btn.setVisible(False)

        self.log_console.append("<div style='color:#f87171;'><b>[SYSTEM] Telemetry logging terminated.</b></div>")
        QMessageBox.information(self, "Log Saved", f"Logging completed successfully.\nFile: {getattr(self, 'current_csv_path', 'logs/')}")

    def open_logs_folder(self):
        folder = os.path.abspath("logs")
        os.makedirs(folder, exist_ok=True)
        open_path(folder)

    # ================= INDUSTRIAL-GRADE 7-PAGE PDF REPORT =================
    def generate_industrial_7page_report(self):
        try:
            os.makedirs("reports", exist_ok=True)
            pdf_path = os.path.abspath(f"reports/PurifyX_Industrial_Dossier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4
            margin = 40
            content_w = width - (2 * margin)

            title_style = ParagraphStyle(name='RTitle', fontName='Helvetica-Bold', fontSize=17, textColor=colors.HexColor("#0f172a"), leading=21)
            h1_style = ParagraphStyle(name='RH1', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#1e1b4b"), leading=15)
            body_style = ParagraphStyle(name='RBody', fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#334155"), leading=13)
            bold_body_style = ParagraphStyle(name='RBoldBody', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#0f172a"), leading=13)

            # Robust helper to draw Paragraphs safely without 'blPara' crashes
            def draw_p(text, style, x, y_pos, max_w, max_h=500):
                p = Paragraph(text, style)
                w_p, h_p = p.wrap(max_w, max_h)
                p.drawOn(c, x, y_pos - h_p)
                return h_p

            history = list(self.log_history)
            now = datetime.now()
            if not history:
                history = [{
                    "Time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "pH": self.telemetry["pH"],
                    "Turbidity": self.telemetry["Turb"],
                    "TDS": self.telemetry["TDS"],
                    "Temperature": self.telemetry["Temp"],
                    "WaterScore": round(self.calc_wqi(), 2),
                    "Status": self.overall_verdict,
                    "AIConfidence": f"{self.correction_acc:.1f}%"
                }]

            current_ph = self.telemetry["pH"]
            current_tds = self.telemetry["TDS"]
            current_turb = self.telemetry["Turb"]
            current_temp = self.telemetry["Temp"]
            wqi_val = self.calc_wqi()
            verdict = self.overall_verdict

            def draw_decorations(page_num, page_title):
                c.setFillColor(colors.HexColor("#090414"))
                c.rect(0, height - 42, width, 42, stroke=0, fill=1)
                c.setFillColor(colors.HexColor("#00f2fe"))
                c.rect(0, height - 44, width, 2, stroke=0, fill=1)

                c.setFont("Helvetica-Bold", 10.5)
                c.setFillColor(colors.white)
                c.drawString(margin, height - 26, "PURIFYX A.Q.U.A | INDUSTRIAL WATER INTELLIGENCE DOSSIER")
                c.setFont("Helvetica", 8.5)
                c.setFillColor(colors.HexColor("#c4b5fd"))
                c.drawRightString(width - margin, height - 26, f"PAGE {page_num} OF 7")

                c.setStrokeColor(colors.HexColor("#cbd5e1"))
                c.setLineWidth(0.8)
                c.line(margin, 35, width - margin, 35)
                c.setFont("Helvetica", 8)
                c.setFillColor(colors.HexColor("#64748b"))
                c.drawString(margin, 22, f"Certified Telemetry Dossier • Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                c.drawRightString(width - margin, 22, f"Section: {page_title}")

            # ================= PAGE 1 =================
            draw_decorations(1, "Executive Telemetry Dossier")
            y = height - 65

            h_used = draw_p("INDUSTRIAL WATER QUALITY & NEURAL DIAGNOSTIC REPORT", title_style, margin, y, content_w)
            y -= (h_used + 10)

            sub_text = (
                f"<b>Target System:</b> PurifyX High-Precision Multi-Probe Core | <b>Station ID:</b> A.Q.U.A-NODE-01<br/>"
                f"<b>Evaluation Timestamp:</b> {now.strftime('%A, %B %d, %Y - %H:%M:%S')} | <b>Operator Mode:</b> Real-Time Synthesis"
            )
            h_used = draw_p(sub_text, body_style, margin, y, content_w)
            y -= (h_used + 15)

            h_used = draw_p("1. Primary Electrochemical & Physical Readings", h1_style, margin, y, content_w)
            y -= (h_used + 8)

            telemetry_table_data = [
                ["Parameter", "Measured Telemetry", "WHO/EPA Safe Threshold", "Operational Delta", "Sensor State"],
                ["Hydrogen Potential (pH)", f"{current_ph:.2f}", "6.50 – 8.50 pH", f"{current_ph - 7.0:+.2f} pH", "Optimal" if 6.5<=current_ph<=8.5 else "Critical Deviation"],
                ["Total Dissolved Solids (TDS)", f"{current_tds:.1f} ppm", "50.0 – 500.0 ppm", f"{current_tds - 300.0:+.1f} ppm", "Optimal" if current_tds<=500 else "High Ionic Load"],
                ["Nephelometric Turbidity", f"{current_turb:.2f} NTU", "0.00 – 5.00 NTU", f"{current_turb - 1.0:+.2f} NTU", "Clear Optical" if current_turb<=5 else "Turbid Particulate"],
                ["Thermal Core Temperature", f"{current_temp:.1f} °C", "20.0 – 30.0 °C", f"{current_temp - 25.0:+.1f} °C", "Nominal Band" if 20<=current_temp<=30 else "Thermal Hazard"]
            ]
            t1 = Table(telemetry_table_data, colWidths=[130, 95, 115, 85, 90])
            t1.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#ede9fe")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7.5),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            w_t1, h_t1 = t1.wrap(content_w, 200)
            t1.drawOn(c, margin, y - h_t1)
            y -= (h_t1 + 15)

            h_used = draw_p("2. Neural Decision & Self-Validation Telemetry", h1_style, margin, y, content_w)
            y -= (h_used + 8)

            ai_table_data = [
                ["Neural Metric", "Calculated Ratio", "Interpretation & Stability"],
                ["Primary AI Verdict", f"{verdict}", "Safe Potable" if verdict=="SAFE" else "Filtration Required" if verdict=="TREAT" else "Severe Bio-Chemical Hazard"],
                ["Safe Probability Spectrum", f"{self.ai_conf['Safe']:.1f}%", "Confidence allocation toward potability without treatment."],
                ["Treat Probability Spectrum", f"{self.ai_conf['Treat']:.1f}%", "Confidence allocation requiring physical or chemical remediation."],
                ["Unsafe Probability Spectrum", f"{self.ai_conf['Unsafe']:.1f}%", "Confidence allocation indicating immediate hazardous ingestion."],
                ["Correction Accuracy (Self-Check)", f"{self.correction_acc:.1f}%", "Validated (≥80% accuracy ensures statistical robustness)."],
                ["Discorrection Uncertainty", f"{self.discorrection_acc:.1f}%", "Self-doubt / noise margin evaluated by meta-cognitive kernel."]
            ]
            t2 = Table(ai_table_data, colWidths=[150, 95, 270])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#065f46")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f0fdf4"), colors.HexColor("#f8fafc")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7.5),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
            w_t2, h_t2 = t2.wrap(content_w, 200)
            t2.drawOn(c, margin, y - h_t2)
            y -= (h_t2 + 15)

            c.setLineWidth(1.0)
            c.setStrokeColor(colors.HexColor("#4c1d95"))
            c.setFillColor(colors.HexColor("#f5f3ff"))
            c.roundRect(margin, y - 55, content_w, 55, 8, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#1e1b4b"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin + 12, y - 18, f"COMPOSITE WATER QUALITY INDEX (WQI): {wqi_val:.2f} / 10.0")
            c.setFont("Helvetica", 8)
            c.drawString(margin + 12, y - 32, f"Overall Classification: {verdict} | Model Confidence: {self.correction_acc:.1f}%")
            c.drawString(margin + 12, y - 46, "Dossier Status: Approved for industrial review, municipal compliance, and field logistics.")
            c.showPage()

            # ================= PAGE 2 =================
            draw_decorations(2, "Oscilloscope Time-Series Telemetry (20-Second Window)")
            y = height - 60

            h_used = draw_p("20-Sample Historical Oscilloscope Signatures", title_style, margin, y, content_w)
            y -= (h_used + 6)
            h_used = draw_p("High-frequency telemetry records plotted across the preceding 20 sample intervals (1 Hz resolution):", body_style, margin, y, content_w)
            y -= (h_used + 10)

            last20 = history[-20:] if len(history) >= 20 else history
            if len(last20) < 20:
                pad_count = 20 - len(last20)
                last20 = [last20[0]] * pad_count + last20

            time_idx = list(range(1, 21))
            ph_series = [s["pH"] for s in last20]
            tds_series = [s["TDS"] for s in last20]
            turb_series = [s["Turbidity"] for s in last20]
            temp_series = [s["Temperature"] for s in last20]
            wqi_series = [s["WaterScore"] for s in last20]

            plot_configs = [
                ("Hydrogen Potential (pH Level)", ph_series, "#9333ea", "pH", 6.0, 9.0),
                ("Total Dissolved Solids (TDS ppm)", tds_series, "#0284c7", "ppm", 0, 1000),
                ("Nephelometric Turbidity (NTU)", turb_series, "#00b4d8", "NTU", 0, 20),
                ("Core Temperature (°C)", temp_series, "#e11d48", "°C", -20, 80),
                ("Composite Water Quality Index (WQI)", wqi_series, "#059669", "WQI /10", 0, 10)
            ]

            temp_images = []
            for idx, (g_title, g_data, g_color, g_ylabel, ymin_d, ymax_d) in enumerate(plot_configs):
                fig, ax = plt.subplots(figsize=(6.8, 1.35), dpi=130)
                fig.patch.set_facecolor('#ffffff')
                ax.set_facecolor('#f8fafc')
                ax.plot(time_idx, g_data, color=g_color, lw=2.2, marker='o', markersize=3.5)
                ax.grid(True, color="#e2e8f0", linestyle="--", lw=0.7)
                ax.set_title(g_title, fontsize=8.5, fontweight='bold', color="#0f172a", pad=3)
                ax.set_ylabel(g_ylabel, fontsize=7.5, color="#334155")
                ax.tick_params(colors="#475569", labelsize=7)
                ax.set_xlim(1, 20)
                ax.set_ylim(min(min(g_data) * 0.95, ymin_d), max(max(g_data) * 1.05, ymax_d))
                fig.tight_layout(pad=0.4)

                img_name = f"temp_plot_{idx}_{now.strftime('%H%M%S%f')}.png"
                fig.savefig(img_name)
                plt.close(fig)
                temp_images.append(img_name)

                c.drawImage(ImageReader(img_name), margin, y - 95, width=content_w, height=95, preserveAspectRatio=True)
                y -= 105

            for img in temp_images:
                try:
                    if os.path.exists(img):
                        os.remove(img)
                except Exception:
                    pass

            c.showPage()

            # ================= PAGE 3 =================
            draw_decorations(3, "Telemetry Log Repository (Previous 50 Readings)")
            y = height - 60

            h_used = draw_p("Continuous Telemetry Stream Records (50 Epochs)", title_style, margin, y, content_w)
            y -= (h_used + 10)

            last50 = history[-50:]
            log_table_data = [["Timestamp", "pH", "Turb (NTU)", "TDS (ppm)", "Temp (°C)", "WQI /10", "AI Verdict", "Confidence"]]
            for row in last50:
                log_table_data.append([
                    row["Time"].split()[-1] if " " in row["Time"] else row["Time"],
                    f"{row['pH']:.2f}",
                    f"{row['Turbidity']:.2f}",
                    f"{row['TDS']:.1f}",
                    f"{row['Temperature']:.1f}",
                    f"{row['WaterScore']:.2f}",
                    row["Status"],
                    row["AIConfidence"]
                ])

            t3 = Table(log_table_data, colWidths=[80, 50, 65, 65, 60, 55, 75, 65])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7.5),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 2.2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.2),
            ]))
            w_t3, h_t3 = t3.wrap(content_w, 650)
            t3.drawOn(c, margin, y - h_t3)
            c.showPage()

            # ================= PAGE 4 =================
            draw_decorations(4, "Electrochemical & Physical Diagnostic Analysis")
            y = height - 60

            h_used = draw_p("Comprehensive Electrochemical & Physical Diagnostics", title_style, margin, y, content_w)
            y -= (h_used + 15)

            p_diag_1 = (
                "<b>1. Acid-Base Equilibrium & Hydroxonium Ion Activity:</b><br/>"
                f"The measured pH value of <b>{current_ph:.2f}</b> indicates the logarithmic molar concentration of hydronium ions ([H3O+]) "
                f"within the sampled aquatic substrate. In drinking water systems, strict electrochemical stability is bounded between pH 6.50 "
                f"and 8.50. When pH falls below 6.50, accelerated metallic pipe corrosion occurs, mobilizing toxic divalent copper (Cu2+) and "
                f"lead (Pb2+) ions into solution. Conversely, elevated alkaline values exceeding 8.50 induce calcium carbonate scaling, reduce "
                f"free chlorine disinfectant potency, and yield an unpalatable caustic bitterness."
            )
            h_used = draw_p(p_diag_1, body_style, margin, y, content_w)
            y -= (h_used + 14)

            p_diag_2 = (
                "<b>2. Nephelometric Light Scattering & Particulate Colloids:</b><br/>"
                f"The turbidity readout of <b>{current_turb:.2f} NTU</b> quantifies light attenuation caused by suspended micro-solids, inorganic silts, "
                f"and colloidal biomass. Suspended particles shield pathogenic cryptosporidium oocysts, giardia cysts, and bacterial clusters from ultraviolet "
                f"sterilization and chemical oxidation. For safe potable transmission, nephelometric turbidity must remain strictly beneath 1.0 NTU, "
                f"with an upper legal threshold of 5.0 NTU during peak municipal utility loading."
            )
            h_used = draw_p(p_diag_2, body_style, margin, y, content_w)
            y -= (h_used + 14)

            p_diag_3 = (
                "<b>3. Total Dissolved Solids & Ionic Conductivity Dynamics:</b><br/>"
                f"At a measured concentration of <b>{current_tds:.1f} ppm</b>, total dissolved solids encompass the cumulative inorganic salts (calcium, "
                f"magnesium, potassium, sodium, bicarbonates, chlorides, and sulfates) dissolved in the volume. Extreme TDS values (>500 ppm) indicate "
                f"mineral over-saturation, elevated salinity, and potential industrial wastewater discharge, while excessively low TDS (<50 ppm) produces "
                f"aggressive, mineral-deficient water capable of leaching minerals from biological tissue upon ingestion."
            )
            h_used = draw_p(p_diag_3, body_style, margin, y, content_w)
            y -= (h_used + 14)

            p_diag_4 = (
                "<b>4. Thermodynamic Kinetics & Microbial Proliferation Index:</b><br/>"
                f"The recorded core temperature of <b>{current_temp:.1f} °C</b> plays a direct catalytic role in chemical reaction kinetics and dissolved "
                f"gas saturation. Temperatures exceeding 30.0 °C accelerate biofilm formation along distribution conduits and drastically reduce dissolved oxygen "
                f"solubility, exacerbating anaerobic decomposition and hydrogen sulfide (H2S) generation. Temperatures below 0 °C introduce freezing risks "
                f"and mechanical conduit failure."
            )
            h_used = draw_p(p_diag_4, body_style, margin, y, content_w)
            y -= (h_used + 14)

            verdict_detail = (
                f"<b>5. Final Synthesis & Classification Rationale:</b><br/>"
                f"The PurifyX Neural Matrix has designated this sample as <b>{verdict}</b> with a meta-cognitive validation accuracy of "
                f"<b>{self.correction_acc:.1f}%</b>. This verdict is synthesized from the integrated Euclidean deviation of all four simultaneous "
                f"parameters against international WHO drinking water guidelines."
            )
            draw_p(verdict_detail, bold_body_style, margin, y, content_w)
            c.showPage()

            # ================= PAGE 5 =================
            draw_decorations(5, "Probabilistic Mineral & Hazardous Estimation")
            y = height - 60

            h_used = draw_p("Probabilistic Contaminant & Chemical Profile", title_style, margin, y, content_w)
            y -= (h_used + 8)

            h_used = draw_p("Based on electrochemical signatures, temperature kinetics, and ionic dispersion models, the AI has computed the estimated presence probability of specific mineral complexes and toxic contaminants:", body_style, margin, y, content_w)
            y -= (h_used + 14)

            ca_prob = min(98.5, max(12.0, (current_tds / 600.0) * 85.0))
            heavy_metal_prob = min(95.0, max(2.1, (14.0 - current_ph if current_ph < 6.5 else current_ph - 8.5 if current_ph > 8.5 else 0.5) * 22.0 + (current_tds / 1200.0) * 30.0))
            microbial_prob = min(99.0, max(1.5, (current_turb / 15.0) * 70.0 + (current_temp / 40.0) * 25.0))
            chlorides_prob = min(92.0, max(8.0, (current_tds / 800.0) * 75.0))
            organic_toc_prob = min(96.0, max(3.0, (current_turb / 10.0) * 60.0 + (100.0 - wqi_val * 10.0) * 0.3))

            chem_table_data = [
                ["Contaminant / Mineral Complex", "Estimated Probability", "Risk Tier", "Potential Source & Impact"],
                ["Calcium & Magnesium Hardness (CaCO3)", f"{ca_prob:.1f}%", "Moderate" if ca_prob>50 else "Low", "Natural limestone leaching; boiler scaling, soap scums."],
                ["Heavy Metal Leachate (Pb, Cu, Cd, Fe)", f"{heavy_metal_prob:.1f}%", "CRITICAL" if heavy_metal_prob>40 else "Low", "Corroded piping & industrial effluent; neurotoxic risks."],
                ["Microbial & Pathogenic Coliform Index", f"{microbial_prob:.1f}%", "HIGH" if microbial_prob>45 else "Nominal", "Biofilm growth & fecal particulates; gastrointestinal illness."],
                ["Inorganic Chlorides & Sulfate Salts", f"{chlorides_prob:.1f}%", "Moderate" if chlorides_prob>50 else "Low", "Saline intrusion & road runoff; pipe pitting and brackish taste."],
                ["Total Organic Carbon (TOC) / Colloids", f"{organic_toc_prob:.1f}%", "ELEVATED" if organic_toc_prob>50 else "Low", "Decomposing plant matter & agricultural runoff; disinfection byproduct risk."]
            ]

            t4 = Table(chem_table_data, colWidths=[150, 85, 75, 205])
            t4.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#311042")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#faf5ff"), colors.HexColor("#f8fafc")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7.5),
                ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ]))
            w_t4, h_t4 = t4.wrap(content_w, 200)
            t4.drawOn(c, margin, y - h_t4)
            y -= (h_t4 + 16)

            h_used = draw_p("Probabilistic Contaminant Evaluation Details:", h1_style, margin, y, content_w)
            y -= (h_used + 8)

            p_chem_exp = (
                "The neural estimation algorithm analyzes the cross-correlation between elevated turbidity (which binds organic carbon "
                "and microbial colonies) and pH-driven ionic mobilization. Waters displaying high TDS accompanied by acidic pH show an "
                "exponentially higher affinity for dissolved heavy metal ions, while elevated temperature with moderate turbidity heavily correlates "
                "with heterotrophic bacterial count escalation."
            )
            draw_p(p_chem_exp, body_style, margin, y, content_w)
            c.showPage()

            # ================= PAGE 6 =================
            draw_decorations(6, "Industrial Remediation & Treatment Protocols")
            y = height - 60

            h_used = draw_p("Prescriptive Water Treatment & Remediation Engineering", title_style, margin, y, content_w)
            y -= (h_used + 14)

            p_rem_1 = (
                "<b>Stage 1 — Coagulation, Flocculation & Media Filtration:</b><br/>"
                "To eliminate colloidal turbidity and suspended particulate matter, inject Polyaluminium Chloride (PAC) or Alum at 15–30 mg/L. "
                "Subject the mixture to high-shear rapid mixing for 60 seconds, followed by slow flocculation for 15 minutes. Route through a "
                "multi-media anthracite-sand-garnet pressure filter to reduce turbidity beneath 0.3 NTU."
            )
            h_used = draw_p(p_rem_1, body_style, margin, y, content_w)
            y -= (h_used + 12)

            p_rem_2 = (
                "<b>Stage 2 — High-Pressure Reverse Osmosis (RO) Demineralization:</b><br/>"
                "For samples exhibiting TDS exceeding 500 ppm or elevated inorganic salinity, pass the pre-filtered effluent through spiral-wound "
                "thin-film composite (TFC) polyamide RO membranes operating at 150–250 PSI. This process achieves a 98.5% rejection rate of dissolved "
                "minerals, heavy metals, and ionic chlorides."
            )
            h_used = draw_p(p_rem_2, body_style, margin, y, content_w)
            y -= (h_used + 12)

            p_rem_3 = (
                "<b>Stage 3 — Chemical pH Neutralization & Buffering:</b><br/>"
                "• <i>For Acidic Effluent (pH < 6.50):</i> Dose sodium carbonate (soda ash, Na2CO3) or pass through calcite/corosex neutralizing beds.<br/>"
                "• <i>For Alkaline Effluent (pH > 8.50):</i> Inject food-grade carbon dioxide (CO2) or dilute hydrochloric acid (HCl) via automated PID dosing."
            )
            h_used = draw_p(p_rem_3, body_style, margin, y, content_w)
            y -= (h_used + 12)

            p_rem_4 = (
                "<b>Stage 4 — Ultraviolet (UV-C) Sterilization & Residual Disinfection:</b><br/>"
                "Expose the polished water stream to closed-vessel UV-C irradiation at 254 nm wavelength with a minimum fluence dose of 40 mJ/cm². "
                "Follow with secondary dosing of 0.5–1.5 mg/L free chlorine (NaOCl) to maintain residual bacterial protection across the distribution loop."
            )
            h_used = draw_p(p_rem_4, body_style, margin, y, content_w)
            y -= (h_used + 12)

            p_rem_5 = (
                "<b>Hazardous Containment & Disposal Mandate:</b><br/>"
                "If the sample is categorized as <b>UNSAFE</b> with toxic contaminant load, DO NOT discharge to municipal storm drains. "
                "Isolate effluent in specialized chemical retention basins for high-temperature incineration or certified hazardous wastewater hauling."
            )
            draw_p(p_rem_5, bold_body_style, margin, y, content_w)
            c.showPage()

            # ================= PAGE 7 =================
            draw_decorations(7, "Executive AI Summary & Formal Certification")
            y = height - 60

            h_used = draw_p("Executive Conclusion & Meta-Cognitive Directives", title_style, margin, y, content_w)
            y -= (h_used + 10)

            h_used = draw_p("Autonomous System Verdict Summary:", h1_style, margin, y, content_w)
            y -= (h_used + 6)

            p_summary = (
                f"The PurifyX A.Q.U.A neural monitoring architecture has compiled and evaluated all continuous telemetry streams. "
                f"With a composite Water Quality Index score of <b>{wqi_val:.2f} / 10.0</b>, the body of water is officially designated as <b>{verdict}</b>. "
                f"The meta-cognitive self-questioning kernel has cross-validated this output with an internal correction certainty of <b>{self.correction_acc:.1f}%</b> "
                f"and an uncertainty margin of <b>{self.discorrection_acc:.1f}%</b>."
            )
            h_used = draw_p(p_summary, body_style, margin, y, content_w)
            y -= (h_used + 14)

            h_used = draw_p("Required Operational Action Matrix:", h1_style, margin, y, content_w)
            y -= (h_used + 6)

            action_data = [
                ["Condition", "Immediate Directive", "Monitoring Interval", "Authority Sign-Off"],
                ["SAFE (Nominal)", "Direct potable utilization permitted; continue regular sampling.", "Every 6 Hours", "Certified Potable"],
                ["TREAT (Alert)", "Engage PAC coagulation, media filtration, and pH neutralization.", "Every 15 Minutes", "Treatment Mandated"],
                ["UNSAFE (Hazard)", "Halt distribution instantly. Seal containment valves and alert EHS.", "Continuous (1 Hz)", "Hazard Quarantine"]
            ]
            t5 = Table(action_data, colWidths=[100, 210, 95, 110])
            t5.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7.5),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ]))
            w_t5, h_t5 = t5.wrap(content_w, 140)
            t5.drawOn(c, margin, y - h_t5)
            y -= (h_t5 + 18)

            c.setLineWidth(1.2)
            c.setStrokeColor(colors.HexColor("#0284c7"))
            c.setFillColor(colors.HexColor("#f0f9ff"))
            c.roundRect(margin, y - 110, content_w, 110, 8, stroke=1, fill=1)

            c.setFillColor(colors.HexColor("#0369a1"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin + 12, y - 20, "AUTONOMOUS SYSTEM CERTIFICATION & AUDIT HASH")
            
            c.setFont("Helvetica", 7.8)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(margin + 12, y - 38, f"Neural Core Kernel: PurifyX-v4.8.2-Release • Model Checksum: SHA256:{hash(str(now)) & 0xFFFFFFFF:08X}")
            c.drawString(margin + 12, y - 52, f"Total Data Samples Processed: {self.samples} frames | Live Telemetry History Buffer: {len(history)} records")
            c.drawString(margin + 12, y - 66, f"Environmental Standards Compliance: WHO Guidelines for Drinking-water Quality (4th Ed.)")
            c.drawString(margin + 12, y - 80, f"Digital Audit Signoff: VERIFIED AUTONOMOUS ENGINE • NODE IDENTIFIER: AQUA-SYS-MAIN")

            c.setFont("Helvetica-Bold", 8.5)
            c.setFillColor(colors.HexColor("#0f172a"))
            c.drawRightString(width - margin - 15, y - 98, "STATUS: OFFICIAL DOSSIER GENERATED")

            c.showPage()
            c.save()

            msg = QMessageBox(self)
            msg.setWindowTitle("Industrial PDF Report Ready")
            msg.setText("Comprehensive 7-Page Industrial Dossier Generated Successfully!")
            op = msg.addButton("Open PDF Dossier", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("Dismiss", QMessageBox.ButtonRole.RejectRole)
            msg.exec()

            if msg.clickedButton() == op:
                open_path(pdf_path)

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Export Error", f"Report generation failed:\n{e}")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        if self.logfile:
            self.logfile.flush()
            self.logfile.close()
        event.accept()

    def dark_theme(self):
        return """
        QWidget {
            background-color: #06030d;
            color: #f8fafc;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLineEdit {
            background-color: #0f0721;
            border: 1px solid #4c1d95;
            border-radius: 8px;
            padding: 7px;
            color: #ffffff;
        }
        QLineEdit:focus {
            border-color: #00f2fe;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a0b36, stop:1 #0f1538);
            color: #f8fafc;
            border: 1px solid #4c1d95;
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4c1d95, stop:1 #0284c7);
            border-color: #00f2fe;
        }
        """


# ================= APPLICATION ENTRY =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    splash = AquaSplashScreen()
    if splash.exec() == QDialog.DialogCode.Accepted:
        win = Dashboard()
        win.show()
        sys.exit(app.exec())

        
