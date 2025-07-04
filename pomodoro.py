#!/usr/bin/env python

import time
import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import math

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer • Task Edition")
        self.root.geometry("500x700")
        self.root.minsize(400, 500)  
        self.root.resizable(False, False)
        self.break_reminders = True  # Enable break reminders by default
        self.reminder_shown = False 
        self.sound_var = tk.StringVar(value="beep")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabel", background="#f5f5f5", font=("Noto Sans", 12))
        self.style.configure("TButton", font=("Noto Sans", 10), padding=5)
        self.style.configure("info.TButton", background="#5bc0de", foreground="white")
        self.style.map("TButton", 
                      background=[("active", "#d3d3d3"), ("!active", "#e0e0e0")],
                      foreground=[("active", "black"), ("!active", "black")])
        
        # Timer variables
        self.work_time = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60
        self.time_left = self.work_time
        self.is_running = False
        self.pomodoro_count = 0
        self.current_mode = "Work"
        
        # Task variables
        self.current_task = None
        self.tasks = []
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_checkbutton(label="Enable Break Reminders", 
                                      variable=tk.BooleanVar(value=True),
                                      command=lambda: setattr(self, 'break_reminders', not self.break_reminders))
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.root.config(menu=menubar)
        
        # Create tabs
        self.create_timer_tab()
        self.create_tasks_tab()
        
        # Load saved tasks
        self.load_tasks()
    
    def create_timer_tab(self):
        """Create the timer interface"""
        self.timer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.timer_tab, text="Timer")
        
        # Header
        header_frame = ttk.Frame(self.timer_tab)
        header_frame.pack(pady=10)
        
        ttk.Label(header_frame, text="Pomodoro Timer", 
                 font=("Noto Sans", 20, "bold")).pack()
        ttk.Label(header_frame, text="Linux Edition • Fedora Cinnamon",
                 font=("Noto Sans", 9)).pack()
        
        # Current task display
        self.current_task_label = ttk.Label(self.timer_tab, 
                                          text="No current task",
                                          font=("Noto Sans", 12))
        self.current_task_label.pack(pady=5)
        
        # Timer display
        self.timer_frame = ttk.Frame(self.timer_tab)
        self.timer_frame.pack(pady=20)
        
        self.timer_canvas = tk.Canvas(self.timer_frame, width=300, height=300, 
                                     bg="#f5f5f5", highlightthickness=0)
        self.timer_canvas.pack()
        
        # Timer elements
        self.progress_circle = self.timer_canvas.create_oval(50, 50, 250, 250, 
                                                            outline="#4a90d9", width=10)
        self.timer_text = self.timer_canvas.create_text(150, 150, 
                                                       text="25:00", 
                                                       font=("Noto Sans", 30, "bold"), 
                                                       fill="#4a90d9")
        self.mode_text = self.timer_canvas.create_text(150, 200, 
                                                      text="Work Time", 
                                                      font=("Noto Sans", 14), 
                                                      fill="#4a90d9")
        
        # Controls
        control_frame = ttk.Frame(self.timer_tab)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="Start", command=self.start_timer).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Pause", command=self.pause_timer).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Reset", command=self.reset_timer).grid(row=0, column=2, padx=5)
        
        # Counter
        self.counter_label = ttk.Label(self.timer_tab, 
                                 text="Tasks: 0/0 completed",  # Changed from Pomodoros
                                 font=("Noto Sans", 10))
        self.counter_label.pack(pady=5)
        
        # Settings
        settings_frame = ttk.Frame(self.timer_tab)
        settings_frame.pack(pady=10)
        
        ttk.Label(settings_frame, text="Work:").grid(row=0, column=0)
        self.work_entry = ttk.Entry(settings_frame, width=5)
        self.work_entry.insert(0, "25")
        self.work_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Short Break:").grid(row=0, column=2)
        self.short_entry = ttk.Entry(settings_frame, width=5)
        self.short_entry.insert(0, "5")
        self.short_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(settings_frame, text="Long Break:").grid(row=0, column=4)
        self.long_entry = ttk.Entry(settings_frame, width=5)
        self.long_entry.insert(0, "15")
        self.long_entry.grid(row=0, column=5, padx=5)
        
        ttk.Button(settings_frame, text="Apply", command=self.apply_settings).grid(row=1, column=2, columnspan=2, pady=5)
    
    def create_tasks_tab(self):
        """Create the task management interface"""
        self.tasks_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Tasks")
        
        # Task input
        self.task_input = ttk.Entry(self.tasks_tab, font=("Noto Sans", 12))
        self.task_input.pack(pady=10, padx=10, fill=tk.X)
        self.task_input.insert(0, "Enter task...")
        self.task_input.bind("<FocusIn>", lambda e: self.clear_placeholder())
        self.task_input.bind("<FocusOut>", lambda e: self.restore_placeholder())
        
        # Add task button
        ttk.Button(self.tasks_tab, text="Add Task", command=self.add_task).pack(pady=5)
        
        # Task list
        self.task_list = tk.Listbox(self.tasks_tab, font=("Noto Sans", 12), 
                                  height=15, selectmode=tk.SINGLE)
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Task controls
        control_frame = ttk.Frame(self.tasks_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Set as Current", 
                  command=self.set_current_task).pack(side=tk.LEFT)
        ttk.Button(self.tasks_tab, text="View Stats", style="info.TButton",
                   command=self.view_stats).pack(pady=5)
        ttk.Button(control_frame, text="Delete", 
                  command=self.delete_task).pack(side=tk.RIGHT)
    
    def clear_placeholder(self):
        if self.task_input.get() == "Enter task...":
            self.task_input.delete(0, tk.END)
    
    def restore_placeholder(self):
        if not self.task_input.get():
            self.task_input.insert(0, "Enter task...")
    
    def add_task(self):
        task = self.task_input.get()
        if task and task != "Enter task...":
            self.task_list.insert(tk.END, task)
            self.task_list.itemconfig(tk.END, fg="orange")  # New task color
            self.task_input.delete(0, tk.END)
            self.save_tasks()

    def set_current_task(self):
        selection = self.task_list.curselection()
        if selection:
            self.current_task = self.task_list.get(selection)
            self.current_task_label.config(text=f"Current Task: {self.current_task}")
            # Mark as done when set as current
            self.task_list.itemconfig(selection, fg="green")
            self.save_tasks()
            
            # Update completed task count in stats
            self.update_stats_display()
    
    def delete_task(self):
        selection = self.task_list.curselection()
        if selection:
            self.task_list.delete(selection)
            self.save_tasks()
            self.update_stats_display()
    
    def load_tasks(self):
        try:
            with open("pomodoro_tasks.json", "r") as f:
                data = json.load(f)
                for task in data:
                    self.task_list.insert(tk.END, task["text"])
                    self.task_list.itemconfig(tk.END, fg=task["color"])
                self.update_stats_display()  # Add this line
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
    def save_tasks(self):
        data = []
        for i in range(self.task_list.size()):
            text = self.task_list.get(i)
            color = self.task_list.itemcget(i, "fg")
            data.append({"text": text, "color": color})
        with open("pomodoro_tasks.json", "w") as f:
            json.dump(data, f)

    def view_stats(self):
        done_count = 0
        total_count = self.task_list.size()
        for i in range(total_count):
            if self.task_list.itemcget(i, "fg") == "green":
                done_count += 1
        messagebox.showinfo("Task Statistics", 
                            f"Total tasks: {total_count}\nCompleted tasks: {done_count}")

    def update_stats_display(self):
        done_count = 0
        total_count = self.task_list.size()
        for i in range(total_count):
            if self.task_list.itemcget(i, "fg") == "green":
                done_count += 1
        self.counter_label.config(text=f"Tasks: {done_count}/{total_count} completed")
            
    def update_timer_display(self):
        minutes, seconds = divmod(self.time_left, 60)
        self.timer_canvas.itemconfig(self.timer_text, text=f"{minutes:02d}:{seconds:02d}")
        
        # Update progress circle
        self.timer_canvas.delete(self.progress_circle)
        
        if self.current_mode == "Work":
            total_time = self.work_time
            color = "#4a90d9"  # Blue
        elif self.current_mode == "Short Break":
            total_time = self.short_break
            color = "#2daf7d"  # Green
        else:
            total_time = self.long_break
            color = "#d94a4a"  # Red
            
        progress = 1 - (self.time_left / total_time)
        angle = progress * 360
        
        # Draw progress arc
        self.timer_canvas.create_arc(50, 50, 250, 250, 
                                    start=90, extent=-angle, 
                                    outline=color, width=10, style=tk.ARC)
        
        # Draw remaining arc
        self.timer_canvas.create_arc(50, 50, 250, 250, 
                                    start=90-angle, extent=-(360-angle), 
                                    outline="#f5f5f5", width=10, style=tk.ARC)
    
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.run_timer()
    
    def pause_timer(self):
        self.is_running = False
    
    def reset_timer(self):
        self.is_running = False
        if self.current_mode == "Work":
            self.time_left = self.work_time
        elif self.current_mode == "Short Break":
            self.time_left = self.short_break
        else:
            self.time_left = self.long_break
        self.update_timer_display()
    
    def run_timer(self):
        if self.is_running and self.time_left > 0:
            # Show reminder at 15 minutes remaining (10 minutes into work)
            if self.current_mode == "Work" and self.time_left == 15 * 60:
                self.show_break_reminder()
                
            self.time_left -= 1
            self.update_timer_display()
            self.root.after(1000, self.run_timer)
        elif self.time_left == 0:
            self.timer_complete()

    def show_break_reminder(self):
        if self.break_reminders and self.current_mode == "Work" and not self.reminder_shown:
            messagebox.showwarning("Posture Check!", 
                                   "Remember to:\n\n"
                                   "1. Stretch your arms and back\n"
                                   "2. Look away from the screen\n"
                                   "3. Take deep breaths\n\n"
                                   "Your body will thank you!")
            self.reminder_shown = True

    def timer_complete(self):
        self.is_running = False
        if hasattr(self, 'reminder_shown'):
            self.reminder_shown = False
            
        try:
            self.play_sound()
        except Exception as e:
            print(f"Error in timer completion: {e}")
        
        if self.current_mode == "Work":
            self.pomodoro_count += 1
            self.counter_label.config(text=f"Pomodoros Completed: {self.pomodoro_count}")
            
            if self.pomodoro_count % 4 == 0:
                self.current_mode = "Long Break"
                self.time_left = self.long_break
                messagebox.showinfo("Great job!", "You've completed 4 pomodoros! Time for a long break.")
            else:
                self.current_mode = "Short Break"
                self.time_left = self.short_break
                messagebox.showinfo("Time's up!", "Take a short break!")
        else:
            self.current_mode = "Work"
            self.time_left = self.work_time
            messagebox.showinfo("Break's over", "Time to get back to work!")
        
        self.timer_canvas.itemconfig(self.mode_text, text=f"{self.current_mode}")
        self.update_timer_display()
    
    def play_sound(self):
        sound_type = self.sound_var.get()
        try:
            if sound_type == "beep":
                # Using speaker-test for simple beep
                subprocess.run(["speaker-test", "-t", "sine", "-f", "1000", "-l", "1"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sound_type == "bell":
                # Using paplay with system bell sound
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"])
            elif sound_type == "alert":
                # Using notify-send for visual notification with sound
                subprocess.run(["notify-send", "-i", "timer", "Pomodoro Timer", "Time's up!"])
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"])
        except:
            # Fallback to terminal bell if other methods fail
            print("\a", end="", flush=True)
    
    def apply_settings(self):
        try:
            new_work = int(self.work_entry.get()) * 60
            new_short = int(self.short_entry.get()) * 60
            new_long = int(self.long_entry.get()) * 60
            
            if new_work <= 0 or new_short <= 0 or new_long <= 0:
                raise ValueError("Times must be positive")
                
            self.work_time = new_work
            self.short_break = new_short
            self.long_break = new_long
            
            if self.current_mode == "Work":
                self.time_left = self.work_time
            elif self.current_mode == "Short Break":
                self.time_left = self.short_break
            else:
                self.time_left = self.long_break
                
            self.update_timer_display()
            messagebox.showinfo("Settings Applied", "Timer settings updated successfully!")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid positive numbers for all times.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
