# THIS COMES IN 2 PARTS, 1 IS THE BOT AND THE OTHER IS THE CLOUD 
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import tweepy
import sqlite3
import threading
import datetime
import time
import os

# --- CONFIGURATION & CONSTANTS ---
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# !!! SECURITY WARNING: HARDCODING KEYS IS EXTREMELY DANGEROUS !!!
# This configuration is used for demonstration ONLY. For any real-world 
# application, you MUST use environment variables or a secure vault 
# to protect these sensitive credentials from accidental exposure.

# You MUST replace these placeholder strings with your actual credentials.
API_KEY = ''
API_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_SECRET = ''
BEARER_TOKEN = ''

# Initialize the Tweepy Client for V2 API endpoints (Posting, Retweeting, DMs)
# This client requires OAuth 1.0a User Context for write operations.


class DatabaseManager:
    def __init__(self, db_name='scheduler.db'):
        self.db_name = db_name
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _create_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                run_at TEXT NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                status TEXT DEFAULT 'PENDING'
            )
        """)
        conn.commit()
        conn.close()

    def add_task(self, content, run_at, is_recurring=False):
        conn = self._get_connection()
        conn.execute("INSERT INTO tasks (content, run_at, is_recurring) VALUES (?, ?, ?)", 
                     (content, run_at.isoformat(), 1 if is_recurring else 0))
        conn.commit()
        conn.close()

    def get_pending_tasks(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status='PENDING' ORDER BY run_at ASC")
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def mark_completed(self, task_id):
        conn = self._get_connection()
        conn.execute("UPDATE tasks SET status='COMPLETED' WHERE id=?", (task_id,))
        conn.commit()
        conn.close()
        
    def delete_task(self, task_id):
        conn = self._get_connection()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

# --- BACKGROUND WORKER (THE CLOUD ROBOT) ---
class BackgroundWorker(threading.Thread):
    def __init__(self, db, client):
        super().__init__()
        self.db = db
        self.client = client
        self.daemon = True
        self.running = True

    def run(self):
        print("--- SCHEDULER STARTED ---")
        while self.running:
            try:
                tasks = self.db.get_pending_tasks()
                now = datetime.datetime.now()
                
                for task in tasks:
                    # task format: (id, content, run_at, is_recurring, status)
                    task_id, content, run_at_str, is_recurring, status = task
                    run_at = datetime.datetime.fromisoformat(run_at_str)

                    if now >= run_at:
                        print(f"Executing Task {task_id}...")
                        try:
                            # ATTEMPT POST
                            self.client.create_tweet(text=content)
                            print(f"SUCCESS: Posted '{content}'")
                            
                            if is_recurring:
                                # Schedule for tomorrow
                                next_run = run_at + datetime.timedelta(days=1)
                                self.db.add_task(content, next_run, True)
                                self.db.mark_completed(task_id) # Mark old one done
                            else:
                                self.db.mark_completed(task_id)
                                
                        except Exception as e:
                            print(f"FAILED: {e}")
                            
            except Exception as e:
                print(f"Scheduler Error: {e}")
            
            time.sleep(10) # Check every 10 seconds

# --- THE SUPER NICE GUI ---
class ModernTwitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # API Setup
        self.setup_api()
        self.db = DatabaseManager()
        
        # Start Background Thread (Simulates Cloud behavior locally)
        self.worker = BackgroundWorker(self.db, self.client)
        self.worker.start()

        # Window Setup
        self.title("X Cloud Scheduler")
        self.geometry("900x600")
        
        # Grid Layout (1x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="X Scheduler", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_compose = ctk.CTkButton(self.sidebar_frame, text="Compose Tweet", command=self.show_compose)
        self.btn_compose.grid(row=2, column=0, padx=20, pady=10)

        self.btn_queue = ctk.CTkButton(self.sidebar_frame, text="View Queue", command=self.show_queue)
        self.btn_queue.grid(row=3, column=0, padx=20, pady=10)

        # --- MAIN CONTENT AREA ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Show default view
        self.show_dashboard()

    def setup_api(self):
        try:
            self.client = tweepy.Client(
                bearer_token=BEARER_TOKEN,
                consumer_key=API_KEY,
                consumer_secret=API_SECRET,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_SECRET
            )
        except:
            print("API Init failed - Placeholder Mode")
            # Dummy client for GUI testing without keys
            class Dummy: 
                def create_tweet(self, text): pass
            self.client = Dummy()

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- VIEW: DASHBOARD ---
    def show_dashboard(self):
        self.clear_main_frame()
        
        # Header
        ctk.CTkLabel(self.main_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Info Card
        card = ctk.CTkFrame(self.main_frame)
        card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(card, text="System Status", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        
        status_text = "Running Locally"
        ctk.CTkLabel(card, text=f"• {status_text}", text_color="#2CC985").pack(anchor="w", padx=20, pady=(0,10))
        ctk.CTkLabel(card, text="• Database Connected", text_color="#2CC985").pack(anchor="w", padx=20, pady=(0,10))
        
        # Cloud Instruction
        info_box = ctk.CTkTextbox(self.main_frame, height=150, fg_color="transparent", text_color="gray")
        info_box.pack(fill="x", pady=20)
        info_box.insert("0.0", "HOW TO RUN WHEN PC IS OFF:\n\n1. Take this script and the 'scheduler.db' file.\n2. Upload them to PythonAnywhere.com (Free Tier).\n3. Run this script in a 'Bash Console' on the cloud.\n\nOnce running on the cloud, it will never stop!")
        info_box.configure(state="disabled")

    # --- VIEW: COMPOSE ---
    def show_compose(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Compose & Schedule", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Text Input
        self.tweet_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.tweet_text.pack(fill="x", pady=(0, 20))
        self.tweet_text.insert("0.0", "What's happening?")
        
        # Time Inputs
        time_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(time_frame, text="Delay:").pack(side="left", padx=(0, 10))
        
        # Expanded slider to 1440 mins (24 hours)
        self.slider = ctk.CTkSlider(time_frame, from_=0, to=1440, number_of_steps=96)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.slider.set(10) # Default 10 mins
        
        self.lbl_minutes = ctk.CTkLabel(time_frame, text="10 mins")
        self.lbl_minutes.pack(side="left", padx=10)
        
        # Daily Checkbox
        self.chk_daily = ctk.CTkCheckBox(self.main_frame, text="Repeat Daily")
        self.chk_daily.pack(anchor="w", pady=(0, 20))
        
        # Update label on slider drag (Format: Xh Ym)
        def slider_event(value):
            mins = int(value)
            if mins < 60:
                self.lbl_minutes.configure(text=f"{mins} mins")
            else:
                hrs = mins // 60
                m = mins % 60
                self.lbl_minutes.configure(text=f"{hrs}h {m}m")
        self.slider.configure(command=slider_event)

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="Post Now", fg_color="#1DA1F2", command=self.post_now).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Schedule", fg_color="#888888", command=self.schedule_tweet).pack(side="left")

    def post_now(self):
        content = self.tweet_text.get("1.0", "end-1c")
        try:
            self.client.create_tweet(text=content)
            messagebox.showinfo("Success", "Tweet Sent!")
            self.tweet_text.delete("1.0", "end")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def schedule_tweet(self):
        content = self.tweet_text.get("1.0", "end-1c")
        minutes = int(self.slider.get())
        run_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        is_recurring = self.chk_daily.get()
        
        self.db.add_task(content, run_at, is_recurring)
        
        rec_msg = " (Daily)" if is_recurring else ""
        messagebox.showinfo("Scheduled", f"Tweet saved to DB!{rec_msg}\nWill run at {run_at.strftime('%Y-%m-%d %H:%M')}")

    # --- VIEW: QUEUE ---
    def show_queue(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Scheduled Queue", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))

        # Refresh Button
        ctk.CTkButton(self.main_frame, text="Refresh List", command=self.show_queue, width=100).pack(anchor="e", pady=(0, 10))

        # List of Tasks
        tasks = self.db.get_pending_tasks()
        
        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True)
        
        if not tasks:
            ctk.CTkLabel(scroll, text="No pending tweets.").pack(pady=20)
        
        for task in tasks:
            # task: id, content, run_at, is_rec, status
            task_frame = ctk.CTkFrame(scroll)
            task_frame.pack(fill="x", pady=5)
            
            run_time = datetime.datetime.fromisoformat(task[2]).strftime("%Y-%m-%d %H:%M")
            is_recurring = task[3]
            
            # Add label if daily
            time_display = f"{run_time} [Daily]" if is_recurring else run_time
            
            ctk.CTkLabel(task_frame, text=time_display, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(task_frame, text=task[1][:30]+"...").pack(side="left", padx=10)
            
            ctk.CTkButton(task_frame, text="Delete", width=60, fg_color="#FF4444", 
                          command=lambda t_id=task[0]: self.delete_task_ui(t_id)).pack(side="right", padx=10, pady=5)

    def delete_task_ui(self, task_id):
        self.db.delete_task(task_id)
        self.show_queue() # Refresh

if __name__ == "__main__":
    app = ModernTwitterApp()
    app.mainloop()
