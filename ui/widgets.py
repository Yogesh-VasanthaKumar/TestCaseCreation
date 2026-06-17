import tkinter as tk
from tkinter import ttk

class CollapsiblePane(ttk.Frame):
    """
    A collapsible frame.
    """
    def __init__(self, parent, title="Collapsible", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.show = tk.BooleanVar(value=False)
        self.title = title
        
        self.toggle_button = ttk.Checkbutton(
            self, text=self.title, command=self.toggle,
            variable=self.show, style='Toolbutton'
        )
        self.toggle_button.pack(fill="x", expand=False)
        
        self.container = ttk.Frame(self)
        
    def toggle(self):
        if self.show.get():
            self.container.pack(fill="both", expand=True, pady=5)
        else:
            self.container.pack_forget()
