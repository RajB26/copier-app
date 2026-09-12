import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FastCopierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast File Copier")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        
        self.total_bytes = 0
        self.copied_bytes = 0
        self.last_update_time = 0

        self.setup_ui()

    def setup_ui(self):
        # Source Selection
        tk.Label(self.root, text="Source Folder:").pack(anchor="w", padx=20, pady=(15, 0))
        src_frame = tk.Frame(self.root)
        src_frame.pack(fill="x", padx=20, pady=5)
        tk.Entry(src_frame, textvariable=self.source_dir, width=45).pack(side="left")
        tk.Button(src_frame, text="Browse", command=self.select_source).pack(side="right")

        # Destination Selection
        tk.Label(self.root, text="Destination Folder:").pack(anchor="w", padx=20, pady=(10, 0))
        dest_frame = tk.Frame(self.root)
        dest_frame.pack(fill="x", padx=20, pady=5)
        tk.Entry(dest_frame, textvariable=self.dest_dir, width=45).pack(side="left")
        tk.Button(dest_frame, text="Browse", command=self.select_dest).pack(side="right")

        # Progress Bar and Status
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, length=460)
        self.progress_bar.pack(pady=(20, 5))

        self.status_label = tk.Label(self.root, text="Waiting for input...", fg="gray")
        self.status_label.pack()

        # Copy Button
        self.copy_btn = tk.Button(self.root, text="Start Copying", bg="#4CAF50", fg="white", 
                                  font=("Arial", 10, "bold"), command=self.start_copy_thread)
        self.copy_btn.pack(pady=15)

    def select_source(self):
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder: self.source_dir.set(folder)

    def select_dest(self):
        folder = filedialog.askdirectory(title="Select Destination Folder")
        if folder: self.dest_dir.set(folder)

    def start_copy_thread(self):
        src = self.source_dir.get().strip()
        dest = self.dest_dir.get().strip()

        if not os.path.exists(src) or not os.path.exists(dest):
            messagebox.showwarning("Error", "Please select valid source and destination folders.")
            return
        if src == dest:
            messagebox.showwarning("Error", "Source and destination cannot be the same.")
            return

        self.copy_btn.config(state="disabled", bg="gray")
        self.status_label.config(text="Scanning files... Please wait.", fg="blue")
        self.progress_var.set(0)

        threading.Thread(target=self.execute_copy, args=(src, dest), daemon=True).start()

    def update_ui(self):
        if self.total_bytes > 0:
            percent = (self.copied_bytes / self.total_bytes) * 100
            self.progress_var.set(percent)
            self.status_label.config(text=f"Copying... {percent:.1f}%")

    def execute_copy(self, src, dest):
        try:
            # 1. Scan all files to determine exact total size
            files_to_copy = []
            total_size = 0
            for root_dir, _, files in os.walk(src):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    files_to_copy.append(file_path)
                    total_size += os.path.getsize(file_path)

            if total_size == 0:
                self.root.after(0, self.finish_copy, True, "No files found to copy.")
                return

            self.total_bytes = total_size
            self.copied_bytes = 0
            self.last_update_time = time.time()

            # 2. Copy files in chunks
            folder_name = os.path.basename(os.path.normpath(src))
            target_dest_root = os.path.join(dest, folder_name)

            for src_file in files_to_copy:
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(target_dest_root, rel_path)

                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # 4MB chunks for optimal speed and accurate progress tracking
                with open(src_file, 'rb') as fsrc, open(dst_file, 'wb') as fdst:
                    while True:
                        chunk = fsrc.read(4 * 1024 * 1024)
                        if not chunk:
                            break
                        fdst.write(chunk)
                        self.copied_bytes += len(chunk)

                        now = time.time()
                        if now - self.last_update_time > 0.1:
                            self.last_update_time = now
                            self.root.after(0, self.update_ui)

                shutil.copystat(src_file, dst_file)

            self.root.after(0, self.update_ui)
            self.root.after(0, self.finish_copy, True, "Transfer completed successfully!")

        except Exception as e:
            self.root.after(0, self.finish_copy, False, str(e))

    def finish_copy(self, success, message):
        self.copy_btn.config(state="normal", bg="#4CAF50")
        if success:
            self.status_label.config(text="Done!", fg="green")
            messagebox.showinfo("Success", message)
        else:
            self.status_label.config(text="Error occurred.", fg="red")
            messagebox.showerror("Transfer Error", f"An error occurred:\n{message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FastCopierApp(root)
    root.mainloop()
