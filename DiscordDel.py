#code created and modifyed by Ezcool Entities.
#python code that was used for the app. 
#works for anyone with python 3 and the Modules/Lib mentioned below.
#works for MACOS & Windows

import requests
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog as fd
import os
import sys
import subprocess
from PIL import Image, ImageTk, ImageDraw  # Added Pillow imports

class DeleteApp:
    def __init__(self, root):
        self.root = root
        root.title("Discord Message Deleter")
        root.geometry("900x850")
        root.resizable(False, False)

        # ------------------ Dynamic Icon & Links ------------------
        try:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            assets_dir = os.path.join(base_dir, "assets")

            # Main window icon
            icon_path = os.path.join(assets_dir, "red_discord.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
            else:
                print(f"Icon not found at {icon_path}, using default icon.")

            # Social buttons frame
            social_frame = tk.Frame(root, bg=root['bg'])
            social_frame.pack(side='top', anchor='ne', padx=10, pady=5)

            # ------------------ Function to make circular images ------------------
            def make_circle(image_path, size=(50, 50)):
                img = Image.open(image_path).convert("RGBA")
                img = img.resize(size, Image.Resampling.LANCZOS)  # high-quality resize
                mask = Image.new("L", img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
                img.putalpha(mask)
                return ImageTk.PhotoImage(img)

            # Helper function to create social button
            def create_social_button(image_path, url, size=(50,50)):
                if os.path.exists(image_path):
                    img = make_circle(image_path, size=size)
                    btn = tk.Button(
                        social_frame, image=img,
                        command=lambda: subprocess.Popen(['start', url], shell=True),
                        bd=0, highlightthickness=0,
                        relief='flat',
                        bg=root['bg'], activebackground=root['bg']
                    )
                    btn.image = img
                    btn.pack(side='left', padx=5)
                    return btn
                return None

            # GitHub button
            github_btn = create_social_button(
                os.path.join(assets_dir, "github.png"),
                "https://github.com/VSOLOCODING"
            )

            # YouTube button
            youtube_btn = create_social_button(
                os.path.join(assets_dir, "youtube.png"),
                "https://www.youtube.com/@ezcode2025"
            )

        except Exception as e:
            print(f"Failed to set icons/buttons: {e}")

        # ------------------ Variables ------------------
        self.token = None
        self.headers = None
        self.stop_flag = False
        self.thread = None

        self.deleted_count = 0
        self.messages_this_sec = 0
        self.last_update_time = time.time()
        self.error_count = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None

        # ------------------ Token Input ------------------
        token_frame = tk.Frame(root)
        token_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(token_frame, text="Your Discord Token:").pack(side='left')
        self.token_entry = tk.Entry(token_frame, show='*', width=80)
        self.token_entry.pack(side='left', padx=10)

        # ------------------ Tabs ------------------
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        self.dm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dm_frame, text="Delete DM Messages")
        self.build_dm_tab()

        self.server_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.server_frame, text="Delete Server Messages")
        self.build_server_tab()

        # ------------------ Rate Selection ------------------
        slider_frame = tk.Frame(root)
        slider_frame.pack(fill='x', padx=10, pady=(0, 10))
        tk.Label(slider_frame, text="Deletion Rate (messages/sec):").pack(side='left')
        rate_values = [round(x * 0.1, 1) for x in range(4, 10)] + list(range(1, 11))
        self.rate_var = tk.DoubleVar(value=3.0)
        self.rate_dropdown = ttk.Combobox(slider_frame, textvariable=self.rate_var, state="readonly", width=5)
        self.rate_dropdown['values'] = rate_values
        self.rate_dropdown.pack(side='left', padx=10)
        self.rate_display = tk.Label(slider_frame, text=f"{self.rate_var.get()} msg/sec")
        self.rate_display.pack(side='left')
        self.rate_var.trace("w", self.update_rate_display)

        # ------------------ Guide Section ------------------
        self.guide_label = tk.Label(root, text="Help will be displayed here for errors", fg="red", justify='left', wraplength=850)
        self.guide_label.pack(fill='x', padx=10, pady=(0,5))

        # ------------------ Logs Frame ------------------
        logs_frame = tk.Frame(root)
        logs_frame.pack(expand=True, fill='both', padx=10, pady=5)
        deleted_frame = tk.Frame(logs_frame)
        deleted_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        tk.Label(deleted_frame, text="Deleted Messages Log:").pack(anchor='w')
        self.log = scrolledtext.ScrolledText(deleted_frame, width=60, height=20, state='disabled')
        self.log.pack(fill='both', expand=True)
        error_frame = tk.Frame(logs_frame)
        error_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        tk.Label(error_frame, text="Error Log:").pack(anchor='w')
        self.error_log = scrolledtext.ScrolledText(error_frame, width=40, height=20, fg="red", state='disabled')
        self.error_log.pack(fill='both', expand=True)

        # ------------------ Controls ------------------
        controls_frame = tk.Frame(root)
        controls_frame.pack(fill='x', padx=10, pady=10)
        self.start_btn = tk.Button(controls_frame, text="Start", width=20, command=self.start_deleting_selected)
        self.start_btn.pack(side='left', padx=5)
        self.stop_btn = tk.Button(controls_frame, text="Stop", width=20, command=self.stop_deleting, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        self.save_log_btn = tk.Button(controls_frame, text="Save Logs", width=20, state='disabled', command=self.save_logs)
        self.save_log_btn.pack(side='left', padx=5)

        # ------------------ Stats ------------------
        stats_frame = tk.Frame(root)
        stats_frame.pack(fill='x', padx=10)
        self.deleted_label = tk.Label(stats_frame, text="Messages deleted: 0")
        self.deleted_label.pack(side='left', padx=(0,15))
        self.rate_label = tk.Label(stats_frame, text="Deleting speed: 0 msg/sec")
        self.rate_label.pack(side='left', padx=(0,15))
        self.left_label = tk.Label(stats_frame, text="Messages left: ?")
        self.left_label.pack(side='left', padx=(0,15))
        self.error_label = tk.Label(stats_frame, text="Errors: 0", fg="red")
        self.error_label.pack(side='left')

        # ------------------ Status & Progress ------------------
        status_frame = tk.Frame(root)
        status_frame.pack(fill='x', padx=10, pady=5)
        self.status_label = tk.Label(status_frame, text="Status: Idle")
        self.status_label.pack(side='left')
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side='right', fill='x', expand=True)

        # ------------------ Update Stats Loop ------------------
        self.update_stats()

    # ------------------ Methods ------------------
    def update_rate_display(self, *args):
        self.rate_display.config(text=f"{self.rate_var.get()} msg/sec")

    def build_dm_tab(self):
        frame = self.dm_frame
        tk.Label(frame, text="Target User ID:").pack(anchor='w', pady=(10, 2))
        self.dm_user_id_entry = tk.Entry(frame, width=30)
        self.dm_user_id_entry.pack(anchor='w')

    def build_server_tab(self):
        frame = self.server_frame
        tk.Label(frame, text="Server (Guild) ID:").pack(anchor='w', pady=(10, 2))
        self.server_id_entry = tk.Entry(frame, width=30)
        self.server_id_entry.pack(anchor='w')
        tk.Label(frame, text="Channel ID:").pack(anchor='w', pady=(10, 2))
        self.channel_id_entry = tk.Entry(frame, width=30)
        self.channel_id_entry.pack(anchor='w')

    # ------------------ Logging ------------------
    def log_message(self, message):
        self.log.configure(state='normal')
        self.log.insert(tk.END, message + '\n')
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def log_error(self, message):
        self.error_log.configure(state='normal')
        self.error_log.insert(tk.END, message + '\n')
        self.error_log.see(tk.END)
        self.error_log.configure(state='disabled')
        self.error_count += 1
        self.error_label.config(text=f"Errors: {self.error_count}")

        guide_text = ""

        if "400" in message:
            guide_text = "400 Bad Request: Check your request data and parameters."
        elif "401" in message:
            guide_text = "401 Unauthorized: Your token is invalid or expired."
        elif "403" in message:
            guide_text = "403 Forbidden: Make sure your token has correct permissions."
        elif "404" in message:
            guide_text = "404 Not Found: The target user/channel/message does not exist."
        elif "429" in message:
            guide_text = "429 Rate Limit: Slow down the deletion rate."
        elif "426" in message:
            guide_text = "426 Upgrade Required: Update API usage."
        elif "500" in message:
            guide_text = "500 Internal Server Error: Discord server issue, try again later."
        elif "502" in message:
            guide_text = "502 Bad Gateway: Discord server gateway error, try again later."
        elif "503" in message:
            guide_text = "503 Service Unavailable: Discord servers are temporarily down."
        elif "Failed to fetch messages" in message:
            guide_text = "Network/Error: Check internet connection and token validity."
        elif "Exception" in message:
            guide_text = "Unexpected error: Check token/permissions and logs."

        if guide_text:
            self.guide_label.config(text=f"Guide: {guide_text}")

    # ------------------ Start/Stop ------------------
    def start_deleting_selected(self):
        current_tab = self.notebook.index(self.notebook.select())
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter your Discord token.")
            return
        self.token = token
        self.headers = {'Authorization': self.token, 'User-Agent': 'Mozilla/5.0'}

        if current_tab == 0:
            target_user_id = self.dm_user_id_entry.get().strip()
            if not target_user_id:
                messagebox.showerror("Error", "Please enter the target User ID.")
                return
            self.target_user_id = target_user_id
            self.prepare_deletion(self.delete_dm_messages)
        else:
            server_id = self.server_id_entry.get().strip()
            channel_id = self.channel_id_entry.get().strip()
            if not server_id or not channel_id:
                messagebox.showerror("Error", "Please enter both Server ID and Channel ID.")
                return
            self.server_id = server_id
            self.channel_id = channel_id
            self.prepare_deletion(self.delete_server_messages)

    # ------------------ Prepare & Control ------------------
    def prepare_deletion(self, func):
        self.disable_buttons()
        self.reset_stats()
        self.clear_logs()
        self.save_log_btn.config(state='disabled')
        self.start_deleting(func)

    def disable_buttons(self):
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

    def enable_buttons(self):
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def clear_logs(self):
        self.log.configure(state='normal')
        self.log.delete('1.0', tk.END)
        self.log.configure(state='disabled')
        self.error_log.configure(state='normal')
        self.error_log.delete('1.0', tk.END)
        self.error_log.configure(state='disabled')
        self.guide_label.config(text="Guides will appear here for errors.")

    def start_deleting(self, target_function):
        self.stop_flag = False
        self.start_time = time.time()
        self.progress.start(10)
        self.status_label.config(text="Status: Starting...")
        self.thread = threading.Thread(target=target_function, daemon=True)
        self.thread.start()

    def stop_deleting(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to stop deleting?"):
            self.stop_flag = True
            self.end_time = time.time()
            self.status_label.config(text="Status: Stopping...")
            self.stop_btn.config(state='disabled')

    # ------------------ Stats ------------------
    def reset_stats(self):
        with self.lock:
            self.deleted_count = 0
            self.messages_this_sec = 0
            self.last_update_time = time.time()
            self.error_count = 0
            self.start_time = None
            self.end_time = None
        self.deleted_label.config(text="Messages deleted: 0")
        self.rate_label.config(text="Deleting speed: 0 msg/sec")
        self.left_label.config(text="Messages left: ?")
        self.error_label.config(text="Errors: 0")

    def update_stats(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update_time
            rate = self.messages_this_sec / elapsed if elapsed > 0 else 0
            self.deleted_label.config(text=f"Messages deleted: {self.deleted_count}")
            self.rate_label.config(text=f"Deleting speed: {rate:.2f} msg/sec")
            self.messages_this_sec = 0
            self.last_update_time = now
        self.root.after(1000, self.update_stats)

    # ------------------ Discord API ------------------
    def get_own_user_id(self):
        self.log_message("Fetching your user ID...")
        try:
            response = requests.get("https://discord.com/api/v9/users/@me", headers=self.headers)
            if response.status_code == 200:
                user_id = response.json()['id']
                self.log_message(f"Your user ID: {user_id}")
                return user_id
            else:
                self.log_error(f"❌ Failed to get user info: {response.status_code} {response.text}")
                return None
        except Exception as e:
            self.log_error(f"❌ Exception getting user ID: {e}")
            return None

    def get_dm_channel_id(self):
        self.log_message(f"Getting DM channel with user {self.target_user_id}...")
        try:
            response = requests.post(
                'https://discord.com/api/v9/users/@me/channels',
                headers=self.headers,
                json={'recipient_id': self.target_user_id}
            )
            if response.status_code == 200:
                channel_id = response.json()['id']
                self.log_message(f"DM channel ID: {channel_id}")
                return channel_id
            else:
                self.log_error(f"❌ Failed to get DM channel: {response.status_code} {response.text}")
                return None
        except Exception as e:
            self.log_error(f"❌ Exception getting DM channel: {e}")
            return None

    def delete_dm_messages(self):
        my_user_id = self.get_own_user_id()
        if not my_user_id: return self.finish_deleting()
        dm_channel_id = self.get_dm_channel_id()
        if not dm_channel_id: return self.finish_deleting()
        self.delete_messages_from_channel(dm_channel_id, my_user_id)
        self.finish_deleting()

    def delete_server_messages(self):
        my_user_id = self.get_own_user_id()
        if not my_user_id: return self.finish_deleting()
        self.delete_messages_from_channel(self.channel_id, my_user_id)
        self.finish_deleting()

    def delete_messages_from_channel(self, channel_id, my_user_id):
        deleted_count = 0
        last_message_id = None
        delay = 1.0 / float(self.rate_var.get())
        self.log_message(f"Starting deletion in channel {channel_id} at up to {self.rate_var.get()} msg/sec...\n")

        while not self.stop_flag:
            params = {'limit': 100}
            if last_message_id:
                params['before'] = last_message_id
            try:
                response = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages',
                                        headers=self.headers, params=params)
                if response.status_code == 429:
                    retry_after = response.json().get('retry_after', 5)
                    self.log_error(f"⚠️ Rate limit reached. Sleeping for {retry_after} seconds.")
                    time.sleep(retry_after)
                    continue
                if response.status_code != 200:
                    self.log_error(f"❌ Failed to fetch messages: {response.status_code} {response.text}")
                    break
                messages = response.json()
                if not messages:
                    self.log_message("No more messages found.")
                    break
                for message in messages:
                    if self.stop_flag: break
                    if str(message['author']['id']) == str(my_user_id):
                        try:
                            del_resp = requests.delete(
                                f"https://discord.com/api/v9/channels/{channel_id}/messages/{message['id']}",
                                headers=self.headers
                            )
                            if del_resp.status_code == 204:
                                deleted_count += 1
                                with self.lock:
                                    self.deleted_count += 1
                                    self.messages_this_sec += 1
                                content = message.get('content', '...')
                                truncated = (content[:50] + '...') if len(content) > 50 else content
                                self.log_message(f"✅ Deleted message ID: {message['id']} | Context: {truncated}")
                                time.sleep(delay)
                            else:
                                self.log_error(f"❌ Failed to delete message ID: {message['id']} - Status: {del_resp.status_code}")
                        except Exception as e:
                            self.log_error(f"❌ Exception deleting message ID {message['id']}: {e}")
                    last_message_id = message['id']
                time.sleep(0.3)
            except Exception as e:
                self.log_error(f"❌ Exception fetching messages: {e}")
                break
        self.log_message(f"\nFinished deleting messages. Total deleted: {deleted_count}")

    def finish_deleting(self):
        self.progress.stop()
        self.status_label.config(text="Status: Finished.")
        self.enable_buttons()
        self.save_log_btn.config(state='normal')
        self.end_time = time.time()
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.log_message(f"\n⏱ Total time taken: {duration:.2f} seconds")

    # ------------------ Save Logs ------------------
    def save_logs(self):
        deleted_log = self.log.get('1.0', tk.END)
        error_log = self.error_log.get('1.0', tk.END)
        file = fd.asksaveasfilename(defaultextension=".txt",
                                    filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                                    title="Save Logs As")
        if file:
            try:
                with open(file, "w", encoding='utf-8') as f:
                    f.write("Deleted Messages Log:\n")
                    f.write(deleted_log)
                    f.write("\n\nError Log:\n")
                    f.write(error_log)
                    f.write(f"\n\nTotal Errors: {self.error_count}")
                    if self.start_time and self.end_time:
                        duration = self.end_time - self.start_time
                        f.write(f"\nTotal Time Taken: {duration:.2f} seconds")
                messagebox.showinfo("Success", f"Logs saved to {file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DeleteApp(root)
    root.mainloop()
