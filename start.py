import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, 'scripts')
    if not os.path.exists(scripts_dir) or not os.path.isdir(scripts_dir):
        print("No 'scripts' directory found.")
        return

    scripts = sorted([f for f in os.listdir(scripts_dir) if f.endswith('.py')])
    if not scripts:
        print("No .py scripts found in the 'scripts' directory.")
        return

    print("Available scripts in the 'scripts' directory:\n")
    for idx, script_name in enumerate(scripts, start=1):
        print(f"{idx}. {script_name}")

    try:
        choice = input("\nEnter the number of the script you want to run: ")
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(scripts):
            print("Invalid choice.")
            return
        chosen_script = scripts[choice_idx]
        subprocess.run([sys.executable, os.path.join(scripts_dir, chosen_script)])
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nExiting.")

if __name__ == "__main__":
    main()
