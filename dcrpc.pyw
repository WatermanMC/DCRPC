import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
import threading
from pypresence import Presence

CONFIG_FILE = os.path.expanduser("~/.discord_rpc_img.json")

class DCRPC:
    def __init__(self, root):
        self.root = root
        self.root.title("DCRPC")
        self.root.geometry("500x420")
        self.root.resizable(False, False)
        
        self.rpc = None
        self.app_id = None
        
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill="both", expand=True)
        
        ttk.Label(main, text="Application ID:").grid(row=0, column=0, sticky="w", pady=3)
        self.app_id_entry = ttk.Entry(main, width=40)
        self.app_id_entry.grid(row=0, column=1, pady=3)
        
        ttk.Label(main, text="Playing:").grid(row=1, column=0, sticky="w", pady=3)
        self.details_entry = ttk.Entry(main, width=40)
        self.details_entry.grid(row=1, column=1, pady=3)
        
        ttk.Label(main, text="Extra info:").grid(row=2, column=0, sticky="w", pady=3)
        self.state_entry = ttk.Entry(main, width=40)
        self.state_entry.grid(row=2, column=1, pady=3)
        
        ttk.Label(main, text="Large Image Key:").grid(row=3, column=0, sticky="w", pady=3)
        self.image_key_entry = ttk.Entry(main, width=40)
        self.image_key_entry.grid(row=3, column=1, pady=3)
        
        ttk.Label(main, text="Image Hover Text:").grid(row=4, column=0, sticky="w", pady=3)
        self.image_text_entry = ttk.Entry(main, width=40)
        self.image_text_entry.grid(row=4, column=1, pady=3)
        
        button_frame = ttk.Frame(main)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)
        
        self.update_btn = ttk.Button(button_frame, text="Set Status", command=self.update_status)
        self.update_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(main, text="Status: Not connected", foreground="red")
        self.status_label.grid(row=6, column=0, columnspan=2)
        
        help_text = "Image Key = asset name from Discord Developer Portal > Rich Presence > Art Assets"
        ttk.Label(main, text=help_text, wraplength=450, foreground="gray").grid(row=7, column=0, columnspan=2, pady=5)

        instruct = "Remove your status by closing this program or change your status by filling the fields and clicking 'Set Status' again."
        ttk.Label(main, text=instruct, wraplength=450, foreground="gray").grid(row=8, column=0, columnspan=2, pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_status(self):
        app_id_text = self.app_id_entry.get().strip()
        if not app_id_text:
            messagebox.showerror("Error", "Application ID required")
            return
        
        try:
            app_id = int(app_id_text)
        except ValueError:
            messagebox.showerror("Error", "Application ID must be a number")
            return
        
        details = self.details_entry.get().strip()
        state = self.state_entry.get().strip()
        image_key = self.image_key_entry.get().strip()
        image_text = self.image_text_entry.get().strip()
        
        if not details and not state and not image_key:
            messagebox.showwarning("Warning", "Fill at least one field")
            return
        
        threading.Thread(target=self._set_rpc, args=(app_id, details, state, image_key, image_text), daemon=True).start()
    
    def remove_status(self):
        """Force clear presence by sending empty update then disconnect"""
        def _remove():
            try:
                if self.rpc:
                    self.rpc.update(
                        details="",
                        state="",
                        large_image="",
                        large_text="",
                        small_image="",
                        small_text="",
                        start=None,
                        end=None
                    )
                    time.sleep(0.5)
                    self.rpc.close()
                    self.rpc = None
                    self.app_id = None
                    self._update_status_label("Status cleared", "orange")
                else:
                    self._update_status_label("Not connected", "red")
            except Exception as e:
                self._update_status_label(f"Error: {e}", "red")
                messagebox.showerror("Clear Error", str(e))
        
        threading.Thread(target=_remove, daemon=True).start()
    
    def _set_rpc(self, app_id, details, state, image_key, image_text):
        try:
            # Reconnect if needed
            if self.rpc is None or self.app_id != app_id:
                if self.rpc:
                    self.rpc.close()
                self.rpc = Presence(app_id)
                self.rpc.connect()
                self.app_id = app_id
                self._update_status_label("Connected", "green")
            
            activity = {"start": int(time.time())}
            if details:
                activity["details"] = details
            if state:
                activity["state"] = state
            if image_key:
                activity["large_image"] = image_key
                if image_text:
                    activity["large_text"] = image_text
            
            self.rpc.update(**activity)
            self._update_status_label("Status set!", "green")
            self.root.after(2000, lambda: self._update_status_label("Connected", "green"))
            
        except Exception as e:
            self._update_status_label(f"Error: {e}", "red")
            messagebox.showerror("RPC Error", str(e))
    
    def _update_status_label(self, text, color):
        def _update():
            self.status_label.config(text=f"Status: {text}", foreground=color)
        self.root.after(0, _update)
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.app_id_entry.insert(0, data.get("app_id", ""))
                    self.details_entry.insert(0, data.get("details", ""))
                    self.state_entry.insert(0, data.get("state", ""))
                    self.image_key_entry.insert(0, data.get("image_key", ""))
                    self.image_text_entry.insert(0, data.get("image_text", ""))
            except:
                pass
    
    def save_config(self):
        data = {
            "app_id": self.app_id_entry.get().strip(),
            "details": self.details_entry.get().strip(),
            "state": self.state_entry.get().strip(),
            "image_key": self.image_key_entry.get().strip(),
            "image_text": self.image_text_entry.get().strip()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def on_close(self):
        self.save_config()
        if self.rpc:
            try:
                self.rpc.update(details="", state="", large_image="")
                time.sleep(0.5)
                self.rpc.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DCRPC(root)
    root.mainloop()
