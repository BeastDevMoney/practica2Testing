import tkinter as tk
from tkinter import ttk
from client.app.app_controller import AppController
from client.domain.incidence_dto import IncidenceDTO

# Usamos tkinter para producir una interfaz de forma sencilla para visualizar los datos
class MainWindow(tk.Tk):
    def __init__(self, controller: AppController, csv_path: str):
        super().__init__()
        self.controller = controller
        self.title(f"Rail Incidences - {controller.user_id}")
        self.geometry("900x500")

        self.listbox = tk.Listbox(self, width=50)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X)

        ttk.Button(btns, text="Subscribe", command=self._subscribe).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Unsubscribe", command=self._unsubscribe).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Refresh", command=self._refresh).pack(side=tk.LEFT, padx=4)

        self.detail = tk.Text(right, height=30)
        self.detail.pack(fill=tk.BOTH, expand=True, pady=8)

        self._data: list[IncidenceDTO] = []

        boot = self.controller.bootstrap(csv_path)
        print("BOOTSTRAP:", boot.status, boot.json)

        self._refresh()

    def _subscribe(self):
        self.controller.subscribe()

    def _unsubscribe(self):
        self.controller.unsubscribe()

    def _refresh(self):
        self._data = self.controller.refresh()
        self.listbox.delete(0, tk.END)
        for inc in self._data:
            self.listbox.insert(tk.END, f"{inc.start} | {inc.tipoIncidencia}")

        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, f"Loaded: {len(self._data)} incidences\n")

    def _on_select(self, _evt):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        inc = self._data[idx]
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END,
            f"ID: {inc.incidenceID}\n"
            f"Type: {inc.tipoIncidencia}\n"
            f"Start: {inc.start}\n"
            f"End: {inc.end}\n"
            f"Details:\n{inc.details}\n"
        )
