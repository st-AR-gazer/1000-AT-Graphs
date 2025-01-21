import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

def run_selected_script():
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("No selection", "Please select a script first.")
        return
    index = selection[0]
    chosen_script = scripts[index]
    try:
        subprocess.run([sys.executable, os.path.join(scripts_dir, chosen_script)])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        messagebox.showerror("Error", str(e))

def main():
    global scripts, scripts_dir, listbox
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, 'scripts')
    if not os.path.isdir(scripts_dir):
        messagebox.showerror("Error", f"No 'scripts' directory found in:\n{scripts_dir}")
        return
    scripts = sorted([f for f in os.listdir(scripts_dir) if f.endswith('.py')])
    if not scripts:
        messagebox.showerror("Error", f"No .py scripts found in:\n{scripts_dir}")
        return

    root = tk.Tk()
    root.title("Script Runner")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    label = tk.Label(frame, text="Select a script to run:")
    label.pack()

    listbox = tk.Listbox(frame, width=50, height=8)
    listbox.pack(pady=5)
    for script in scripts:
        listbox.insert(tk.END, script)

    run_button = tk.Button(frame, text="Run Script", command=run_selected_script)
    run_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
