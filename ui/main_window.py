import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import webbrowser
import urllib.parse

from core.api_client import APIClient
from core.prompt_builder import PromptBuilder
from core.validator import GherkinValidator
from core.exporter import Exporter
from ui.widgets import CollapsiblePane
from core.logger import logger
from core.config import Config
from core.rag_client import RAGClient

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title(Config.APP_NAME)
        self.geometry("1100x800")
        
        # iOS Style Colors
        self.bg_color = "#F2F2F7"
        self.panel_color = "#FFFFFF"
        self.accent_color = "#007AFF"
        self.text_color = "#000000"
        self.font_main = ("Segoe UI", 11)
        self.font_code = ("Consolas", 11)
        
        self.configure(bg=self.bg_color)
        
        self.api_client = APIClient()
        self.rag_client = RAGClient()
        
        self.debounce_timer = None
        self.is_converting = False
        
        # State Management
        self.requirements_list = [] # [{"input": "...", "output": "...", "raw_output": "", "flagged": False, "reviewed": False, "issues": []}]
        self.current_req_idx = None
        self.active_collection = tk.StringVar()
        
        self.setup_styles()
        self.setup_ui()
        
        # Initialize with one empty requirement
        self.add_new_requirement()
        
    def setup_styles(self):
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        style.configure("TFrame", background=self.bg_color)
        style.configure("Panel.TFrame", background=self.panel_color)
        
        style.configure("TLabel", background=self.bg_color, font=self.font_main)
        style.configure("Panel.TLabel", background=self.panel_color, font=self.font_main)
        
        style.configure("TLabelframe", background=self.bg_color, font=self.font_main, borderwidth=0)
        style.configure("TLabelframe.Label", background=self.bg_color, font=("Segoe UI", 11, "bold"), foreground="#8E8E93")
        
        style.configure("TButton", 
                        background=self.panel_color, 
                        foreground=self.accent_color,
                        font=("Segoe UI", 11, "bold"),
                        borderwidth=0,
                        focuscolor=self.panel_color,
                        padding=5)
        style.map("TButton",
                  background=[("active", "#E5E5EA")],
                  foreground=[("active", self.accent_color), ("disabled", "#C7C7CC")])
                  
        style.configure("Convert.TButton", 
                        background=self.accent_color, 
                        foreground="#FFFFFF",
                        font=("Segoe UI", 11, "bold"),
                        borderwidth=0,
                        padding=8)
        style.map("Convert.TButton",
                  background=[("active", "#0056b3"), ("disabled", "#A1C9F2")],
                  foreground=[("disabled", "#FFFFFF")])

    def setup_ui(self):
        # Main layout padding
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill="both", expand=True)
        
        # Create Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Tab 1: Editor
        self.editor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_tab, text="Editor")
        self.setup_editor_tab(self.editor_tab)
        
        # Tab 2: RAG Context
        self.rag_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.rag_tab, text="RAG Context")
        self.setup_rag_tab(self.rag_tab)
        
        # Tab 3: Settings
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        self.setup_settings_tab(self.settings_tab)
        
        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, background="#E5E5EA", padding="2")
        self.status_bar.pack(side="bottom", fill="x")

    def setup_editor_tab(self, parent_frame):
        # --- Top Controls ---
        top_frame = ttk.Frame(parent_frame)
        top_frame.pack(fill="x", pady=(0, 15))
        
        title_lbl = ttk.Label(top_frame, text="Requirements Editor", font=("Segoe UI", 18, "bold"))
        title_lbl.pack(side="left")
        
        ttk.Button(top_frame, text="Clear All", command=self.clear_all).pack(side="right", padx=(5, 0))
        ttk.Button(top_frame, text="Mail Req. Engineer", command=self.mail_req_engineer).pack(side="right", padx=(5, 0))
        ttk.Button(top_frame, text="Import CSV", command=self.import_csv).pack(side="right", padx=(5, 0))
        ttk.Button(top_frame, text="+ Add New", command=self.add_new_requirement).pack(side="right", padx=(5, 0))
        
        # --- Split View ---
        paned_window = ttk.PanedWindow(parent_frame, orient="horizontal")
        paned_window.pack(fill="both", expand=True, pady=(0, 10))
        
        # Left side: List
        list_frame = ttk.Frame(paned_window, width=250)
        paned_window.add(list_frame, weight=0)
        
        list_lbl = ttk.Label(list_frame, text="Requirements", font=("Segoe UI", 11, "bold"), foreground="#8E8E93")
        list_lbl.pack(anchor="w", pady=(0, 5))
        
        self.req_listbox = tk.Listbox(list_frame, font=self.font_main, bg=self.panel_color, fg=self.text_color,
                                      selectbackground=self.accent_color, selectforeground="#FFFFFF",
                                      relief="flat", borderwidth=0, highlightthickness=1, highlightbackground="#E5E5EA")
        self.req_listbox.pack(fill="both", expand=True)
        self.req_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        # Right side: Detail View
        detail_frame = ttk.Frame(paned_window)
        paned_window.add(detail_frame, weight=1)
        
        # Detail Top controls
        detail_top = ttk.Frame(detail_frame)
        detail_top.pack(fill="x", pady=(0, 5))
        
        self.live_preview_var = tk.BooleanVar(value=Config.DEFAULT_PREVIEW_MODE)
        ttk.Checkbutton(detail_top, text="Live Preview Mode", variable=self.live_preview_var).pack(side="left")
        
        self.btn_convert = ttk.Button(detail_top, text="Convert Selected", command=self.manual_convert, style="Convert.TButton")
        self.btn_convert.pack(side="right")
        self.btn_review = ttk.Button(detail_top, text="Review Requirement", command=self.review_requirement)
        self.btn_review.pack(side="right", padx=(0, 5))
        
        # Detail Paned Window (Input/Output)
        detail_paned = ttk.PanedWindow(detail_frame, orient="vertical")
        detail_paned.pack(fill="both", expand=True)
        
        # Input
        input_frame = ttk.Labelframe(detail_paned, text="EARS Requirement Input", padding="5")
        self.txt_input = tk.Text(input_frame, wrap="word", font=self.font_main, bg=self.panel_color, 
                                 relief="flat", highlightthickness=1, highlightbackground="#E5E5EA", height=5)
        self.txt_input.pack(fill="both", expand=True)
        self.txt_input.bind("<KeyRelease>", self.on_input_change)
        detail_paned.add(input_frame, weight=1)
        
        # Output
        output_frame = ttk.Labelframe(detail_paned, text="Gherkin Output", padding="5")
        self.txt_output = tk.Text(output_frame, wrap="word", font=self.font_code, bg=self.panel_color,
                                  relief="flat", highlightthickness=1, highlightbackground="#E5E5EA")
        self.txt_output.pack(fill="both", expand=True)
        
        output_controls = ttk.Frame(output_frame, style="Panel.TFrame")
        output_controls.pack(fill="x", pady=(5, 0))
        ttk.Button(output_controls, text="Copy Output", command=self.copy_output).pack(side="left", padx=(0, 5))
        ttk.Button(output_controls, text="Export .feature", command=self.export_file).pack(side="left")
        ttk.Button(output_controls, text="View Raw AI Log", command=self.view_raw_log).pack(side="right")
        
        detail_paned.add(output_frame, weight=2)
        
    def setup_rag_tab(self, parent_frame):
        content = ttk.Frame(parent_frame, padding="20")
        content.pack(fill="both", expand=True)
        
        ttk.Label(content, text="Qdrant RAG Context Manager", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
        
        if not self.rag_client.connected:
            ttk.Label(content, text="Disconnected from Qdrant. Check URL/API Key in config.", foreground="red").pack(anchor="w")
            return
            
        # Collection Selection
        sel_frame = ttk.Frame(content)
        sel_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(sel_frame, text="Active Collection:").pack(side="left", padx=(0, 10))
        
        self.combo_collections = ttk.Combobox(sel_frame, textvariable=self.active_collection, state="readonly", width=30)
        self.combo_collections.pack(side="left")
        
        ttk.Button(sel_frame, text="Refresh", command=self.refresh_collections).pack(side="left", padx=5)
        
        # Add to Collection
        add_frame = ttk.Labelframe(content, text="Add New Context Document", padding="10")
        add_frame.pack(fill="both", expand=True)
        
        ttk.Label(add_frame, text="Collection Name (creates if not exists):").pack(anchor="w")
        self.txt_col_name = ttk.Entry(add_frame, width=30)
        self.txt_col_name.pack(anchor="w", pady=(0, 10))
        
        ttk.Label(add_frame, text="Document Content:").pack(anchor="w")
        self.txt_rag_doc = tk.Text(add_frame, wrap="word", font=self.font_main, bg=self.panel_color, 
                                 relief="flat", highlightthickness=1, highlightbackground="#E5E5EA", height=10)
        self.txt_rag_doc.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Button(add_frame, text="Upload to Qdrant", command=self.upload_rag_doc, style="Convert.TButton").pack(anchor="e")
        
        self.refresh_collections()

    def setup_settings_tab(self, parent_frame):
        content = ttk.Frame(parent_frame, padding="20")
        content.pack(fill="both", expand=True)
        
        ttk.Label(content, text="Session Settings", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
        ttk.Label(content, text="These settings apply only to the current session. Edit .env for permanent changes.", foreground="#8E8E93").pack(anchor="w", pady=(0, 15))
        
        row1 = ttk.Frame(content)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="API Call Max Retries:", width=20).pack(side="left")
        self.var_retries = tk.StringVar(value=str(Config.MAX_RETRIES))
        ttk.Entry(row1, textvariable=self.var_retries, width=10).pack(side="left")
        
        ttk.Button(content, text="Apply Settings", command=self.apply_settings, style="Convert.TButton").pack(anchor="w", pady=20)
        
    def refresh_collections(self):
        if self.rag_client.connected:
            cols = self.rag_client.get_collections()
            self.combo_collections['values'] = cols
            if cols and not self.active_collection.get():
                self.active_collection.set(cols[0])
                
    def upload_rag_doc(self):
        col_name = self.txt_col_name.get().strip()
        doc_text = self.txt_rag_doc.get("1.0", "end-1c").strip()
        
        if not col_name or not doc_text:
            messagebox.showwarning("Validation Error", "Please provide both Collection Name and Document Content.")
            return
            
        success = self.rag_client.add_document(col_name, doc_text)
        if success:
            self.status_var.set(f"Successfully uploaded document to '{col_name}'.")
            self.txt_rag_doc.delete("1.0", "end")
            self.refresh_collections()
            self.active_collection.set(col_name)
        else:
            messagebox.showerror("Upload Error", "Failed to upload document to Qdrant.")
            
    def apply_settings(self):
        try:
            val = int(self.var_retries.get())
            if val < 0:
                raise ValueError
            Config.MAX_RETRIES = val
            self.status_var.set(f"Max retries set to {val} for this session.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Max retries must be a positive integer.")

    def _refresh_listbox(self):
        self.req_listbox.delete(0, tk.END)
        for i, req in enumerate(self.requirements_list):
            snippet = req["input"].strip()
            
            prefix = ""
            if req.get("flagged"):
                prefix = "[!] "
            elif req.get("reviewed"):
                prefix = "[✓] "
                
            if not snippet:
                snippet = f"{prefix}Requirement {i+1} (Empty)"
            else:
                snippet = f"{prefix}Req {i+1}: " + (snippet[:25] + "..." if len(snippet) > 25 else snippet)
            self.req_listbox.insert(tk.END, snippet)
            
        if self.current_req_idx is not None and self.current_req_idx < len(self.requirements_list):
            self.req_listbox.selection_set(self.current_req_idx)

    def add_new_requirement(self, text=""):
        self.requirements_list.append({"input": text, "output": "", "raw_output": "", "flagged": False, "reviewed": False, "issues": []})
        self.current_req_idx = len(self.requirements_list) - 1
        self._refresh_listbox()
        self._load_current_requirement()
        
    def _save_current_input(self):
        if self.current_req_idx is not None and self.current_req_idx < len(self.requirements_list):
            self.requirements_list[self.current_req_idx]["input"] = self.txt_input.get("1.0", "end-1c")
            
    def _load_current_requirement(self):
        if self.current_req_idx is None or self.current_req_idx >= len(self.requirements_list):
            self.txt_input.delete("1.0", "end")
            self.txt_output.delete("1.0", "end")
            return
            
        req = self.requirements_list[self.current_req_idx]
        self.txt_input.delete("1.0", "end")
        self.txt_input.insert("1.0", req["input"])
        
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", req["output"])
        
        # Validate existing output if any
        if req["output"].strip():
            is_valid, errors = GherkinValidator.validate(req["output"])
            if is_valid:
                self.txt_output.config(bg=self.panel_color)
            else:
                self.txt_output.config(bg="#ffeeee")
        else:
            self.txt_output.config(bg=self.panel_color)

    def on_listbox_select(self, event):
        selection = self.req_listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        if idx == self.current_req_idx:
            return
            
        self._save_current_input()
        
        # Update listbox text in case snippet changed
        if self.current_req_idx is not None:
            text = self.requirements_list[self.current_req_idx]["input"].strip()
            req = self.requirements_list[self.current_req_idx]
            
            prefix = ""
            if req.get("flagged"):
                prefix = "[!] "
            elif req.get("reviewed"):
                prefix = "[✓] "
                
            if not text:
                snippet = f"{prefix}Requirement {self.current_req_idx+1} (Empty)"
            else:
                snippet = f"{prefix}Req {self.current_req_idx+1}: " + (text[:25] + "..." if len(text) > 25 else text)
            self.req_listbox.delete(self.current_req_idx)
            self.req_listbox.insert(self.current_req_idx, snippet)
            # Re-select the new current item
            self.req_listbox.selection_clear(0, tk.END)
            self.req_listbox.selection_set(idx)

        self.current_req_idx = idx
        self._load_current_requirement()

    def on_input_change(self, event):
        self._save_current_input()
        
        if not self.live_preview_var.get():
            return
            
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)
            
        # Debounce for 800ms
        self.debounce_timer = self.after(800, self.do_convert)
        
    def manual_convert(self):
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)
        self.do_convert()
        
    def do_convert(self):
        if self.current_req_idx is None:
            self.status_var.set("No requirement selected.")
            return
            
        self._save_current_input()
        input_text = self.requirements_list[self.current_req_idx]["input"].strip()
        
        if not input_text:
            self.status_var.set("Input is empty.")
            return
            
        if self.is_converting:
            return
            
        self.is_converting = True
        self.btn_convert.config(state="disabled")
        self.status_var.set("Converting...")
        
        # Fetch RAG context if collection is active
        context_text = ""
        col_name = self.active_collection.get()
        if col_name and self.rag_client.connected:
            docs = self.rag_client.query(col_name, input_text)
            if docs:
                context_text = "\n\n".join(docs)
        
        prompt = PromptBuilder.build_prompt(input_text, context_text)
        
        # Run conversion in a background thread to avoid freezing UI
        threading.Thread(target=self._convert_thread, args=(prompt, self.current_req_idx), daemon=True).start()
        
    def _convert_thread(self, prompt, req_idx):
        result, latency = self.api_client.generate_gherkin(prompt)
        
        # Update UI in main thread
        self.after(0, lambda: self._conversion_done(result, latency, req_idx))
        
    def _conversion_done(self, result, latency, req_idx):
        self.is_converting = False
        self.btn_convert.config(state="normal")
        
        # Save to state
        if req_idx < len(self.requirements_list):
            self.requirements_list[req_idx]["output"] = result
            self.requirements_list[req_idx]["raw_output"] = result
            
        # Only update UI if we are still viewing this requirement
        if req_idx == self.current_req_idx:
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", result)
            
            # Validate
            is_valid, errors = GherkinValidator.validate(result)
            
            if is_valid:
                self.status_var.set(f"Conversion successful in {latency:.2f}s.")
                self.txt_output.config(bg=self.panel_color)
            else:
                err_str = " | ".join(errors)
                self.status_var.set(f"Validation Error: {err_str} (Latency: {latency:.2f}s)")
                self.txt_output.config(bg="#ffeeee") # Light red
                
        else:
            self.status_var.set(f"Background conversion for Req {req_idx+1} finished in {latency:.2f}s.")

    def review_requirement(self):
        if self.current_req_idx is None:
            self.status_var.set("No requirement selected.")
            return
            
        self._save_current_input()
        input_text = self.requirements_list[self.current_req_idx]["input"].strip()
        
        if not input_text:
            self.status_var.set("Input is empty.")
            return
            
        if self.is_converting:
            return
            
        self.is_converting = True
        self.btn_review.config(state="disabled")
        self.btn_convert.config(state="disabled")
        self.status_var.set("Reviewing requirement...")
        
        threading.Thread(target=self._review_thread, args=(input_text, self.current_req_idx), daemon=True).start()
        
    def _review_thread(self, input_text, req_idx):
        data, raw_result, latency = self.api_client.validate_requirement_with_llm(input_text)
        self.after(0, lambda: self._review_done(data, raw_result, latency, req_idx))
        
    def _review_done(self, data, raw_result, latency, req_idx):
        self.is_converting = False
        self.btn_review.config(state="normal")
        self.btn_convert.config(state="normal")
        
        if req_idx < len(self.requirements_list):
            self.requirements_list[req_idx]["raw_output"] = raw_result
            
        if req_idx == self.current_req_idx:
            self.status_var.set(f"Review finished in {latency:.2f}s.")
            if not data.get("is_valid", False):
                issues = "\n".join([f"- {issue}" for issue in data.get("issues", [])])
                msg = f"Issues found with the requirement:\n\n{issues}\n\nWould you like to email the System Engineer about this?"
                
                # Custom dialog to handle options
                dialog = tk.Toplevel(self)
                dialog.title("Requirement Issues Found")
                dialog.geometry("500x300")
                dialog.configure(bg=self.bg_color)
                dialog.transient(self)
                dialog.grab_set()
                
                ttk.Label(dialog, text=msg, wraplength=460, font=self.font_main, background=self.bg_color).pack(pady=20, padx=20, fill="both", expand=True)
                
                btn_frame = ttk.Frame(dialog)
                btn_frame.pack(fill="x", pady=10, padx=10)
                
                def add_to_flagged():
                    self.requirements_list[req_idx]["flagged"] = True
                    self.requirements_list[req_idx]["issues"] = data.get("issues", [])
                    self._refresh_listbox()
                    dialog.destroy()
                    self.status_var.set("Requirement added to flagged list.")
                    
                ttk.Button(btn_frame, text="Add to Flagged List", command=add_to_flagged).pack(side="left", padx=5)
                ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)
                
            else:
                self.requirements_list[req_idx]["reviewed"] = True
                self.requirements_list[req_idx]["flagged"] = False
                self._refresh_listbox()
                messagebox.showinfo("Review Passed", "The requirement is in proper EARS format and is testable!")
                
    def view_raw_log(self):
        if self.current_req_idx is None:
            return
        
        raw = self.requirements_list[self.current_req_idx].get("raw_output", "")
        if not raw:
            messagebox.showinfo("Raw AI Log", "No raw log available for this requirement yet. Run Convert or Review first.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Raw AI Output Log")
        dialog.geometry("700x500")
        
        txt = tk.Text(dialog, wrap="word", font=self.font_code)
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", raw)
        txt.config(state="disabled")

    def mail_req_engineer(self):
        flagged_reqs = [r for r in self.requirements_list if r.get("flagged")]
        if not flagged_reqs:
            messagebox.showinfo("Mail Req. Engineer", "There are no flagged requirements to email.")
            return
            
        subject = "Review Required for EARS Requirements"
        body = "Hello,\n\nThe following requirements have been flagged for review due to format or testability issues:\n\n"
        
        for i, req in enumerate(flagged_reqs):
            body += f"--- Requirement {i+1} ---\n"
            body += f"Text: \"{req['input']}\"\n"
            issues_text = "\n".join([f"- {issue}" for issue in req.get('issues', [])])
            body += f"Issues:\n{issues_text}\n\n"
            
        body += "Please advise.\n"
        
        subject_enc = urllib.parse.quote(subject)
        body_enc = urllib.parse.quote(body)
        webbrowser.open(f"mailto:?subject={subject_enc}&body={body_enc}")

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all requirements?"):
            self.requirements_list = []
            self.add_new_requirement()
            self.status_var.set("Cleared all requirements.")
        
    def copy_output(self):
        content = self.txt_output.get("1.0", "end-1c")
        if content.strip():
            Exporter.copy_to_clipboard(self, content)
            self.status_var.set("Copied to clipboard.")
            
    def export_file(self):
        content = self.txt_output.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showwarning("Export", "Nothing to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".feature",
            filetypes=[("Gherkin Feature Files", "*.feature"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Gherkin Output"
        )
        
        if filepath:
            success = Exporter.write_file(filepath, content)
            if success:
                self.status_var.set(f"Successfully exported to {filepath}")
            else:
                messagebox.showerror("Export Error", "Failed to save file.")

    def import_csv(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Import CSV Requirements"
        )
        if not filepath:
            return
            
        try:
            import csv
            requirements = []
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                # Read header or first row to guess column
                sample = f.read(1024)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    has_header = csv.Sniffer().has_header(sample)
                except csv.Error:
                    dialect = csv.excel
                    has_header = False
                    
                reader = csv.reader(f, dialect)
                
                if has_header:
                    header = next(reader)
                    req_idx = 0
                    for i, col in enumerate(header):
                        col_lower = col.lower().strip()
                        if 'requirement' in col_lower or 'content' in col_lower or 'req' in col_lower or 'ears' in col_lower:
                            req_idx = i
                            break
                    for row in reader:
                        if row and len(row) > req_idx:
                            req = row[req_idx].strip()
                            if req:
                                requirements.append(req)
                else:
                    for row in reader:
                        if row:
                            req = row[0].strip()
                            if req:
                                requirements.append(req)
                                
            if requirements:
                # Replace current if there's only one empty requirement, else append
                if len(self.requirements_list) == 1 and not self.requirements_list[0]["input"].strip():
                    self.requirements_list = [{"input": req, "output": "", "raw_output": "", "flagged": False, "reviewed": False, "issues": []} for req in requirements]
                else:
                    self.requirements_list.extend([{"input": req, "output": "", "raw_output": "", "flagged": False, "reviewed": False, "issues": []} for req in requirements])
                
                self.current_req_idx = 0
                self._refresh_listbox()
                self._load_current_requirement()
                self.status_var.set(f"Imported {len(requirements)} requirements from CSV.")
            else:
                messagebox.showinfo("Import CSV", "No requirements found in the CSV file.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import CSV:\n{str(e)}")
