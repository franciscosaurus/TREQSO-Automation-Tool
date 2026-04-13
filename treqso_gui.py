"""
TREQSO Automation GUI
Graphical interface for TREQSO automation tasks — dark mode UI
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import os
import sys
import subprocess
from treqso_processor import TREQSODataProcessor
from dotenv import load_dotenv
import csv
from win32 import win32print

# Load environment variables
load_dotenv()


# ── Colour palette ────────────────────────────────────────────────────────────
BG       = '#16181f'   # root / outermost app background
SURFACE  = '#1e2128'   # tab panels, main frames
CARD     = '#252932'   # raised card surfaces — LabelFrames
INPUT    = '#1a1d24'   # entry / combobox field background
BORDER   = '#2c3040'   # default border
BORDER_A = '#4f9cf9'   # active / focus border (accent colour)
TEXT     = '#dde2ed'   # primary text
TEXT_2   = '#6b7694'   # secondary / muted text
ACCENT   = '#4f9cf9'   # primary blue accent
ACCENT_P = '#1a6fd4'   # accent pressed state
ACCENT_H = '#74b5fb'   # accent hover state
# Table cells
TBL_H    = '#252932'   # header background
TBL_ODD  = '#1e2128'   # odd data row
TBL_EVEN = '#22252d'   # even data row
TBL_BORD = '#2c3040'   # cell border colour
# Console
CON_BG   = '#0d0f14'   # console background
CON_FG   = '#a8b4cc'   # console default text
# ─────────────────────────────────────────────────────────────────────────────


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _apply_dark_theme(root: tk.Tk) -> None:
    """
    Configure a comprehensive dark-mode ttk.Style.
    Called once during __init__ before any widgets are created.
    """
    root.configure(bg=BG)

    style = ttk.Style()
    style.theme_use('clam')   # clam is the most customisable built-in theme

    # ── Frames ────────────────────────────────────────────────────────────────
    style.configure('TFrame',     background=SURFACE, relief='flat')
    style.configure('App.TFrame', background=BG,      relief='flat')

    # ── Labels ────────────────────────────────────────────────────────────────
    style.configure('TLabel',
        background=SURFACE, foreground=TEXT, font=('Segoe UI', 9))
    style.configure('Title.TLabel',
        background=BG, foreground=TEXT, font=('Segoe UI', 15, 'bold'))
    style.configure('Section.TLabel',
        background=SURFACE, foreground=TEXT, font=('Segoe UI', 11, 'bold'))
    # Labels that live inside a CARD-background LabelFrame
    style.configure('Card.TLabel',
        background=CARD, foreground=TEXT, font=('Segoe UI', 9))

    # ── LabelFrame (cards) ────────────────────────────────────────────────────
    style.configure('TLabelframe',
        background=CARD, foreground=TEXT_2,
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        relief='solid', borderwidth=1)
    style.configure('TLabelframe.Label',
        background=CARD, foreground=TEXT_2, font=('Segoe UI', 9))

    # ── Notebook (tabs) ───────────────────────────────────────────────────────
    style.configure('TNotebook',
        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
    style.configure('TNotebook.Tab',
        background=BG, foreground=TEXT_2,
        padding=[16, 8], font=('Segoe UI', 9), borderwidth=0)
    style.map('TNotebook.Tab',
        background=[('selected', SURFACE), ('active', '#1a1d24')],
        foreground=[('selected', TEXT),    ('active', TEXT)],
        expand=[('selected', [0, 0, 0, 0])])

    # ── Buttons ───────────────────────────────────────────────────────────────
    style.configure('TButton',
        background=CARD, foreground=TEXT,
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        relief='flat', focusthickness=0,
        padding=[10, 5], font=('Segoe UI', 9))
    style.map('TButton',
        background=[('active', '#2e3342'), ('pressed', '#1a1d24')],
        foreground=[('active', TEXT),      ('pressed', TEXT)],
        bordercolor=[('active', BORDER_A)])

    # Primary action button — filled accent
    style.configure('Accent.TButton',
        background=ACCENT, foreground='#ffffff',
        bordercolor=ACCENT, lightcolor=ACCENT_H, darkcolor=ACCENT_P,
        relief='flat', focusthickness=0,
        padding=[12, 6], font=('Segoe UI', 9, 'bold'))
    style.map('Accent.TButton',
        background=[('active', ACCENT_H), ('pressed', ACCENT_P)],
        foreground=[('active', '#ffffff'), ('pressed', '#ffffff')],
        bordercolor=[('active', ACCENT_H), ('pressed', ACCENT_P)])

    # ── Entry fields ──────────────────────────────────────────────────────────
    style.configure('TEntry',
        fieldbackground=INPUT, foreground=TEXT,
        insertcolor=TEXT, selectbackground=ACCENT, selectforeground='#ffffff',
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        relief='solid', borderwidth=1,
        padding=[6, 4], font=('Segoe UI', 9))
    style.map('TEntry',
        bordercolor=[('focus', BORDER_A)],
        lightcolor=[('focus', BORDER_A)],
        darkcolor=[('focus', BORDER_A)])

    # ── Combobox ──────────────────────────────────────────────────────────────
    style.configure('TCombobox',
        fieldbackground=INPUT, foreground=TEXT, background=CARD,
        selectbackground=ACCENT, selectforeground='#ffffff',
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        arrowcolor=TEXT_2, relief='solid', borderwidth=1,
        padding=[6, 4], font=('Segoe UI', 9))
    style.map('TCombobox',
        fieldbackground=[('readonly', INPUT)],
        foreground=[('readonly', TEXT)],
        bordercolor=[('focus', BORDER_A)],
        lightcolor=[('focus', BORDER_A)])

    # ── Checkbutton ───────────────────────────────────────────────────────────
    style.configure('TCheckbutton',
        background=SURFACE, foreground=TEXT,
        indicatorcolor=INPUT, indicatorrelief='flat',
        focusthickness=0, font=('Segoe UI', 9))
    style.map('TCheckbutton',
        background=[('active', SURFACE)],
        foreground=[('active', TEXT)],
        indicatorcolor=[('selected', ACCENT), ('active', INPUT)])

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    style.configure('TScrollbar',
        background=CARD, troughcolor=BG,
        bordercolor=BG, arrowcolor=TEXT_2,
        relief='flat', borderwidth=0)
    style.map('TScrollbar',
        background=[('active', BORDER_A), ('pressed', ACCENT)])

    # ── Status bar label ──────────────────────────────────────────────────────
    style.configure('Status.TLabel',
        background='#12141a', foreground=TEXT_2,
        font=('Segoe UI', 8), padding=[8, 3])


class TREQSOGui:
    def __init__(self, root):
        self.root = root
        self.root.title("TREQSO Automation Tool")
        self.root.geometry("1300x940")
        self.root.resizable(True, True)

        # Initialize processor
        self.processor = TREQSODataProcessor()

        # Apply full dark theme before building any widgets
        _apply_dark_theme(root)

        # ── Outer container ───────────────────────────────────────────────────
        main_frame = ttk.Frame(root, style='App.TFrame', padding="12")
        main_frame.grid(row=0, column=0, sticky='nsew')

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=6)
        main_frame.rowconfigure(3, weight=1)

        # ── Title + separator ─────────────────────────────────────────────────
        ttk.Label(main_frame, text="TREQSO Automation Tool",
            style='Title.TLabel'
        ).grid(row=0, column=0, pady=(6, 2), sticky=tk.W)

        tk.Frame(main_frame, bg=BORDER, height=1).grid(
            row=1, column=0, sticky='ew', pady=(0, 8))

        # ── Notebook ──────────────────────────────────────────────────────────
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky='nsew', pady=(0, 8))

        self.create_print_tab()
        self.create_parts_tab()
        self.create_edit_parts_tab()
        self.create_bom_tab()
        self.create_replace_tab()
        self.create_settings_tab()

        # ── Output console ────────────────────────────────────────────────────
        console_frame = ttk.LabelFrame(main_frame, text="Output Console", padding="6")
        console_frame.grid(row=3, column=0, sticky='nsew', pady=(0, 6))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=10, wrap=tk.WORD,
            font=('Consolas', 9),
            bg=CON_BG, fg=CON_FG,
            insertbackground=TEXT,
            selectbackground=ACCENT, selectforeground='#ffffff',
            relief='flat', borderwidth=0
        )
        self.console.grid(row=0, column=0, sticky='nsew')

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame,
            textvariable=self.status_var,
            style='Status.TLabel', anchor=tk.W
        ).grid(row=4, column=0, sticky='ew')

        # First-run: ensure Playwright browsers are installed
        threading.Thread(target=self._ensure_playwright_browsers, daemon=True).start()

    # ── First-run: Playwright browser installation ───────────────────────────

    def _chromium_installed(self) -> bool:
        playwright_dir = os.path.join(
            os.environ.get('LOCALAPPDATA', os.path.expanduser('~')),
            'ms-playwright'
        )
        if not os.path.exists(playwright_dir):
            return False
        return any(
            d.startswith('chromium')
            for d in os.listdir(playwright_dir)
            if os.path.isdir(os.path.join(playwright_dir, d))
        )

    def _ensure_playwright_browsers(self):
        if self._chromium_installed():
            return

        self.log("=== First-Time Setup ===")
        self.log("Playwright browser (Chromium) not found.")
        self.log("Downloading now (~150 MB). This only happens once...")
        self.update_status("Downloading browser — please wait...")

        node_exe       = self.processor._get_node_path()
        app_dir        = self.processor._get_app_dir()
        playwright_cmd = os.path.join(app_dir, 'node_modules', '.bin', 'playwright.cmd')

        if not os.path.exists(playwright_cmd):
            self.log("✗ playwright.cmd not found in node_modules/.bin/")
            self.log("  Ensure node_modules is present in the install directory.")
            self.update_status("Browser setup failed — see console")
            return

        env = os.environ.copy()
        if os.path.isabs(node_exe):
            env['PATH'] = os.path.dirname(node_exe) + os.pathsep + env.get('PATH', '')

        try:
            result = subprocess.run(
                ['cmd', '/c', playwright_cmd, 'install', 'chromium'],
                env=env, capture_output=True, text=True,
                timeout=600, cwd=app_dir
            )
            if result.returncode == 0:
                self.log("✓ Browser installation complete.")
                self.update_status("Ready")
            else:
                self.log(f"✗ Browser installation exited with code {result.returncode}")
                if result.stderr:
                    self.log(f"  {result.stderr.strip()}")
                self.update_status("Browser setup failed — see console")
        except subprocess.TimeoutExpired:
            self.log("✗ Browser download timed out after 10 minutes.")
            self.log("  Check your internet connection and try restarting the application.")
            self.update_status("Browser download timed out")
        except Exception as e:
            self.log(f"✗ Browser installation error: {e}")
            self.update_status("Browser setup failed — see console")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_scrollable_tab(self, parent_notebook) -> tuple[ttk.Frame, ttk.Frame]:
        container = ttk.Frame(parent_notebook, style='TFrame')
        canvas = tk.Canvas(container, bg=SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        content_frame = ttk.Frame(canvas, style='TFrame')
        content_frame.columnconfigure(0, weight=1)

        # Use a BooleanVar to track if scrolling is needed
        scroll_needed = tk.BooleanVar(value=False)

        def _toggle_scrollbar():
            if canvas.bbox("all"):
                content_height = canvas.bbox("all")[3]
                canvas_height = canvas.winfo_height()
                need = content_height > canvas_height
            else:
                need = False

            scroll_needed.set(need)
            if need:
                scrollbar.pack(side="right", fill="y")
            else:
                scrollbar.pack_forget()
                canvas.yview_moveto(0)

        def _update_scroll_region():
            canvas.configure(scrollregion=canvas.bbox("all"))
            _toggle_scrollbar()

        content_frame.bind("<Configure>", lambda e: _update_scroll_region())

        canvas_window = canvas.create_window((16,0), window=content_frame, anchor="nw")

        def _configure_canvas(event):
            padding_total = 32
            canvas.itemconfig(canvas_window, width=event.width - padding_total)
            _toggle_scrollbar()

        canvas.bind("<Configure>", _configure_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)

        # Mouse wheel: scroll only if scroll_needed is True
        def _on_mousewheel(event):
            if scroll_needed.get():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        return container, content_frame

    def _build_csv_table(self, parent, csv_filename: str) -> None:
        """Read a CSV and render it as a dark-mode table inside a LabelFrame."""
        with open(resource_path(csv_filename), 'r', newline='') as fh:
            data = list(csv.reader(fh))

        for i, row in enumerate(data):
            for col, cell in enumerate(row):
                if i == 0:
                    lbl = tk.Label(parent, text=cell,
                        font=('Segoe UI', 9, 'bold'),
                        bg=TBL_H, fg=TEXT,
                        relief=tk.FLAT,
                        highlightbackground=TBL_BORD, highlightthickness=1,
                        padx=10, pady=5)
                else:
                    lbl = tk.Label(parent, text=cell,
                        font=('Segoe UI', 9),
                        bg=TBL_ODD if i % 2 == 1 else TBL_EVEN,
                        fg=TEXT,
                        relief=tk.FLAT,
                        highlightbackground=TBL_BORD, highlightthickness=1,
                        padx=10, pady=3)
                lbl.grid(row=i, column=col, sticky='ew')

        for col in range(len(data[0]) if data else 0):
            parent.columnconfigure(col, weight=1)

    def _build_instructions(self, parent, row: int, text: str) -> None:
        """Render a 'How to prepare your CSV' LabelFrame with step-by-step text."""
        frame = ttk.LabelFrame(parent, text="How to prepare your CSV", padding="12")
        frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=(0, 6))
        ttk.Label(frame, text=text,
            justify=tk.LEFT, wraplength=820, style='Card.TLabel'
        ).grid(row=0, column=0, sticky=tk.W)

    def open_printer_settings(self):
        """Open Windows Printers & Scanners settings page."""
        try:
            os.startfile('ms-settings:printers')
        except Exception:
            try:
                subprocess.run(['control', 'printers'], shell=True)
            except Exception:
                messagebox.showerror("Error", "Could not open printer settings.")

    # ── Tab builders ──────────────────────────────────────────────────────────

    def create_print_tab(self):
        # tab = self._make_tab_frame()
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Print Manufacturing Orders")

        ttk.Label(tab_content,
            text="Print all Manufacturing Orders belonging to a parent MO Reference ID.",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky=tk.W)

        ttk.Label(tab_content, text="Parent MO Reference ID:").grid(row=1, column=0, sticky=tk.E, pady=5)
        self.MO_ref_id = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.MO_ref_id).grid(
            row=1, column=1, sticky='ew', pady=5, padx=6)

        try:
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            default_printer = win32print.GetDefaultPrinter()
        except Exception as e:
            printers = ["No printers found"]
            default_printer = None
            self.log(f"Warning: Could not enumerate printers: {e}")

        self.printer_var = tk.StringVar(value=default_printer or "")
        printer_dropdown = ttk.Combobox(
            tab_content, textvariable=self.printer_var,
            values=printers, state='readonly', width=37)
        ttk.Label(tab_content, text="Select Printer:").grid(row=2, column=0, sticky=tk.E, pady=5)
        printer_dropdown.grid(row=2, column=1, sticky='ew', pady=5, padx=6)

        if default_printer and default_printer in printers:
            printer_dropdown.set(default_printer)
        elif printers and printers[0] != "No printers found":
            printer_dropdown.set(printers[0])

        ttk.Button(tab_content, text="⟳", width=3,
            command=lambda: self.refresh_printers(printer_dropdown)
        ).grid(row=2, column=2, pady=5, padx=(0, 6))

        # Printer setup note
        note = ttk.LabelFrame(tab_content, text="Printer Setup Required", padding="10")
        note.grid(row=3, column=0, columnspan=3, sticky='nsew', pady=(10, 6))
        ttk.Label(note,
            text="'Let Windows manage my default printer' must be set to OFF in\n"
                 "Printers & Scanners settings for printer selection to work correctly.",
            style='Card.TLabel', justify=tk.LEFT
        ).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(note, text="⚙  Open Printer Settings",
            command=self.open_printer_settings
        ).grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        note.columnconfigure(0, weight=1)

        ttk.Button(tab_content, text="Print MOs",
            command=self.print_mos, style='Accent.TButton'
        ).grid(row=5, column=0, columnspan=3, pady=20)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    def create_parts_tab(self):
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Create Parts")

        ttk.Label(tab_content,
            text="Create parts in TREQSO from a CSV file — one part per row.",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky=tk.W)

        ttk.Label(tab_content, text="CSV File:").grid(row=1, column=0, sticky=tk.E, pady=5)
        self.parts_file_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.parts_file_var, width=50).grid(
            row=1, column=1, sticky='ew', pady=5, padx=6)
        ttk.Button(tab_content, text="Browse…",
            command=lambda: self.browse_file(self.parts_file_var)
        ).grid(row=1, column=2, pady=5)

        format_frame = ttk.LabelFrame(tab_content, text="Expected CSV Format", padding="10")
        format_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(6, 4))
        self._build_csv_table(format_frame, "sample_parts.csv")

        self._build_instructions(tab_content, row=3, text=(
            "1.  Click \"Open Parts Template\" to open Parts_Template.xlsx in Excel.\n"
            "2.  Fill in your part data — one part per row. Do not change the column headers.\n"
            "3.  In Excel: File → Save As → CSV (Comma delimited) (*.csv) → Save.\n"
            "4.  Click Browse above and select the CSV file you just saved.\n"
            "5.  Click Create Parts."
        ))

        btn_frame = ttk.Frame(tab_content)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(8, 4))
        ttk.Button(btn_frame, text="Create Parts",
            command=self.create_parts, style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Parts Template",
            command=lambda: self.open_sample(resource_path('Parts_Template.csv'))
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Sample CSV",
            command=lambda: self.open_sample(resource_path('sample_parts.csv'))
        ).pack(side=tk.LEFT, padx=5)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    def create_edit_parts_tab(self):
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Edit Parts")

        ttk.Label(tab_content,
            text="Update attributes of existing parts in TREQSO from a CSV file. "
                 "Only the columns you include in the CSV will be changed — "
                 "all other fields are left exactly as they are.",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky=tk.W)

        ttk.Label(tab_content, text="CSV File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.edit_parts_file_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.edit_parts_file_var, width=50).grid(
            row=1, column=1, sticky='ew', pady=5, padx=6)
        ttk.Button(tab_content, text="Browse…",
            command=lambda: self.browse_file(self.edit_parts_file_var)
        ).grid(row=1, column=2, pady=5)

        # Format preview — shows the sample CSV (minimal columns)
        format_frame = ttk.LabelFrame(tab_content, text="Example CSV Format", padding="10")
        format_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(6, 4))
        self._build_csv_table(format_frame, "sample_edit_parts.csv")

        # Available fields reference card
        fields_frame = ttk.LabelFrame(tab_content, text="All Editable Fields                                                                                                          " \
        "                                    Instructions", padding="12")
        fields_frame.grid(row=3, column=0, columnspan=3, pady=(0, 4))

        fields_text = (
            "Include only the columns you need — any combination is valid.\n"
            "partNumber is always required.  All other columns are optional.\n\n"
            "  partStatus          standardCost     unitOfMeasure\n"
            "  partNumber          partDescription  fullDescription\n"
            "  partCategory        productCode      salesGroup\n"
            "  partType            phaseNumber      defaultCostField"
        )
        tk.Label(
            fields_frame,
            text=fields_text,
            font=('Consolas', 9),
            bg=CARD, fg=TEXT,
            justify=tk.LEFT, padx=4, pady=4
        ).grid(row=0, column=0, sticky=tk.W)

        instruction_text = (
            "   |   \n"
            "   |   \n"
            "   |   \n"
            "   |   \n"
            "   |   \n"
            "   |   \n"
            "   |   "
        )
        tk.Label(
            fields_frame,
            text=instruction_text,
            font=('Consolas', 9),
            bg=CARD, fg=TEXT,
            justify=tk.LEFT, padx=4, pady=4
        ).grid(row=0, column=1, sticky=tk.E)

        instruction_text = (
            "1.  Create a CSV file with a 'partNumber' column plus any fields you want to update.\n"
            "    You do not need to include columns you are not changing.\n"
            "2.  Fill in the part numbers and new values. Leave cells blank to skip that field for that part.     \n"
            "3.  In Excel: File → Save As → CSV (Comma delimited) (*.csv) → Save.\n"
            "4.  Click Browse above and select the CSV file you just saved.\n"
            "5.  Click Edit Parts."
        )
        tk.Label(
            fields_frame,
            text=instruction_text,
            font=('Consolas', 9),
            bg=CARD, fg=TEXT,
            justify=tk.LEFT, padx=4, pady=4
        ).grid(row=0, column=2, sticky=tk.E)

        btn_frame = ttk.Frame(tab_content)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(8, 4))
        ttk.Button(btn_frame, text="Edit Parts",
            command=self.edit_parts, style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Edit Parts Template",
            command=lambda: self.open_sample(resource_path('Edit_Parts_Template.csv'))
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Sample CSV",
            command=lambda: self.open_sample(resource_path('sample_edit_parts.csv'))
        ).pack(side=tk.LEFT, padx=5)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    def create_bom_tab(self):
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Create BOMs")

        ttk.Label(tab_content,
            text="Create Bills of Materials in TREQSO from a CSV file. "
                 "A single file can contain data for multiple assemblies.",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky=tk.W)

        ttk.Label(tab_content, text="CSV File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bom_file_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.bom_file_var, width=50).grid(
            row=1, column=1, sticky='ew', pady=5, padx=6)
        ttk.Button(tab_content, text="Browse…",
            command=lambda: self.browse_file(self.bom_file_var)
        ).grid(row=1, column=2, pady=5)

        format_frame = ttk.LabelFrame(tab_content, text="Expected CSV Format", padding="10")
        format_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(6, 4))
        self._build_csv_table(format_frame, "sample_bom.csv")

        self._build_instructions(tab_content, row=3, text=(
            "1.  Click \"Open BOM Template\" to open BOMs_Template.xlsx in Excel.\n"
            "2.  Fill in your BOM data — one component line per row. "
                 "All lines for the same assembly must be grouped together. "
                 "Do not change the column headers.\n"
            "3.  In Excel: File → Save As → CSV (Comma delimited) (*.csv) → Save.\n"
            "4.  Click Browse above and select the CSV file you just saved.\n"
            "5.  Click Create BOMs."
        ))

        btn_frame = ttk.Frame(tab_content)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(8, 4))
        ttk.Button(btn_frame, text="Create BOMs",
            command=self.create_bom, style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open BOM Template",
            command=lambda: self.open_sample(resource_path('BOMs_Template.csv'))
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Sample CSV",
            command=lambda: self.open_sample(resource_path('sample_bom.csv'))
        ).pack(side=tk.LEFT, padx=5)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    def create_replace_tab(self):
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Mass Replace Part")

        ttk.Label(tab_content,
            text="Replace a part across every assembly BOM that contains it. "
                 "The tool finds all affected assemblies automatically.",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky=tk.W)

        ttk.Label(tab_content, text="Old Part Number:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.old_pn_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.old_pn_var, width=40).grid(
            row=1, column=1, sticky='ew', pady=5, padx=6)

        ttk.Label(tab_content, text="New Part Number:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.new_pn_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.new_pn_var, width=40).grid(
            row=2, column=1, sticky='ew', pady=5, padx=6)

        ttk.Label(tab_content, text="New Quantity (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.quantity_var = tk.StringVar()
        ttk.Entry(tab_content, textvariable=self.quantity_var, width=40).grid(
            row=3, column=1, sticky='ew', pady=5, padx=6)

        # Example card
        ex_frame = ttk.LabelFrame(tab_content, text="Example", padding="12")
        ex_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(12, 4))
        tk.Label(ex_frame,
            text="Old Part Number:  RES-001-100K\n"
                 "New Part Number:  RES-002-100K\n"
                 "New Quantity:     4",
            font=('Consolas', 9),
            bg=CARD, fg=TEXT,
            justify=tk.LEFT, padx=4, pady=4
        ).grid(row=0, column=0, sticky=tk.W)

        ttk.Button(tab_content, text="Replace Part",
            command=self.replace_part, style='Accent.TButton'
        ).grid(row=5, column=0, columnspan=2, pady=20)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    def create_settings_tab(self):
        tab_container, tab_content = self._make_scrollable_tab(self.notebook)
        self.notebook.add(tab_container, text="Settings")

        ttk.Label(tab_content, text="TREQSO Connection Settings",
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 14), sticky=tk.W)

        ttk.Label(tab_content, text="TREQSO URL:").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.url_var = tk.StringVar(value=os.getenv('TREQSO_URL', ''))
        ttk.Entry(tab_content, textvariable=self.url_var, width=55).grid(
            row=1, column=1, sticky='ew', pady=6, padx=6)

        ttk.Label(tab_content, text="Company:").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.company = tk.StringVar(value=os.getenv('COMPANY', 'CargoTest'))
        ttk.Entry(tab_content, textvariable=self.company, width=55).grid(
            row=2, column=1, sticky='ew', pady=6, padx=6)

        ttk.Label(tab_content, text="Headless Mode:").grid(row=3, column=0, sticky=tk.W, pady=6)
        self.headless_var = tk.BooleanVar(
            value=os.getenv('TREQSO_HEADLESS', 'false').lower() == 'true')
        ttk.Checkbutton(tab_content,
            text="Run browser in background (no window)",
            variable=self.headless_var
        ).grid(row=3, column=1, sticky=tk.W, pady=6, padx=6)

        ttk.Label(tab_content, text="Slow Motion (ms):").grid(row=4, column=0, sticky=tk.W, pady=6)
        self.slowmo_var = tk.StringVar(value=os.getenv('TREQSO_SLOW_MO', '0'))
        ttk.Entry(tab_content, textvariable=self.slowmo_var, width=20).grid(
            row=4, column=1, sticky=tk.W, pady=6, padx=6)

        btn_frame = ttk.Frame(tab_content)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save Settings",
            command=self.save_settings
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frame, text="Test Connection",
            command=self.test_connection, style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Open User Guide",
            command=self.open_user_guide
        ).pack(side=tk.LEFT, padx=6)

        note_frame = ttk.LabelFrame(tab_content, text="Note", padding="12")
        note_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(4, 0))
        ttk.Label(note_frame,
            text="Settings are loaded from the .env file on startup. "
                 "Click 'Save Settings' to persist any changes.",
            style='Card.TLabel', wraplength=700
        ).grid(row=0, column=0, sticky=tk.W)

        tab_content.columnconfigure(0, weight=1)
        tab_content.columnconfigure(1, weight=20)
        tab_content.columnconfigure(2, weight=1)

    # ── Utility methods ───────────────────────────────────────────────────────

    def browse_file(self, var):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            var.set(filename)

    def open_user_guide(self):
        guide_path = os.path.join(self.processor._get_app_dir(), 'README_USER.md')
        if os.path.exists(guide_path):
            os.startfile(guide_path)
        else:
            messagebox.showwarning("File Not Found",
                f"User guide not found at:\n{guide_path}")

    def open_sample(self, filename):
        if os.path.exists(filename):
            os.startfile(filename) if os.name == 'nt' else os.system(f'open {filename}')
        else:
            messagebox.showwarning("File Not Found", f"File not found:\n{filename}")

    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.root.update()

    def clear_console(self):
        self.console.delete(1.0, tk.END)

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update()

    def update_processor_config(self):
        self.processor.config = {
            'url':      self.url_var.get(),
            'company':  self.company.get(),
            'headless': self.headless_var.get(),
            'slowMo':   int(self.slowmo_var.get() or 0)
        }
        self.processor.log_callback = self.log

    def refresh_printers(self, dropdown):
        try:
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            default_printer = win32print.GetDefaultPrinter()
            dropdown['values'] = printers
            if default_printer and default_printer in printers:
                dropdown.set(default_printer)
            elif printers:
                dropdown.set(printers[0])
            self.log(f"Printers refreshed. Found {len(printers)} printer(s).")
        except Exception as e:
            self.log(f"Error refreshing printers: {e}")
            messagebox.showerror("Error", f"Could not refresh printers: {e}")

    # ── Action handlers ───────────────────────────────────────────────────────

    def print_mos(self):
        MO_ref_id    = self.MO_ref_id.get()
        printer_name = self.printer_var.get()
        if not MO_ref_id:
            messagebox.showwarning("Missing Information",
                "Please enter a Parent MO Reference ID.")
            return
        if not printer_name or printer_name == "No printers found":
            messagebox.showwarning("No Printer Selected",
                "Please select a printer from the dropdown.")
            return
        try:
            win32print.SetDefaultPrinter(printer_name)
            self.log(f"Set default printer to: {printer_name}")
        except Exception as e:
            self.log(f"Warning: Could not set default printer: {e}")
        self.clear_console()
        self.log("=== Printing MOs ===")
        self.log(f"Parent Reference ID: {MO_ref_id}")
        self.log(f"Printer: {printer_name}")
        threading.Thread(
            target=self._print_mos_thread, args=(MO_ref_id, printer_name)
        ).start()

    def _print_mos_thread(self, MO_ref_id, printer_name):
        try:
            self.update_processor_config()
            result  = self.processor.print_MOs(MO_ref_id)
            summary = result.get('summary', {})
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log(f"✓ MOs printed successfully! "
                    f"({summary.get('successful', 0)}/{summary.get('total', 0)})")
                self.update_status("Printing completed")
                messagebox.showinfo("Success",
                    f"MOs printed successfully!\n"
                    f"{summary.get('successful', 0)}/{summary.get('total', 0)} MOs printed.")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                if summary.get('total', 0) > 0:
                    self.log(f"Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
                    if summary.get('failures'):
                        self.log("\nFailed MOs:")
                        for mo in summary['failures']:
                            self.log(f"  - {mo}")
                    self.update_status("Printing completed with failures")
                    failures_list = '\n'.join(f"  - {mo}" for mo in summary.get('failures', []))
                    messagebox.showwarning("Partial Failure",
                        f"{summary.get('successful', 0)}/{summary.get('total', 0)} MOs printed.\n\n"
                        f"Failed MOs:\n{failures_list}")
                else:
                    self.update_status("Printing failed")
                    messagebox.showerror("Error",
                        f"Failed to print MOs: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def create_parts(self):
        csv_file = self.parts_file_var.get()
        if not csv_file:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        if not os.path.exists(csv_file):
            messagebox.showerror("File Not Found", f"File not found:\n{csv_file}")
            return
        self.clear_console()
        self.log("=== Creating Parts ===")
        self.log(f"Reading from: {csv_file}")
        self.update_status("Creating parts...")
        threading.Thread(target=self._create_parts_thread, args=(csv_file,)).start()

    def _create_parts_thread(self, csv_file):
        try:
            self.update_processor_config()
            result  = self.processor.create_parts_from_csv(csv_file)
            summary = result.get('summary', {})
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log("✓ Parts created successfully!")
                self.log(f"Total: {summary.get('total', 0)}")
                self.log(f"Successful: {summary.get('successful', 0)}")
                self.log(f"Failed: {summary.get('failed', 0)}")
                if summary.get('failures'):
                    self.log("\nFailed parts:")
                    for pn in summary['failures']:
                        self.log(f"  - {pn}")
                self.update_status("Parts creation completed")
                messagebox.showinfo("Success",
                    f"Parts created successfully!\n"
                    f"{summary.get('successful', 0)}/{summary.get('total', 0)} parts created.")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                if summary.get('total', 0) > 0:
                    self.log(f"Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
                    if summary.get('failures'):
                        self.log("\nFailed parts:")
                        for pn in summary['failures']:
                            self.log(f"  - {pn}")
                    self.update_status("Parts creation completed with failures")
                    failures_list = '\n'.join(f"  - {pn}" for pn in summary.get('failures', []))
                    messagebox.showwarning("Partial Failure",
                        f"{summary.get('successful', 0)}/{summary.get('total', 0)} parts created.\n\n"
                        f"Failed parts:\n{failures_list}")
                else:
                    self.update_status("Parts creation failed")
                    messagebox.showerror("Error",
                        f"Failed to create parts: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def edit_parts(self):
        csv_file = self.edit_parts_file_var.get()
        if not csv_file:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        if not os.path.exists(csv_file):
            messagebox.showerror("File Not Found", f"File not found:\n{csv_file}")
            return
        self.clear_console()
        self.log("=== Editing Parts ===")
        self.log(f"Reading from: {csv_file}")
        self.update_status("Editing parts...")
        threading.Thread(target=self._edit_parts_thread, args=(csv_file,)).start()

    def _edit_parts_thread(self, csv_file):
        try:
            self.update_processor_config()
            result  = self.processor.edit_parts_from_csv(csv_file)
            summary = result.get('summary', {})
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log("✓ Parts updated successfully!")
                self.log(f"Total: {summary.get('total', 0)}")
                self.log(f"Successful: {summary.get('successful', 0)}")
                self.log(f"Failed: {summary.get('failed', 0)}")
                if summary.get('failures'):
                    self.log("\nFailed parts:")
                    for pn in summary['failures']:
                        self.log(f"  - {pn}")
                self.update_status("Parts edit completed")
                messagebox.showinfo("Success",
                    f"Parts updated successfully!\n"
                    f"{summary.get('successful', 0)}/{summary.get('total', 0)} parts updated.")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                if summary.get('total', 0) > 0:
                    self.log(f"Successful: {summary.get('successful', 0)}/{summary.get('total', 0)}")
                    if summary.get('failures'):
                        self.log("\nFailed parts:")
                        for pn in summary['failures']:
                            self.log(f"  - {pn}")
                    self.update_status("Parts edit completed with failures")
                    failures_list = '\n'.join(f"  - {pn}" for pn in summary.get('failures', []))
                    messagebox.showwarning("Partial Failure",
                        f"{summary.get('successful', 0)}/{summary.get('total', 0)} parts updated.\n\n"
                        f"Failed parts:\n{failures_list}")
                else:
                    self.update_status("Parts edit failed")
                    messagebox.showerror("Error",
                        f"Failed to edit parts: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def create_bom(self):
        csv_file = self.bom_file_var.get()
        if not csv_file:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        if not os.path.exists(csv_file):
            messagebox.showerror("File Not Found", f"File not found:\n{csv_file}")
            return
        self.clear_console()
        self.log("=== Creating BOMs ===")
        self.log(f"Reading from: {csv_file}")
        self.update_status("Creating BOMs...")
        threading.Thread(target=self._create_bom_thread, args=(csv_file,)).start()

    def _create_bom_thread(self, csv_file):
        try:
            self.update_processor_config()
            result = self.processor.create_bom_from_csv(csv_file)
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log(f"✓ BOM created successfully for {result.get('assemblyPartNumber')}!")
                self.log(f"Lines added: {result.get('lineCount', 0)}")
                self.update_status("BOM creation completed")
                messagebox.showinfo("Success", "BOMs created successfully!")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                self.update_status("BOM creation failed")
                messagebox.showerror("Error",
                    f"Failed to create BOMs: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def replace_part(self):
        old_pn   = self.old_pn_var.get()
        new_pn   = self.new_pn_var.get()
        quantity = self.quantity_var.get()
        if not all([old_pn, new_pn]):
            messagebox.showwarning("Missing Information",
                "Please fill in both Old Part Number and New Part Number.")
            return
        self.clear_console()
        self.log("=== Replacing Part ===")
        self.log(f"Old Part: {old_pn}")
        self.log(f"New Part: {new_pn}")
        if quantity:
            self.log(f"New Quantity: {quantity}")
        self.update_status("Replacing part...")
        qty = float(quantity) if quantity else None
        threading.Thread(
            target=self._replace_part_thread, args=(old_pn, new_pn, qty)
        ).start()

    def _replace_part_thread(self, old_pn, new_pn, quantity=None):
        try:
            self.update_processor_config()
            result = self.processor.replace_part(old_pn, new_pn, quantity)
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log("✓ Part replaced successfully!")
                self.update_status("Part replacement completed")
                messagebox.showinfo("Success", "Part replaced successfully!")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                self.update_status("Part replacement failed")
                messagebox.showerror("Error",
                    f"Failed to replace part: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def test_connection(self):
        self.clear_console()
        self.log("=== Testing Connection ===")
        self.log(f"URL: {self.url_var.get()}")
        self.log(f"Company: {self.company.get()}")
        self.update_status("Testing connection...")
        threading.Thread(target=self._test_connection_thread).start()

    def _test_connection_thread(self):
        try:
            self.update_processor_config()
            result = self.processor.test_login()
            self.log("\n=== Results ===")
            if result.get('success'):
                self.log("✓ Connection successful!")
                self.log("Screenshot saved: login_success.png")
                self.update_status("Connection test passed")
                messagebox.showinfo("Success", "Successfully connected to TREQSO!")
            else:
                self.log(f"✗ Error: {result.get('error', 'Unknown error')}")
                self.update_status("Connection test failed")
                messagebox.showerror("Error",
                    f"Connection failed: {result.get('error')}")
        except Exception as e:
            self.log(f"✗ Exception: {e}")
            self.update_status("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def save_settings(self):
        try:
            env_content = (
                "# TREQSO Configuration\n"
                f"TREQSO_URL={self.url_var.get()}\n"
                f"COMPANY={self.company.get()}\n"
                f"TREQSO_HEADLESS={'true' if self.headless_var.get() else 'false'}\n"
                f"TREQSO_SLOW_MO={self.slowmo_var.get()}\n"
            )
            env_path = os.path.join(self.processor._get_app_dir(), '.env')
            with open(env_path, 'w') as f:
                f.write(env_content)
            messagebox.showinfo("Saved", "Settings saved to .env file.")
            self.log("Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


def main():
    """Launch the TREQSO Automation Tool GUI."""
    root = tk.Tk()
    app = TREQSOGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
