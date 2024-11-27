"""
TClicker

Author: HafizhVito
GitHub: https://github.com/Hafizhvito
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import pyautogui
import json
from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
import logging
import os
import queue

class SplashScreen:
    def __init__(self, master):
        self.master = master
        self.splash_window = tk.Toplevel(master)
        self.splash_window.title("TClicker")
        self.splash_window.geometry("400x300")
        self.splash_window.overrideredirect(True)  # Remove window decorations
        
        # Center the splash screen
        self._center_window(self.splash_window)

        # Splash screen frame
        splash_frame = tk.Frame(self.splash_window, bg='white', borderwidth=2, relief='raised')
        splash_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Logo or App Name
        title_label = tk.Label(splash_frame, text="Auto Clicker", 
                                font=("Arial", 16, "bold"), bg='white', fg='navy')
        title_label.pack(pady=(20, 10))

        # Version Information
        version_label = tk.Label(splash_frame, text="Version 1.0.0", 
                                  font=("Arial", 9), bg='white', fg='darkgray')
        version_label.pack(pady=(5, 10))

        # Welcome Message
        welcome_label = tk.Label(splash_frame, text=(
            "Thanks for using TClicker!\n\n"
            "Visit our GitHub repository:\n"
            "https://github.com/Hafizhvito"
        ), font=("Arial", 10), bg='white', fg='black', justify='center')
        welcome_label.pack(pady=(10, 20))

        # Add a Close button
        close_btn = ttk.Button(splash_frame, text="Open", command=self.destroy_splash)
        close_btn.pack(pady=(10, 10))

    def _center_window(self, window):
        """Center the window on the screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def destroy_splash(self):
        """Close the splash screen and show the main window"""
        self.splash_window.destroy()
        self.master.deiconify()  # Show the main window

class AutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("TClicker")

        # Center the main window
        self._center_window()

        self.root.geometry("700x650")

        # Enhanced status tracking
        self.is_recording = False
        self.is_playing = False
        self.stop_hotkey = 'esc'  # Default hotkey
        self.hotkey_listener = None

        # Actions storage with enhanced properties
        self.recorded_actions = []
        self.action_queue = queue.Queue()

        # Error handling and logging
        self.setup_logging()

        # Stop signal for threads
        self.stop_event = threading.Event()

        # Performance and reliability settings
        self.play_speed_multiplier = 1.0
        self.retry_attempts = 3

        # Create UI
        self._create_ui()

    def _center_window(self):
        """Center the main window on the screen"""
        self.root.update_idletasks()
        width = 700  # Same as geometry width
        height = 650  # Same as geometry height
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_logging(self):
        """Set up logging to track errors and actions"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'auto_clicker.log')),
                logging.StreamHandler()
            ]
        )

    def _create_ui(self):
        # Frame for controls
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.pack(padx=10, pady=10, fill='x')

        # Record button
        self.record_btn = ttk.Button(control_frame, text="Start Recording", command=self.start_recording)
        self.record_btn.pack(side='left', padx=5, pady=5)

        # Play button
        self.play_btn = ttk.Button(control_frame, text="Play Actions", command=self.toggle_play)
        self.play_btn.pack(side='left', padx=5, pady=5)

        # Save button
        self.save_btn = ttk.Button(control_frame, text="Save Config", command=self.save_recording)
        self.save_btn.pack(side='left', padx=5, pady=5)

        # Load button
        self.load_btn = ttk.Button(control_frame, text="Load Config", command=self.load_recording)
        self.load_btn.pack(side='left', padx=5, pady=5)

        # Stop Hotkey input
        hotkey_frame = ttk.LabelFrame(self.root, text="Set Stop Hotkey")
        hotkey_frame.pack(padx=10, pady=10, fill='x')

        ttk.Label(hotkey_frame, text="Stop Hotkey:").pack(side='left', padx=5, pady=5)
        self.hotkey_entry = ttk.Entry(hotkey_frame, width=20)
        self.hotkey_entry.pack(side='left', padx=5, pady=5)
        self.hotkey_entry.insert(0, self.stop_hotkey)

        set_hotkey_btn = ttk.Button(hotkey_frame, text="Set", command=self.set_stop_hotkey)
        set_hotkey_btn.pack(side='left', padx=5, pady=5)

        # Advanced Settings Frame
        settings_frame = ttk.LabelFrame(self.root, text="Advanced Settings")
        settings_frame.pack(padx=10, pady=10, fill='x')

        # Speed control
        ttk.Label(settings_frame, text="Playback Speed:").pack(side='left', padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(settings_frame, from_=0.1, to=2.0, 
                                 variable=self.speed_var, orient='horizontal', 
                                 command=self.update_play_speed)
        speed_scale.pack(side='left', padx=5, expand=True, fill='x')
        self.speed_label = ttk.Label(settings_frame, text="1.0x")
        self.speed_label.pack(side='left', padx=5)

        # Retry attempts
        ttk.Label(settings_frame, text="Retry Attempts:").pack(side='left', padx=5)
        self.retry_var = tk.IntVar(value=3)
        retry_spinbox = ttk.Spinbox(settings_frame, from_=0, to=10, 
                                     textvariable=self.retry_var, width=5)
        retry_spinbox.pack(side='left', padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Auto Clicker Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x', padx=10, pady=5)

        # Actions table
        self.action_tree = ttk.Treeview(self.root, columns=('Type', 'Details', 'Delay'), show='headings')
        self.action_tree.heading('Type', text='Action Type')
        self.action_tree.heading('Details', text='Details')
        self.action_tree.heading('Delay', text='Delay (seconds)')
        self.action_tree.pack(padx=10, pady=10, fill='both', expand=True)

    def set_stop_hotkey(self):
        new_hotkey = self.hotkey_entry.get().strip().lower()
        if new_hotkey:
            self.stop_hotkey = new_hotkey
            self.status_var.set(f"Stop hotkey set to: {self.stop_hotkey}")

    def update_play_speed(self, value=None):
        """Update playback speed dynamically"""
        speed = round(self.speed_var.get(), 1)
        self.play_speed_multiplier = speed
        self.speed_label.config(text=f"{speed}x")

    def start_hotkey_listener(self):
        if self.hotkey_listener is not None:
            return

        def on_press(key):
            try:
                if key.char and key.char.lower() == self.stop_hotkey:
                    self.stop_event.set()
            except AttributeError:
                if key.name == self.stop_hotkey:
                    self.stop_event.set()

        self.hotkey_listener = pynput_keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()

    def stop_hotkey_listener(self):
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

    def start_recording(self):
        try:
            if self.is_recording:
                return

            self.recorded_actions = []
            self.is_recording = True
            self.stop_event.clear()
            self.status_var.set("Recording... Press Stop Hotkey to stop")
            self.record_btn.config(state='disabled')

            logging.info("Started recording actions")
            self.start_hotkey_listener()

            threading.Thread(target=self._record_actions, daemon=True).start()
        except Exception as e:
            logging.error(f"Recording start error: {e}")
            messagebox.showerror("Error", f"Could not start recording: {e}")

    def _record_actions(self):
        start_time = time.time()
        recording_context = {'last_action_time': start_time}

        def safe_on_click(x, y, button, pressed):
            try:
                if not self.is_recording or self.stop_event.is_set():
                    return False

                if pressed:
                    current_time = time.time()
                    delay = current_time - recording_context['last_action_time']
                    action = {
                        'type': 'click',
                        'x': x,
                        'y': y,
                        'button': str(button),
                        'delay': delay
                    }
                    self.recorded_actions.append(action)
                    recording_context['last_action_time'] = current_time
                    self._update_action_tree()
            except Exception as e:
                logging.error(f"Click recording error: {e}")

        def safe_on_press(key):
            try:
                if not self.is_recording or self.stop_event.is_set():
                    return False

                current_time = time.time()
                delay = current_time - recording_context['last_action_time']
                action = {
                    'type': 'key',
                    'key': str(key),
                    'delay': delay
                }
                self.recorded_actions.append(action)
                recording_context['last_action_time'] = current_time
                self._update_action_tree()
            except Exception as e:
                logging.error(f"Key recording error: {e}")

        with pynput_mouse.Listener(on_click=safe_on_click) as mouse_listener, \
                pynput_keyboard.Listener(on_press=safe_on_press) as key_listener:
            while not self.stop_event.is_set():
                time.sleep(0.1)

        logging.info("Recording stopped")
        self.is_recording = False
        self.stop_hotkey_listener()
        self.status_var.set("Recording stopped")
        self.record_btn.config(state='normal')

    def _update_action_tree(self):
        for row in self.action_tree.get_children():
            self.action_tree.delete(row)
        for action in self.recorded_actions:
            if action['type'] == 'click':
                details = f"x: {action['x']}, y: {action['y']}, button: {action['button']}"
            elif action['type'] == 'key':
                details = f"key: {action['key']}"
            else:
                details = "Unknown"
            self.action_tree.insert('', 'end', values=(action['type'], details, round(action['delay'], 2)))

    def toggle_play(self):
        if self.is_playing:
            self.stop_playing()
        else:
            self.start_playing()

    def start_playing(self):
        if not self.recorded_actions:
            messagebox.showwarning("Warning", "No actions to play!")
            return

        self.is_playing = True
        self.stop_event.clear()
        self.status_var.set("Playing actions...")
        self.play_btn.config(text="Stop")
        self.start_hotkey_listener()

        threading.Thread(target=self._play_actions, daemon=True).start()

    def _play_actions(self):
        for retry in range(self.retry_var.get() + 1):
            try:
                for action in self.recorded_actions:
                    if self.stop_event.is_set():
                        break

                    # Dynamic delay with speed multiplier
                    adjusted_delay = action['delay'] / self.play_speed_multiplier
                    time.sleep(adjusted_delay)

                    if action['type'] == 'click':
                        pyautogui.click(x=action['x'], y=action['y'])
                    elif action['type'] == 'key':
                        pyautogui.press(action['key'].replace("'", ""))
                
                # Successful playback
                self.stop_playing()
                break
            except Exception as e:
                logging.error(f"Playback error (Attempt {retry + 1}): {e}")
                if retry == self.retry_var.get():
                    messagebox.showerror("Error", f"Playback failed after {retry + 1} attempts: {e}")
                    self.stop_playing()

    def stop_playing(self):
        self.is_playing = False
        self.stop_event.set()
        self.stop_hotkey_listener()
        self.status_var.set("Stopped")
        self.play_btn.config(text="Play Actions")

    def save_recording(self):
        try:
            if not self.recorded_actions:
                messagebox.showwarning("Warning", "No actions to save!")
                return

            recordings_dir = 'recordings'
            os.makedirs(recordings_dir, exist_ok=True)
            file_path = filedialog.asksaveasfilename(
                initialdir=recordings_dir,
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")]
            )
            if file_path:
                with open(file_path, 'w') as file:
                    json.dump(self.recorded_actions, file, indent=4)
                logging.info(f"Actions saved to {file_path}")
                self.status_var.set(f"Actions saved to {file_path}")
        except Exception as e:
            logging.error(f"Save recording error: {e}")
            messagebox.showerror("Error", f"Could not save recording: {e}")

    def load_recording(self):
        try:
            recordings_dir = 'recordings'
            os.makedirs(recordings_dir, exist_ok=True)
            file_path = filedialog.askopenfilename(
                initialdir=recordings_dir,
                filetypes=[("JSON Files", "*.json")]
            )
            if file_path:
                with open(file_path, 'r') as file:
                    self.recorded_actions = json.load(file)
                self._update_action_tree()
                logging.info(f"Actions loaded from {file_path}")
                self.status_var.set(f"Actions loaded from {file_path}")
        except Exception as e:
            logging.error(f"Load recording error: {e}")
            messagebox.showerror("Error", f"Could not load recording: {e}")

    def run(self):
        self.root.mainloop()

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main root window until splash is closed
    # Show splash screen
    splash = SplashScreen(root)
    root.update()

    # Create the main application
    app = AutoClicker(root)
    app.run()

if __name__ == "__main__":
    main()