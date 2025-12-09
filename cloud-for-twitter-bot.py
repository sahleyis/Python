import tweepy
import sqlite3
import threading
import datetime
import time
import os
import sys


API_KEY = ''
API_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_SECRET = ''
BEARER_TOKEN = ''


try:
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    print("API Client initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize Tweepy Client. Check API keys and permissions. Error: {e}")
    # Use a dummy client to prevent immediate crash if keys are placeholders,
    # but posting will still fail if keys are invalid.
    class Dummy: 
        def create_tweet(self, text):
            raise Exception("API Keys are not configured correctly.")
    client = Dummy()


# --- DATABASE MANAGER (The Librarian) ---
class DatabaseManager:
    def __init__(self, db_name='scheduler.db'):
        self.db_name = db_name
        self._create_table()
        print(f"Database connected at {self.db_name}")

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
        
    def add_task(self, content, run_at, is_recurring=False):
        # This is primarily used by the worker to schedule the *next* daily run.
        conn = self._get_connection()
        conn.execute("INSERT INTO tasks (content, run_at, is_recurring) VALUES (?, ?, ?)", 
                     (content, run_at.isoformat(), 1 if is_recurring else 0))
        conn.commit()
        conn.close()


# --- BACKGROUND WORKER (The Robot Butler) ---
class BackgroundWorker(threading.Thread):
    def __init__(self, db, client):
        super().__init__()
        self.db = db
        self.client = client
        self.daemon = True
        self.running = True

    def run(self):
        print("\n======================================")
        print(">>> X CLOUD SCHEDULER: STARTED <<<")
        print("======================================")
        
        while self.running:
            try:
                tasks = self.db.get_pending_tasks()
                now = datetime.datetime.now()
                
                if not tasks:
                     sys.stdout.write(".") # print a dot to show we are still alive
                     sys.stdout.flush()
                
                for task in tasks:
                    # task format: (id, content, run_at, is_recurring, status)
                    task_id, content, run_at_str, is_recurring, status = task
                    run_at = datetime.datetime.fromisoformat(run_at_str)

                    if now >= run_at:
                        print(f"\n[EXECUTION] Task ID {task_id} due at {run_at.strftime('%H:%M:%S')}")
                        try:
                            # ATTEMPT POST
                            response = self.client.create_tweet(text=content)
                            tweet_id = response.data['id']
                            print(f"SUCCESS: Posted ID {tweet_id} (Content: {content[:40]}...)")
                            
                            if is_recurring:
                                # Schedule next run and mark old one done
                                next_run = run_at + datetime.timedelta(days=1)
                                self.db.add_task(content, next_run, True)
                                self.db.mark_completed(task_id)
                                print(f"RECURRING: Next run scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                            else:
                                self.db.mark_completed(task_id)
                                
                        except Exception as e:
                            print(f"FAILED: X API Error for Task {task_id}. Error: {e}")
                            
            except Exception as e:
                print(f"CRITICAL SCHEDULER ERROR: {e}")
            
            time.sleep(10) # Check every 10 seconds

# --- Main Execution Block for Cloud Server ---
if __name__ == "__main__":
    db_manager = DatabaseManager()
    worker = BackgroundWorker(db_manager, client)
    
    try:
        worker.start()
        # Keep the main thread alive so the daemon worker thread can continue running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.running = False
        print("\n\nScheduler stopped by user (Keyboard Interrupt). Goodbye!")
        sys.exit(0)
