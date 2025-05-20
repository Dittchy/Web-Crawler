import threading
import queue
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cpuinfo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WebCrawler:
    def __init__(self):
        self.url_queue = queue.Queue()
        self.visited_urls = set()
        self.visited_lock = threading.Lock()
        self.crawler_running = False
        self.setup_ui()
        self.setup_stats()

    def setup_ui(self):
        """Initialize the modern UI components"""
        self.root = tk.Tk()
        self.root.title("SpiderBot - Modern Web Crawler")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")

        # Custom style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # Main container
        self.main_frame = ttk.Frame(self.root, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Setup UI sections
        self.create_control_panel()
        self.create_stats_panel()
        self.create_url_table()
        self.create_log_panel()

    def configure_styles(self):
        """Define modern color scheme and styles"""
        colors = {
            "background": "#1a1a1a",
            "foreground": "#ffffff",
            "accent": "#00ff9d",
            "panel": "#2d2d2d",
            "hover": "#3d3d3d"
        }

        self.style.configure('.', background=colors["background"], foreground=colors["foreground"])
        self.style.configure('TFrame', background=colors["background"])
        self.style.configure('TLabel', background=colors["background"], foreground=colors["accent"],
                             font=('Segoe UI', 10))
        self.style.configure('TButton', background=colors["panel"], foreground=colors["foreground"],
                             font=('Segoe UI', 10), borderwidth=1)
        self.style.map('TButton',
                       background=[('active', colors["hover"]), ('disabled', colors["background"])])
        self.style.configure('TEntry', fieldbackground=colors["panel"],
                             foreground=colors["foreground"], insertcolor=colors["foreground"])
        self.style.configure('Treeview', background=colors["panel"], fieldbackground=colors["panel"],
                             foreground=colors["foreground"])
        self.style.configure('Treeview.Heading', background=colors["hover"],
                             font=('Segoe UI', 10, 'bold'))
        self.style.configure('Vertical.TScrollbar', background=colors["hover"])

    def create_control_panel(self):
        """Create input controls section"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Crawler Settings", padding=10)
        control_frame.pack(fill=tk.X, pady=5)

        # Input fields grid
        entries = [
            ("Start URL:", "start_url", "https://example.com"),
            ("Max Threads:", "max_threads", str(min(cpuinfo.get_cpu_info().get('count', 4), 8))),
            ("Delay (s):", "politeness_delay", "1.0"),
            ("Storage File:", "storage_file", "crawled_urls.csv")
        ]

        for row, (label, name, default) in enumerate(entries):
            ttk.Label(control_frame, text=label).grid(row=row, column=0, padx=5, pady=3, sticky="e")
            entry = ttk.Entry(control_frame, width=40)
            entry.insert(0, default)
            setattr(self, f"{name}_entry", entry)
            entry.grid(row=row, column=1, padx=5, pady=3, sticky="ew")

        # Checkbox and buttons
        self.restrict_domain = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Stay on Domain",
                        variable=self.restrict_domain).grid(row=4, column=1, sticky="w")

        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="▶ Start Crawl", command=self.start_crawler).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_crawler).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 Clear Data", command=self.clear_storage).pack(side=tk.LEFT, padx=5)

    def create_stats_panel(self):
        """Create statistics display"""
        self.stats_frame = ttk.Frame(self.main_frame)
        self.stats_frame.pack(fill=tk.X, pady=10)

        stats = [
            ("Queued URLs:", "queue_count"),
            ("Visited URLs:", "visited_count"),
            ("Status:", "current_status")
        ]

        for col, (label, var_name) in enumerate(stats):
            ttk.Label(self.stats_frame, text=label).grid(row=0, column=col * 2, padx=5)
            label_var = tk.StringVar(value="0")
            setattr(self, var_name, label_var)
            ttk.Label(self.stats_frame, textvariable=label_var,
                      font=('Segoe UI', 10, 'bold')).grid(row=0, column=col * 2 + 1, padx=5, sticky="w")

    def create_url_table(self):
        """Create results table with scrollbar"""
        table_frame = ttk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.url_table = ttk.Treeview(table_frame, columns=('URL', 'Timestamp', 'Status'),
                                      show='headings', selectmode='extended')
        for col, heading in [('URL', 700), ('Timestamp', 200), ('Status', 80)]:
            self.url_table.heading(col, text=col)
            self.url_table.column(col, width=heading, anchor='w' if col == 'URL' else 'center')

        scrollbar = ttk.Scrollbar(table_frame, command=self.url_table.yview)
        self.url_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.url_table.pack(fill=tk.BOTH, expand=True)

    def create_log_panel(self):
        """Create logging output area"""
        log_frame = ttk.LabelFrame(self.main_frame, text="Crawler Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, bg="#2d2d2d", fg="#ffffff",
                                                  insertbackground="#ffffff", wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def setup_stats(self):
        """Initialize statistics variables"""
        self.queue_count.set("0")
        self.visited_count.set("0")
        self.current_status.set("Idle")

    def update_stats(self):
        """Periodically update UI statistics"""
        if self.crawler_running:
            self.queue_count.set(str(self.url_queue.qsize()))
            self.visited_count.set(str(len(self.visited_urls)))
            self.root.after(500, self.update_stats)

    def crawl_page(self, url):
        """Fetch and parse a single webpage"""
        try:
            response = requests.get(url, timeout=5, headers={'User-Agent': 'SpiderBot/2.0'})
            status = response.status_code
            if status != 200:
                return [], status

            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = urlparse(url).netloc if self.restrict_domain.get() else None
            links = []

            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                parsed = urlparse(full_url)

                if (not base_domain or parsed.netloc == base_domain) and parsed.scheme in ('http', 'https'):
                    links.append(full_url)

            return links, status
        except Exception as e:
            self.log(f"Error crawling {url}: {str(e)}")
            return [], 0

    def worker(self):
        """Process URLs from the queue"""
        while self.crawler_running:
            try:
                url = self.url_queue.get(timeout=2)

                with self.visited_lock:
                    if url in self.visited_urls:
                        self.url_queue.task_done()
                        continue
                    self.visited_urls.add(url)

                links, status = self.crawl_page(url)
                self.save_url(url, status)

                with self.visited_lock:
                    for link in links:
                        if link not in self.visited_urls:
                            self.url_queue.put(link)

                time.sleep(float(self.politeness_delay_entry.get()))
                self.url_queue.task_done()

            except queue.Empty:
                break
            except Exception as e:
                self.log(f"Worker error: {str(e)}")
                self.url_queue.task_done()

    def save_url(self, url, status):
        """Save crawled URL to CSV and update UI"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_exists = os.path.exists(self.storage_file_entry.get())

            with open(self.storage_file_entry.get(), 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['URL', 'Timestamp', 'Status'])
                writer.writerow([url, timestamp, status])

            self.url_table.insert('', 'end', values=(url, timestamp, status))
            self.url_table.yview_moveto(1)
            self.log(f"Crawled: {url} (Status: {status})")
        except Exception as e:
            self.log(f"Error saving {url}: {str(e)}")

    def load_urls(self):
        """Load previously crawled URLs from storage"""
        try:
            filename = self.storage_file_entry.get()
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if row:
                            self.visited_urls.add(row[0])
                            self.url_table.insert('', 'end', values=row)
                self.log(f"Loaded {len(self.visited_urls)} URLs from storage")
        except Exception as e:
            self.log(f"Error loading URLs: {str(e)}")

    def start_crawler(self):
        """Start crawling process with validation"""
        try:
            if self.crawler_running:
                messagebox.showinfo("Info", "Crawler is already running")
                return

            # Input validation
            start_url = self.start_url_entry.get().strip()
            if not start_url.startswith(('http://', 'https://')):
                messagebox.showerror("Error", "Invalid URL - must start with http:// or https://")
                return

            try:
                max_threads = int(self.max_threads_entry.get())
                if not 1 <= max_threads <= 16:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Max threads must be 1-16")
                return

            try:
                delay = float(self.politeness_delay_entry.get())
                if delay < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Delay must be ≥0")
                return

            # Initialize crawling
            self.crawler_running = True
            self.current_status.set("Running")
            self.url_queue.queue.clear()
            self.url_queue.put(start_url)
            self.load_urls()

            # Start worker threads
            for _ in range(max_threads):
                thread = threading.Thread(target=self.worker, daemon=True)
                thread.start()

            self.update_stats()
            self.log("Crawler started successfully")

        except Exception as e:
            self.log(f"Startup error: {str(e)}")
            messagebox.showerror("Error", f"Failed to start crawler: {str(e)}")

    def stop_crawler(self):
        """Stop crawling gracefully"""
        if self.crawler_running:
            self.crawler_running = False
            self.current_status.set("Stopped")
            self.log("Crawler stopping...")

    def clear_storage(self):
        """Reset all data and storage"""
        if messagebox.askyesno("Confirm", "Delete all crawled data?"):
            try:
                filename = self.storage_file_entry.get()
                if os.path.exists(filename):
                    os.remove(filename)
                self.visited_urls.clear()
                self.url_table.delete(*self.url_table.get_children())
                self.log("Storage cleared successfully")
                self.setup_stats()
            except Exception as e:
                self.log(f"Clear error: {str(e)}")

    def log(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.update_idletasks()

    def run(self):
        """Start application"""
        self.root.mainloop()


if __name__ == "__main__":
    crawler = WebCrawler()
    crawler.run()