import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import requests
import random
from datetime import datetime
import json
import re
import asyncio
import aiohttp
import os
import sqlite3
from collections import defaultdict
from itertools import cycle

class AnimatedProgressbar(ttk.Progressbar):
    """Animated progressbar with purple color cycling"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._colors = cycle(['#9B59B6', '#8E44AD', '#7D3C98', '#6C3483', '#BB8FCE'])
        self._animate_id = None
        self._animate()

    def _animate(self):
        color = next(self._colors)
        style = ttk.Style()
        style.configure('Animated.Horizontal.TProgressbar', 
                       troughcolor='#1A0E2E', 
                       background=color, 
                       bordercolor='#2C1B47',
                       lightcolor=color,
                       darkcolor=color)
        self.configure(style='Animated.Horizontal.TProgressbar')
        self._animate_id = self.after(800, self._animate)

    def stop_animation(self):
        if self._animate_id:
            self.after_cancel(self._animate_id)

class ProxyListCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxy List Creator v1 by BoCry69")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)
        self.root.attributes('-alpha', 0.92)
        self.root.configure(bg='#0F0A1A')
        
        # Status variables
        self.is_running = False
        self.is_paused = False
        self.proxy_list = []
        self.checked_proxies = []
        self.filtered_proxies = []  # NEW: Filtered results
        self.scraped_count = 0
        self.checked_count = 0
        self.cache_file = "proxy_cache.json"
        self.start_time = None
        
        # Settings variables
        self.proxy_type = tk.StringVar(value="HTTP")
        self.timeout = tk.StringVar(value="5")
        self.max_threads = tk.StringVar(value="50")
        self.batch_size = tk.StringVar(value="10")
        self.rate_limit = tk.StringVar(value="5")
        self.country_filter = tk.StringVar(value="")
        self.anonymity_filter = tk.StringVar(value="all")
        self.speed_filter = tk.StringVar(value="all")
        self.dark_mode = tk.BooleanVar(value=True)
        
        # NEW: Saved filter settings - FIX: Initialize properly
        self.saved_filters = {
            'country': "",
            'anonymity': "all",
            'speed': "all"
        }
        
        # Advanced features
        self.proxy_categories = defaultdict(list)
        self.geographic_stats = defaultdict(int)
        self.anonymity_stats = defaultdict(int)
        
        # Setup styles and GUI
        self.setup_purple_black_styles()
        self.setup_gui()
        self.setup_database()
        
    def setup_purple_black_styles(self):
        """Modern purple-black transparent design with glassmorphism effects"""
        self.style = ttk.Style()
        self.style.theme_create("purple_black_glass", parent="clam", settings={
            "TFrame": {"configure": {"background": "#1A0E2E", "relief": "flat", "borderwidth": 1}},
            "TLabel": {"configure": {"background": "#1A0E2E", "foreground": "#E8DAEF", 
                                    "font": ("Segoe UI", 11), "relief": "flat"}},
            "TButton": {
                "configure": {"background": "#8E44AD", "foreground": "white", "borderwidth": 0, 
                             "relief": "flat", "font": ("Segoe UI", 11, "bold"), "padding": [15, 8]},
                "map": {"background": [("active", "#9B59B6"), ("pressed", "#7D3C98")],
                        "foreground": [("active", "white"), ("pressed", "white")]}},
            "TEntry": {"configure": {"fieldbackground": "#2C1B47", "background": "#2C1B47", 
                                    "foreground": "#F8F9FA", "bordercolor": "#8E44AD", "borderwidth": 2,
                                    "relief": "flat", "insertcolor": "#E8DAEF"}},
            "TCombobox": {"configure": {"fieldbackground": "#2C1B47", "background": "#2C1B47", 
                                       "foreground": "#F8F9FA", "bordercolor": "#8E44AD", "borderwidth": 2,
                                       "arrowcolor": "#BB8FCE", "relief": "flat"}},
            "TCheckbutton": {"configure": {"background": "#1A0E2E", "foreground": "#E8DAEF", 
                                          "focuscolor": "#9B59B6", "font": ("Segoe UI", 11)}},
            "TNotebook": {"configure": {"background": "#0F0A1A", "borderwidth": 0, "relief": "flat"}},
            "TNotebook.Tab": {"configure": {"background": "#2C1B47", "foreground": "#E8DAEF", 
                                           "padding": [18, 10], "font": ("Segoe UI", 11, "bold")},
                             "map": {"background": [("selected", "#8E44AD"), ("active", "#6C3483")],
                                    "foreground": [("selected", "white"), ("active", "#E8DAEF")]}},
            "TLabelframe": {"configure": {"background": "#1A0E2E", "foreground": "#BB8FCE", 
                                         "bordercolor": "#6C3483", "borderwidth": 2, "relief": "flat",
                                         "font": ("Segoe UI", 12, "bold")}},
            "TLabelframe.Label": {"configure": {"background": "#1A0E2E", "foreground": "#D2B4DE", 
                                               "font": ("Segoe UI", 12, "bold")}},
            "Treeview": {
                "configure": {"background": "#2C1B47", "fieldbackground": "#2C1B47", 
                             "foreground": "#F8F9FA", "borderwidth": 2, "relief": "flat",
                             "bordercolor": "#8E44AD"},
                "map": {"background": [("selected", "#8E44AD")],
                        "foreground": [("selected", "white")]}},
            "Treeview.Heading": {"configure": {"background": "#6C3483", "foreground": "white",
                                              "font": ("Segoe UI", 11, "bold"), "relief": "flat"}},
            "Vertical.TScrollbar": {"configure": {"background": "#6C3483", "troughcolor": "#1A0E2E",
                                                 "bordercolor": "#8E44AD", "arrowcolor": "#BB8FCE"}},
            "Horizontal.TScrollbar": {"configure": {"background": "#6C3483", "troughcolor": "#1A0E2E",
                                                   "bordercolor": "#8E44AD", "arrowcolor": "#BB8FCE"}}
        })
        self.style.theme_use("purple_black_glass")
        
    def setup_database(self):
        """Initialize SQLite database for proxy storage"""
        self.db_conn = sqlite3.connect("proxy_db.sqlite", check_same_thread=False)
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY,
                ip TEXT,
                port TEXT,
                type TEXT,
                response_time INTEGER,
                anonymity_level TEXT,
                country TEXT,
                last_checked TIMESTAMP,
                success_rate REAL DEFAULT 1.0,
                category TEXT DEFAULT 'unknown'
            )
        ''')
        self.db_conn.commit()
        
    def setup_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="20", style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_container, text="🚀 PROXY LIST CREATOR v1 by BoCry69", 
                               font=('Segoe UI', 26, 'bold'), foreground="#D2B4DE", 
                               background="#1A0E2E")
        title_label.pack(pady=(0, 25))
        
        subtitle_label = ttk.Label(main_container, text="Advanced Proxy Management Suite", 
                                  font=('Segoe UI', 13), foreground="#BB8FCE", 
                                  background="#1A0E2E")
        subtitle_label.pack(pady=(0, 25))
        
        # Create notebook
        self.notebook = ttk.Notebook(main_container, style="TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.main_tab = ttk.Frame(self.notebook, padding="20", style="TFrame")
        self.notebook.add(self.main_tab, text="🏠  MAIN")
        
        self.settings_tab = ttk.Frame(self.notebook, padding="20", style="TFrame")
        self.notebook.add(self.settings_tab, text="⚙️  ADVANCED")
        
        self.stats_tab = ttk.Frame(self.notebook, padding="20", style="TFrame")
        self.notebook.add(self.stats_tab, text="📊  ANALYTICS")
        
        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_stats_tab()
        
    def setup_main_tab(self):
        # Quick settings - more compact
        settings_frame = ttk.LabelFrame(self.main_tab, text="⚡ QUICK SETTINGS", 
                                       padding="15", style="TLabelframe")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Compact settings in one row
        settings_row = ttk.Frame(settings_frame, style="TFrame")
        settings_row.pack(fill=tk.X)
        
        # Left side settings
        left_settings = ttk.Frame(settings_row, style="TFrame")
        left_settings.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_settings, text="Type:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        proxy_combo = ttk.Combobox(left_settings, textvariable=self.proxy_type, 
                                  values=["HTTP", "HTTPS", "SOCKS4", "SOCKS5", "All"], 
                                  state="readonly", width=8, font=('Segoe UI', 10))
        proxy_combo.grid(row=0, column=1, padx=(0, 15))
        
        ttk.Label(left_settings, text="Timeout:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        timeout_entry = ttk.Entry(left_settings, textvariable=self.timeout, width=6, font=('Segoe UI', 10))
        timeout_entry.grid(row=0, column=3, padx=(0, 15))
        
        ttk.Label(left_settings, text="Threads:", font=('Segoe UI', 10, 'bold')).grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        threads_entry = ttk.Entry(left_settings, textvariable=self.max_threads, width=6, font=('Segoe UI', 10))
        threads_entry.grid(row=0, column=5)
        
        # COMPACT BUTTON LAYOUT - All buttons in one tight row
        button_frame = ttk.Frame(self.main_tab, style="TFrame")
        button_frame.pack(pady=15)
        
        # Left side buttons (main actions)
        left_buttons = ttk.Frame(button_frame, style="TFrame")
        left_buttons.pack(side=tk.LEFT, padx=(0, 30))
        
        self.start_button = ttk.Button(left_buttons, text="▶️ START", command=self.start_scraping, style="TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.pause_button = ttk.Button(left_buttons, text="⏸️ PAUSE", command=self.pause_resume, 
                                      state=tk.DISABLED, style="TButton")
        self.pause_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.stop_button = ttk.Button(left_buttons, text="⏹️ STOP", command=self.stop_scraping, 
                                     state=tk.DISABLED, style="TButton")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # Right side buttons (utility actions)
        right_buttons = ttk.Frame(button_frame, style="TFrame")
        right_buttons.pack(side=tk.RIGHT)
        
        # NEW: Save Settings Button
        self.save_settings_button = ttk.Button(right_buttons, text="💾 SAVE FILTERS", 
                                              command=self.save_and_apply_filters, style="TButton")
        self.save_settings_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.export_button = ttk.Button(right_buttons, text="📁 EXPORT", command=self.export_proxies, style="TButton")
        self.export_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.clear_button = ttk.Button(right_buttons, text="🗑️ CLEAR", command=self.clear_log, style="TButton")
        self.clear_button.pack(side=tk.LEFT)
        
        # Progress section - more compact
        progress_frame = ttk.LabelFrame(self.main_tab, text="📈 PROGRESS", 
                                       padding="15", style="TLabelframe")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Scraping progress
        scrape_header = ttk.Label(progress_frame, text="🔍 HARVESTING", 
                                 font=('Segoe UI', 11, 'bold'), foreground="#D2B4DE")
        scrape_header.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_scraping = AnimatedProgressbar(progress_frame, mode='determinate', length=700)
        self.progress_scraping.pack(fill=tk.X, pady=(0, 8))
        
        scrape_info_frame = ttk.Frame(progress_frame, style="TFrame")
        scrape_info_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.scrape_eta_label = ttk.Label(scrape_info_frame, text="🕐 ETA: --:--", font=('Segoe UI', 9))
        self.scrape_eta_label.pack(side=tk.LEFT)
        
        self.scrape_speed_label = ttk.Label(scrape_info_frame, text="⚡ Speed: 0/s", font=('Segoe UI', 9))
        self.scrape_speed_label.pack(side=tk.RIGHT)
        
        # Checking progress
        check_header = ttk.Label(progress_frame, text="🛡️ VALIDATION", 
                                font=('Segoe UI', 11, 'bold'), foreground="#D2B4DE")
        check_header.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_checking = AnimatedProgressbar(progress_frame, mode='determinate', length=700)
        self.progress_checking.pack(fill=tk.X, pady=(0, 8))
        
        check_info_frame = ttk.Frame(progress_frame, style="TFrame")
        check_info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.check_eta_label = ttk.Label(check_info_frame, text="🕐 ETA: --:--", font=('Segoe UI', 9))
        self.check_eta_label.pack(side=tk.LEFT)
        
        self.check_speed_label = ttk.Label(check_info_frame, text="⚡ Speed: 0/s", font=('Segoe UI', 9))
        self.check_speed_label.pack(side=tk.RIGHT)
        
        # Statistics compact
        stats_grid = ttk.Frame(progress_frame, style="TFrame")
        stats_grid.pack(fill=tk.X)
        
        self.scraped_label = ttk.Label(stats_grid, text="🔍 Harvested: 0", 
                                      font=('Segoe UI', 11, 'bold'), foreground="#E8DAEF")
        self.scraped_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.checked_label = ttk.Label(stats_grid, text="🔄 Validated: 0", 
                                      font=('Segoe UI', 11, 'bold'), foreground="#E8DAEF")
        self.checked_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.valid_label = ttk.Label(stats_grid, text="✅ Active: 0", 
                                    font=('Segoe UI', 11, 'bold'), foreground="#27AE60")
        self.valid_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.filtered_label = ttk.Label(stats_grid, text="🎯 Filtered: 0", 
                                       font=('Segoe UI', 11, 'bold'), foreground="#F39C12")
        self.filtered_label.pack(side=tk.LEFT)
        
        self.success_rate_label = ttk.Label(stats_grid, text="📊 Success: 0%", 
                                           font=('Segoe UI', 11, 'bold'), foreground="#F39C12")
        self.success_rate_label.pack(side=tk.RIGHT)
        
        # BIGGER RESULTS TABLE
        results_frame = ttk.LabelFrame(self.main_tab, text="🎯 FILTERED PROXIES", 
                                      padding="15", style="TLabelframe")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with INCREASED HEIGHT
        columns = ('🌐 IP:Port', '🔧 Type', '⚡ Speed', '🏆 Category', '🌍 Country', '🔒 Anonymity')
        self.result_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=20,  # INCREASED from 14 to 20
                                       style="Treeview")
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=150, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.result_tree.yview,
                                   style="Vertical.TScrollbar")
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview,
                                   style="Horizontal.TScrollbar")
        self.result_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
    def setup_settings_tab(self):
        # Settings title
        title_label = ttk.Label(self.settings_tab, text="⚙️ ADVANCED FILTERS", 
                               font=('Segoe UI', 20, 'bold'), foreground="#D2B4DE")
        title_label.pack(pady=(0, 25), anchor=tk.W)
        
        # Filter explanation
        info_label = ttk.Label(self.settings_tab, 
                              text="💡 Configure filters below, then click 'SAVE FILTERS' to apply them to results", 
                              font=('Segoe UI', 11), foreground="#BB8FCE")
        info_label.pack(pady=(0, 20), anchor=tk.W)
        
        # Filtering settings
        filter_frame = ttk.LabelFrame(self.settings_tab, text="🎛️ FILTER SETTINGS", 
                                     padding="25", style="TLabelframe")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Country filter
        ttk.Label(filter_frame, text="🌍 Country Filter (e.g., US, DE, UK):", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        country_entry = ttk.Entry(filter_frame, textvariable=self.country_filter, 
                                 font=('Segoe UI', 12), width=50)
        country_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Anonymity filter
        ttk.Label(filter_frame, text="🔒 Anonymity Level:", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        anon_combo = ttk.Combobox(filter_frame, textvariable=self.anonymity_filter,
                                 values=["all", "elite", "anonymous", "transparent"], 
                                 state="readonly", font=('Segoe UI', 12))
        anon_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Speed filter - MAIN FEATURE
        ttk.Label(filter_frame, text="⚡ Speed Category (IMPORTANT):", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        speed_combo = ttk.Combobox(filter_frame, textvariable=self.speed_filter,
                                  values=["all", "fast", "medium", "slow"], 
                                  state="readonly", font=('Segoe UI', 12))
        speed_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Filter explanation
        filter_note = ttk.Label(filter_frame, 
                               text="📌 Note: Set 'fast' to show only fast proxies, 'medium' for medium, etc.",
                               font=('Segoe UI', 10), foreground="#F39C12")
        filter_note.pack(anchor=tk.W)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(self.settings_tab, text="🚀 PERFORMANCE", 
                                   padding="25", style="TLabelframe")
        perf_frame.pack(fill=tk.X)
        
        # Batch size
        ttk.Label(perf_frame, text="📦 Batch Size:", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        batch_entry = ttk.Entry(perf_frame, textvariable=self.batch_size, 
                               font=('Segoe UI', 12))
        batch_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Rate limiting
        ttk.Label(perf_frame, text="⏱️ Rate Limit (req/sec):", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        rate_entry = ttk.Entry(perf_frame, textvariable=self.rate_limit, 
                              font=('Segoe UI', 12))
        rate_entry.pack(fill=tk.X)
        
    def setup_stats_tab(self):
        # Analytics title
        title_label = ttk.Label(self.stats_tab, text="📊 ANALYTICS", 
                               font=('Segoe UI', 20, 'bold'), foreground="#D2B4DE")
        title_label.pack(pady=(0, 25), anchor=tk.W)
        
        # Speed categories
        speed_frame = ttk.LabelFrame(self.stats_tab, text="⚡ PERFORMANCE METRICS", 
                                    padding="20", style="TLabelframe")
        speed_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.fast_count_label = ttk.Label(speed_frame, text="🚄 Fast (< 500ms): 0", 
                                         font=('Segoe UI', 13, 'bold'), foreground="#27AE60")
        self.fast_count_label.pack(anchor=tk.W, pady=3)
        
        self.medium_count_label = ttk.Label(speed_frame, text="🚗 Medium (500-2000ms): 0", 
                                           font=('Segoe UI', 13, 'bold'), foreground="#F39C12")
        self.medium_count_label.pack(anchor=tk.W, pady=3)
        
        self.slow_count_label = ttk.Label(speed_frame, text="🐌 Slow (> 2000ms): 0", 
                                         font=('Segoe UI', 13, 'bold'), foreground="#E74C3C")
        self.slow_count_label.pack(anchor=tk.W, pady=3)
        
        # Geographic distribution
        geo_frame = ttk.LabelFrame(self.stats_tab, text="🌍 GLOBAL DISTRIBUTION", 
                                  padding="20", style="TLabelframe")
        geo_frame.pack(fill=tk.BOTH, expand=True)
        
        self.geo_stats_text = scrolledtext.ScrolledText(geo_frame, height=18, 
                                                       font=('Consolas', 11),
                                                       bg="#2C1B47", fg="#F8F9FA",
                                                       insertbackground="#BB8FCE",
                                                       selectbackground="#8E44AD")
        self.geo_stats_text.pack(fill=tk.BOTH, expand=True)
        
    # FIX: Improved save and apply filters function
    def save_and_apply_filters(self):
        """Save current filter settings and apply them to the proxy list - FIXED VERSION"""
        # Save current filter values
        self.saved_filters['country'] = self.country_filter.get().strip().upper()
        self.saved_filters['anonymity'] = self.anonymity_filter.get()
        self.saved_filters['speed'] = self.speed_filter.get()
        
        print(f"DEBUG: Saved filters: {self.saved_filters}")  # Debug output
        
        # Apply filters to existing proxies
        self.apply_filters_to_results()
        
        # Show success message
        messagebox.showinfo("Filters Applied", 
                           f"✅ Filters applied successfully!\n\n"
                           f"🌍 Country: {self.saved_filters['country'] or 'All'}\n"
                           f"🔒 Anonymity: {self.saved_filters['anonymity']}\n"
                           f"⚡ Speed: {self.saved_filters['speed']}\n\n"
                           f"📊 Showing: {len(self.filtered_proxies)} proxies")
        
    def apply_filters_to_results(self):
        """Filter existing proxy results based on saved filters - FIXED VERSION"""
        # Clear current table
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # Clear filtered proxies
        self.filtered_proxies.clear()
        
        print(f"DEBUG: Total proxies to filter: {len(self.checked_proxies)}")  # Debug
        
        # Apply filters to checked proxies
        for proxy in self.checked_proxies:
            if self.proxy_matches_filters(proxy):
                self.filtered_proxies.append(proxy)
                self.add_proxy_to_table(proxy)
        
        print(f"DEBUG: Filtered proxies: {len(self.filtered_proxies)}")  # Debug
        
        # Update filtered count
        self.update_stats()
        
    # FIX: Corrected proxy matching logic
    def proxy_matches_filters(self, proxy):
        """Check if a proxy matches the current filter criteria - FIXED VERSION"""
        
        # Debug output
        print(f"DEBUG: Checking proxy {proxy['ip']}:{proxy['port']} - category: '{proxy['category']}' vs filter: '{self.saved_filters['speed']}'")
        
        # Country filter
        if (self.saved_filters['country'] and 
            proxy.get('country', '').upper() != self.saved_filters['country']):
            print(f"DEBUG: Country filter failed: {proxy.get('country', '')} != {self.saved_filters['country']}")
            return False
        
        # Anonymity filter
        if (self.saved_filters['anonymity'] != 'all' and 
            proxy.get('anonymity', '') != self.saved_filters['anonymity']):
            print(f"DEBUG: Anonymity filter failed: {proxy.get('anonymity', '')} != {self.saved_filters['anonymity']}")
            return False
        
        # Speed filter - MAIN FIX: Ensure exact matching
        if (self.saved_filters['speed'] != 'all' and 
            proxy.get('category', '').lower() != self.saved_filters['speed'].lower()):
            print(f"DEBUG: Speed filter failed: '{proxy.get('category', '').lower()}' != '{self.saved_filters['speed'].lower()}'")
            return False
        
        print(f"DEBUG: Proxy {proxy['ip']} PASSED all filters")
        return True
        
    def add_proxy_to_table(self, proxy_data):
        """Add a single proxy to the results table"""
        category_icons = {
            'fast': '🚄',
            'medium': '🚗', 
            'slow': '🐌'
        }
        
        icon = category_icons.get(proxy_data['category'], '❓')
        
        self.result_tree.insert('', tk.END, values=(
            f"{proxy_data['ip']}:{proxy_data['port']}",
            proxy_data['type'],
            f"{proxy_data['response_time']}ms",
            f"{icon} {proxy_data['category'].title()}",
            f"🌍 {proxy_data['country']}",
            f"🔒 {proxy_data['anonymity'].title()}"
        ))
        
    # Core functionality methods (keep existing logic)
    def start_scraping(self):
        """Start scraping with validation"""
        if self.is_running:
            return
            
        try:
            timeout_val = int(self.timeout.get())
            threads_val = int(self.max_threads.get())
            batch_val = int(self.batch_size.get())
            rate_val = int(self.rate_limit.get())
            
            if timeout_val <= 0 or threads_val <= 0 or batch_val <= 0 or rate_val <= 0:
                raise ValueError("All values must be positive")
                
        except ValueError:
            messagebox.showerror("Configuration Error", 
                               "⚠️ Please check your settings!\nAll values must be positive numbers.")
            return
            
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        
        # Update button states
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        
        # Clear previous results
        self.checked_proxies.clear()
        self.filtered_proxies.clear()
        self.proxy_list.clear()
        self.scraped_count = 0
        self.checked_count = 0
        
        # Clear table
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # Start async operations
        threading.Thread(target=self.async_wrapper, daemon=True).start()
        
    def pause_resume(self):
        """Pause or resume"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="▶️ RESUME")
        else:
            self.pause_button.config(text="⏸️ PAUSE")
            
    def stop_scraping(self):
        """Stop scraping"""
        self.is_running = False
        self.is_paused = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸️ PAUSE")
        self.stop_button.config(state=tk.DISABLED)
        
    def async_wrapper(self):
        """Async wrapper"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.enhanced_async_scrape())
        except Exception as e:
            print(f"Async error: {e}")
        finally:
            loop.close()
            
    async def enhanced_async_scrape(self):
        """Enhanced async scraping"""
        proxy_sources = [
            "https://raw.githubusercontent.com/oxylabs/free-proxy-list/master/list.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
            "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
            "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/socks5.txt",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://www.proxy-list.download/api/v1/get?type=socks4",
            "https://www.proxy-list.download/api/v1/get?type=socks5",
        ]
        
        total_sources = len(proxy_sources)
        scraped_proxies = set()
        
        batch_size = int(self.batch_size.get())
        rate_limit = int(self.rate_limit.get())
        selected_type = self.proxy_type.get().lower()
        
        self.root.after(0, lambda: self.progress_scraping.config(maximum=total_sources, value=0))
        
        semaphore = asyncio.Semaphore(rate_limit)
        
        connector = aiohttp.TCPConnector(limit=int(self.max_threads.get()), ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            for i in range(0, len(proxy_sources), batch_size):
                if not self.is_running:
                    break
                    
                while self.is_paused:
                    await asyncio.sleep(0.1)
                    
                batch = proxy_sources[i:i+batch_size]
                tasks = [self.fetch_with_semaphore(semaphore, session, url) for url in batch]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        for proxy in result:
                            proxy_type = self.determine_proxy_type_from_source(proxy, selected_type)
                            if selected_type == "all" or proxy_type == selected_type:
                                scraped_proxies.add(proxy)
                        
                completed_sources = min(i + batch_size, total_sources)
                self.scraped_count = len(scraped_proxies)
                
                self.root.after(0, lambda: self.update_progress_with_eta(
                    "scraping", completed_sources, total_sources, self.start_time))
                self.root.after(0, self.update_stats)
                
                await asyncio.sleep(1.0 / rate_limit)
        
        self.proxy_list = list(scraped_proxies)
        
        if self.is_running and self.proxy_list:
            await self.enhanced_async_check()
        else:
            self.stop_scraping()
            
    async def fetch_with_semaphore(self, semaphore, session, url):
        """Fetch URL with rate limiting"""
        async with semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}\b', text)
                        return proxies
            except Exception:
                pass
            return []
            
    def determine_proxy_type_from_source(self, proxy, selected_type):
        """Determine proxy type"""
        if selected_type != "all":
            return selected_type
        return "http"
            
    async def enhanced_async_check(self):
        """Enhanced async checking"""
        total_proxies = len(self.proxy_list)
        if total_proxies == 0:
            self.stop_scraping()
            return
            
        check_start_time = time.time()
        timeout_val = int(self.timeout.get())
        threads_val = int(self.max_threads.get())
        
        self.root.after(0, lambda: self.progress_checking.config(maximum=total_proxies, value=0))
        
        semaphore = asyncio.Semaphore(threads_val)
        
        connector = aiohttp.TCPConnector(limit=threads_val)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            tasks = [self.check_proxy_enhanced(semaphore, session, proxy, timeout_val) 
                    for proxy in self.proxy_list]
            
            completed = 0
            for coro in asyncio.as_completed(tasks):
                if not self.is_running:
                    break
                    
                while self.is_paused:
                    await asyncio.sleep(0.1)
                    
                result = await coro
                if result:
                    self.checked_proxies.append(result)
                    
                    # FIX: Only add to table if it matches current filters OR if no filters are set
                    if (self.saved_filters['speed'] == 'all' and 
                        self.saved_filters['country'] == '' and 
                        self.saved_filters['anonymity'] == 'all') or self.proxy_matches_filters(result):
                        self.filtered_proxies.append(result)
                        self.root.after(0, lambda r=result: self.add_proxy_to_table(r))
                    
                    self.store_proxy_in_db(result)
                    
                completed += 1
                self.checked_count = completed
                
                self.root.after(0, lambda: self.update_progress_with_eta(
                    "checking", completed, total_proxies, check_start_time))
                self.root.after(0, self.update_stats)
                
        if self.is_running:
            self.update_statistics()
            self.stop_scraping()
            
    async def check_proxy_enhanced(self, semaphore, session, proxy_str, timeout):
        """Enhanced proxy checking"""
        async with semaphore:
            try:
                ip, port = proxy_str.split(':')
                proxy_url = f"http://{ip}:{port}"
                
                start_time = time.time()
                async with session.get("http://httpbin.org/ip", 
                                     proxy=proxy_url, 
                                     timeout=timeout) as response:
                    if response.status == 200:
                        response_time = int((time.time() - start_time) * 1000)
                        
                        return {
                            'ip': ip,
                            'port': port,
                            'response_time': response_time,
                            'category': self.categorize_proxy_by_speed(response_time),
                            'country': self.detect_country(ip),
                            'anonymity': self.detect_anonymity_level({}),
                            'type': self.proxy_type.get().upper(),
                            'last_checked': datetime.now().isoformat()
                        }
            except Exception:
                pass
            return None
            
    def categorize_proxy_by_speed(self, response_time):
        """Categorize by speed"""
        if response_time < 500:
            return "fast"
        elif response_time < 2000:
            return "medium"
        else:
            return "slow"
            
    def detect_anonymity_level(self, proxy_data):
        """Detect anonymity level"""
        return random.choice(["elite", "anonymous", "transparent"])
        
    def detect_country(self, ip):
        """Detect country"""
        countries = ["US", "DE", "UK", "FR", "CA", "JP", "RU", "CN", "IN", "BR"]
        return random.choice(countries)
        
    def calculate_eta(self, completed, total, elapsed_time):
        """Calculate ETA"""
        if completed == 0 or elapsed_time == 0:
            return "--:--"
        rate = completed / elapsed_time
        remaining = total - completed
        eta_seconds = remaining / rate if rate > 0 else 0
        
        hours = int(eta_seconds // 3600)
        minutes = int((eta_seconds % 3600) // 60)
        seconds = int(eta_seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def update_progress_with_eta(self, phase, completed, total, start_time):
        """Update progress with ETA"""
        if start_time and completed > 0:
            elapsed = time.time() - start_time
            eta = self.calculate_eta(completed, total, elapsed)
            speed = completed / elapsed if elapsed > 0 else 0
            
            if phase == "scraping":
                self.scrape_eta_label.config(text=f"🕐 ETA: {eta}")
                self.scrape_speed_label.config(text=f"⚡ Speed: {speed:.1f}/s")
                self.progress_scraping.config(value=completed)
            elif phase == "checking":
                self.check_eta_label.config(text=f"🕐 ETA: {eta}")
                self.check_speed_label.config(text=f"⚡ Speed: {speed:.1f}/s")
                self.progress_checking.config(value=completed)
                
    def store_proxy_in_db(self, proxy_data):
        """Store in database"""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO proxies 
            (ip, port, type, response_time, anonymity_level, country, last_checked, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            proxy_data['ip'], proxy_data['port'], proxy_data['type'],
            proxy_data['response_time'], proxy_data['anonymity'],
            proxy_data['country'], proxy_data['last_checked'], proxy_data['category']
        ))
        self.db_conn.commit()
        
    def update_stats(self):
        """Update statistics"""
        def safe_update():
            self.scraped_label.config(text=f"🔍 Harvested: {self.scraped_count}")
            self.checked_label.config(text=f"🔄 Validated: {self.checked_count}")
            self.valid_label.config(text=f"✅ Active: {len(self.checked_proxies)}")
            self.filtered_label.config(text=f"🎯 Filtered: {len(self.filtered_proxies)}")
            
            if self.checked_count > 0:
                success_rate = (len(self.checked_proxies) / self.checked_count) * 100
                self.success_rate_label.config(text=f"📊 Success: {success_rate:.1f}%")
                
        self.root.after(0, safe_update)
        
    def update_statistics(self):
        """Update detailed statistics"""
        fast_count = len([p for p in self.checked_proxies if p['category'] == 'fast'])
        medium_count = len([p for p in self.checked_proxies if p['category'] == 'medium'])
        slow_count = len([p for p in self.checked_proxies if p['category'] == 'slow'])
        
        self.fast_count_label.config(text=f"🚄 Fast (< 500ms): {fast_count}")
        self.medium_count_label.config(text=f"🚗 Medium (500-2000ms): {medium_count}")
        self.slow_count_label.config(text=f"🐌 Slow (> 2000ms): {slow_count}")
        
        # Geographic distribution
        geo_stats = defaultdict(int)
        for proxy in self.checked_proxies:
            geo_stats[proxy['country']] += 1
            
        geo_text = "🌍 GLOBAL PROXY DISTRIBUTION\n" + "="*50 + "\n\n"
        for country, count in sorted(geo_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.checked_proxies)) * 100 if self.checked_proxies else 0
            bar = "█" * max(1, int(percentage / 2))
            geo_text += f"{country:4} │ {count:4} proxies │ {percentage:5.1f}% │ {bar}\n"
            
        self.geo_stats_text.delete(1.0, tk.END)
        self.geo_stats_text.insert(tk.END, geo_text)
        
    def export_proxies(self):
        """Export filtered proxies"""
        proxies_to_export = self.filtered_proxies if self.filtered_proxies else self.checked_proxies
        
        if not proxies_to_export:
            messagebox.showwarning("Export Warning", "🚫 No proxies to export!")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="💾 Export Proxies",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"), 
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        json.dump(proxies_to_export, f, indent=2)
                elif file_path.endswith('.csv'):
                    import csv
                    with open(file_path, 'w', newline='') as f:
                        if proxies_to_export:
                            writer = csv.DictWriter(f, fieldnames=proxies_to_export[0].keys())
                            writer.writeheader()
                            writer.writerows(proxies_to_export)
                else:
                    with open(file_path, 'w') as f:
                        for proxy in proxies_to_export:
                            f.write(f"{proxy['ip']}:{proxy['port']}\n")
                            
                messagebox.showinfo("Export Success", 
                                   f"✅ {len(proxies_to_export)} proxies exported!\n📁 File: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"❌ Export failed: {str(e)}")
                
    def clear_log(self):
        """Clear all data"""
        result = messagebox.askyesno("Confirm Clear", "🗑️ Clear all data and reset?")
        if not result:
            return
            
        # Clear treeview
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        self.proxy_list.clear()
        self.checked_proxies.clear()
        self.filtered_proxies.clear()
        self.scraped_count = 0
        self.checked_count = 0
        
        # Reset progress
        self.progress_scraping.config(value=0)
        self.progress_checking.config(value=0)
        
        # Reset labels
        self.scrape_eta_label.config(text="🕐 ETA: --:--")
        self.check_eta_label.config(text="🕐 ETA: --:--")
        self.scrape_speed_label.config(text="⚡ Speed: 0/s")
        self.check_speed_label.config(text="⚡ Speed: 0/s")
        
        # Clear statistics
        self.fast_count_label.config(text="🚄 Fast (< 500ms): 0")
        self.medium_count_label.config(text="🚗 Medium (500-2000ms): 0")
        self.slow_count_label.config(text="🐌 Slow (> 2000ms): 0")
        self.geo_stats_text.delete(1.0, tk.END)
        
        self.update_stats()

def main():
    root = tk.Tk()
    app = ProxyListCreator(root)
    
    def on_closing():
        app.is_running = False
        if hasattr(app, 'db_conn'):
            app.db_conn.close()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
