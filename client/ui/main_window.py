import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk

from client.app.app_controller import AppController
from client.domain.incidence_dto import IncidenceDTO
from server.persistence.in_memory_measurement_repository import InMemoryMeasurementRepository

BG = "#0f1117"
SURFACE = "#1a1d27"
SURFACE2 = "#22263a"
BORDER = "#2e3248"
ACCENT = "#4f8ef7"
ACCENT2= "#7c5cfc"
TEXT = "#e8eaf6"
TEXT_DIM = "#7b82a8"
RED = "#f05c6e"
AMBER = "#f5a623"

TYPE_META = {
    "ABSENCE": (RED, "⚠"),
    "FREQUENCY_JUMP": (AMBER, "⚡"),
}

def _type_meta(tipo: str):
    return TYPE_META.get(tipo, (ACCENT, "●"))


class MainWindow(tk.Tk):
    def __init__(self, controller: AppController, m_repo: InMemoryMeasurementRepository, csv_path: str):
        super().__init__()
        self.controller = controller
        self.m_repo = m_repo
        self.csv_path = csv_path
        self._data: list[IncidenceDTO] = []

        self.title("Rail Voltage Monitor")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_styles()
        self._build_ui()

        boot = self.controller.bootstrap(csv_path)
        print("BOOTSTRAP:", boot.status, boot.json)
        self._refresh()

    # ── Estilos ttk ───────────────────────────────────────────────────────────

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, font=("Helvetica", 10), borderwidth=0, relief="flat")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=SURFACE2, foreground=TEXT_DIM, padding=[18, 8], font=("Helvetica", 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", SURFACE)], foreground=[("selected", TEXT)])
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("TButton", background=ACCENT, foreground="#ffffff", font=("Helvetica", 9, "bold"), padding=[12, 6])
        s.map("TButton", background=[("active", ACCENT2), ("disabled", SURFACE2)], foreground=[("disabled", TEXT_DIM)])
        s.configure("Ghost.TButton", background=SURFACE2, foreground=TEXT_DIM, font=("Helvetica", 9), padding=[10, 6])
        s.map("Ghost.TButton", background=[("active", BORDER)], foreground=[("active", TEXT)])
        s.configure("TCombobox", fieldbackground=SURFACE2, background=SURFACE2, foreground=TEXT, arrowcolor=TEXT_DIM, borderwidth=0)
        s.map("TCombobox", fieldbackground=[("readonly", SURFACE2)])
        s.configure("TSpinbox", fieldbackground=SURFACE2, background=SURFACE2, foreground=TEXT, arrowcolor=TEXT_DIM, borderwidth=0)
        s.configure("Vertical.TScrollbar", background=SURFACE2, troughcolor=SURFACE, arrowcolor=TEXT_DIM, borderwidth=0, relief="flat")

    # ── Layout principal ──────────────────────────────────────────────────────

    def _build_ui(self):
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡Rail Voltage Monitor", bg=SURFACE, fg=TEXT, font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=20, pady=12)
        self._status_lbl = tk.Label(hdr, text="", bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 9))
        self._status_lbl.pack(side=tk.RIGHT, padx=20)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab_inc = ttk.Frame(notebook)
        tab_pred = ttk.Frame(notebook)
        notebook.add(tab_inc, text="  Incidencias  ")
        notebook.add(tab_pred, text="  Predicción de voltaje  ")

        self._build_incidences_tab(tab_inc)
        self._build_prediction_tab(tab_pred)

    # ── Tab 1: Incidencias ────────────────────────────────────────────────────

    def _build_incidences_tab(self, parent):
        toolbar = tk.Frame(parent, bg=BG, pady=10)
        toolbar.pack(fill=tk.X, padx=16)
        ttk.Button(toolbar, text="Subscribe", command=self._subscribe).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="Unsubscribe", style="Ghost.TButton", command=self._unsubscribe).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="↻ Actualizar", style="Ghost.TButton", command=self._refresh).pack(side=tk.LEFT)
        self._count_lbl = tk.Label(toolbar, text="", bg=BG, fg=TEXT_DIM, font=("Helvetica", 9))
        self._count_lbl.pack(side=tk.RIGHT)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=16)

        body = tk.Frame(parent, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        list_frame = tk.Frame(body, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        list_frame.pack_propagate(False)
        list_frame.configure(width=310)

        tk.Label(list_frame, text="INCIDENCIAS DETECTADAS", bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        tk.Frame(list_frame, bg=BORDER, height=1).pack(fill=tk.X)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scroll.set,
            bg=SURFACE, fg=TEXT,
            selectbackground=ACCENT2, selectforeground="#fff",
            activestyle="none", borderwidth=0, highlightthickness=0,
            font=("Courier", 9), relief="flat",
        )
        scroll.config(command=self.listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        self._detail_frame = tk.Frame(body, bg=BG)
        self._detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._show_empty_detail()

    def _show_empty_detail(self):
        for w in self._detail_frame.winfo_children():
            w.destroy()
        tk.Label(self._detail_frame, text="Selecciona una incidencia\npara ver sus detalles", bg=BG, fg=TEXT_DIM, font=("Helvetica", 11)).pack(expand=True)

    def _show_detail(self, inc: IncidenceDTO):
        for w in self._detail_frame.winfo_children():
            w.destroy()

        color, icon = _type_meta(inc.tipoIncidencia)
        duration = inc.end - inc.start
        total_sec = int(duration.total_seconds())
        if duration.days > 0:
            dur_str = (f"{duration.days}d "
                       f"{total_sec % 86400 // 3600}h "
                       f"{total_sec % 3600 // 60}m")
        elif total_sec >= 3600:
            dur_str = f"{total_sec // 3600}h {total_sec % 3600 // 60}m {total_sec % 60}s"
        else:
            dur_str = f"{total_sec // 60}m {total_sec % 60}s"

        f = self._detail_frame

        hdr = tk.Frame(f, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr, text=f"{icon}  {inc.tipoIncidencia.replace('_', ' ')}", bg=SURFACE, fg=color, font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=16, pady=14)
        tk.Label(hdr, text=f"ID: {inc.incidenceID[:16]}…", bg=SURFACE, fg=TEXT_DIM, font=("Courier", 8)).pack(side=tk.RIGHT, padx=16)

        grid = tk.Frame(f, bg=BG)
        grid.pack(fill=tk.X, pady=(0, 10))
        metrics = [
            ("INICIO", f"{inc.start:%d %b %Y  %H:%M:%S}"),
            ("FIN", f"{inc.end:%d %b %Y  %H:%M:%S}"),
            ("DURACIÓN", dur_str),
            ("TIPO", inc.tipoIncidencia.replace("_", " ")),
        ]
        for col, (label, value) in enumerate(metrics):
            card = tk.Frame(grid, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            card.grid(row=0, column=col, padx=(0, 8) if col < 3 else 0, sticky="nsew")

            grid.columnconfigure(col, weight=1)
            tk.Label(card, text=label, bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 7, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(card, text=value, bg=SURFACE, fg=TEXT, font=("Helvetica", 10, "bold"), wraplength=160, justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        tk.Label(f, text="DETALLES TÉCNICOS", bg=BG, fg=TEXT_DIM, font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(4, 4))
        detail_box = tk.Frame(f, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        detail_box.pack(fill=tk.X, pady=(0, 10))
        tk.Label(detail_box, text=inc.details or "-", bg=SURFACE, fg=TEXT, font=("Courier", 10), justify="left", wraplength=600, anchor="w").pack(padx=14, pady=12, fill=tk.X)

        tk.Label(f, text="ID COMPLETO", bg=BG, fg=TEXT_DIM, font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(4, 4))
        id_box = tk.Frame(f, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        id_box.pack(fill=tk.X)
        tk.Label(id_box, text=inc.incidenceID, bg=SURFACE, fg=TEXT_DIM, font=("Courier", 9)).pack(padx=14, pady=10, anchor="w")

    # ── Tab 2: Predicción ─────────────────────────────────────────────────────

    def _build_prediction_tab(self, parent):
        content = tk.Frame(parent, bg=BG)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        tk.Label(content, text="Configuración de la gráfica", bg=BG, fg=TEXT, font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 16))

        card = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill=tk.X, pady=(0, 16))
        inner = tk.Frame(card, bg=SURFACE)
        inner.pack(padx=20, pady=16, fill=tk.X)

        row1 = tk.Frame(inner, bg=SURFACE)
        row1.pack(fill=tk.X, pady=(0, 12))
        tk.Label(row1, text="Canal de voltaje", bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 9, "bold"), width=18, anchor="w").pack(side=tk.LEFT)
        self._channel_var = tk.StringVar(value="vr1_b")
        ttk.Combobox(row1, textvariable=self._channel_var, values=["vr1_a", "vr1_b", "vr2_a", "vr2_b"], state="readonly", width=12).pack(side=tk.LEFT)

        row2 = tk.Frame(inner, bg=SURFACE)
        row2.pack(fill=tk.X)
        tk.Label(row2, text="Margen (minutos)", bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 9, "bold"), width=18, anchor="w").pack(side=tk.LEFT)
        self._margin_var = tk.IntVar(value=5)
        ttk.Spinbox(row2, from_=2, to=60, textvariable=self._margin_var, width=6).pack(side=tk.LEFT)

        btn_row = tk.Frame(content, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 16))
        self._run_btn = ttk.Button(btn_row, text="▶ Ver gráficas", command=self._launch_plot)
        self._run_btn.pack(side=tk.LEFT)
        self._pred_status = tk.Label(btn_row, text="", bg=BG, fg=TEXT_DIM, font=("Helvetica", 9))
        self._pred_status.pack(side=tk.LEFT, padx=14)

        info_card = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        info_card.pack(fill=tk.X)
        for icon, text in [
            ("📊", "Se generan dos ventanas independientes de matplotlib."),
            ("⚡", "Una centrada en la primera incidencia FREQUENCY_JUMP del test set."),
            ("⚠", "Otra centrada en la primera incidencia ABSENCE del test set."),
            ("🕐", "Eje X con resolución minuto a minuto, ±margen alrededor de la incidencia."),
            ("📉", "Panel inferior: error absoluto (mV) por minuto en barras."),
        ]:
            row = tk.Frame(info_card, bg=SURFACE)
            row.pack(fill=tk.X, padx=16, pady=3)
            tk.Label(row, text=icon, bg=SURFACE, fg=TEXT, font=("Helvetica", 10), width=2).pack(side=tk.LEFT)
            tk.Label(row, text=text, bg=SURFACE, fg=TEXT_DIM, font=("Helvetica", 9), anchor="w").pack(side=tk.LEFT, padx=6)
        tk.Frame(info_card, bg=BG, height=8).pack()

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _subscribe(self):
        self.controller.subscribe()

    def _unsubscribe(self):
        self.controller.unsubscribe()

    def _refresh(self):
        import datetime
        self._data = self.controller.refresh()
        self.listbox.delete(0, tk.END)
        for inc in self._data:
            color, icon = _type_meta(inc.tipoIncidencia)
            self.listbox.insert(
                tk.END,
                f" {icon}  {inc.start:%d/%m  %H:%M}  {inc.tipoIncidencia[:3]}"
            )
            self.listbox.itemconfig(tk.END, fg=color)
        self._count_lbl.config(text=f"{len(self._data)} incidencias")
        self._status_lbl.config(
            text=f"Último refresh: {datetime.datetime.now():%H:%M:%S}")
        self._show_empty_detail()

    def _on_select(self, _evt):
        if not self.listbox.curselection():
            return
        self._show_detail(self._data[self.listbox.curselection()[0]])

    def _launch_plot(self):
        self._run_btn.config(state="disabled")
        self._pred_status.config(text="Generando gráficas…")
        target = self._channel_var.get()
        margin = str(self._margin_var.get())

        def _run():
            try:
                subprocess.run(
                    [sys.executable,
                     os.path.join(os.path.dirname(
                         os.path.abspath(__file__)),
                         "..", "..", "server", "predictor", "voltage_plot.py"),
                     self.csv_path, target, margin],
                    check=False
                )
            finally:
                self.after(0, lambda: self._run_btn.config(state="normal"))
                self.after(0, lambda: self._pred_status.config(text="✓ Listo"))

        threading.Thread(target=_run, daemon=True).start()

    def _on_close(self):
        self.destroy()
        sys.exit(0)