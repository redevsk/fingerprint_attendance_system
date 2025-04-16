import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import serial
import mysql.connector
from mysql.connector import Error
import datetime
import time
import threading
import os

class FingerprintAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Fingerprint Attendance System")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        
        self.arduino = None
        self.arduino_thread = None
        self.arduino_thread_running = False
        
        self.db_connection = None
        self.db_cursor = None
        
        self.create_widgets()
        self.create_tabs()
        
        self.connect_to_arduino()
        self.connect_to_database()
        
        self.create_tables()
    
    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding="2")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.connection_label = ttk.Label(self.status_bar, text="Arduino: Not Connected | Database: Not Connected")
        self.connection_label.pack(side=tk.RIGHT)
    
    def create_tabs(self):
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.time_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.time_tab, text="Time In/Out")
        
        self.logs_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.logs_tab, text="Logs")
        
        self.registration_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.registration_tab, text="Registration")
        
        self.setup_time_tab()
        self.setup_logs_tab()
        self.setup_registration_tab()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def setup_time_tab(self):
        main_container = ttk.Frame(self.time_tab)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        user_info_frame = ttk.LabelFrame(main_container, text="User Information", padding="10")
        user_info_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(user_info_frame, text="Last Scanned:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.last_scanned_label = ttk.Label(user_info_frame, text="None")
        self.last_scanned_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(user_info_frame, text="Student ID:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.student_id_label = ttk.Label(user_info_frame, text="-")
        self.student_id_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        ttk.Label(user_info_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.name_label = ttk.Label(user_info_frame, text="-")
        self.name_label.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=2)
        
        ttk.Label(user_info_frame, text="Course:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.course_label = ttk.Label(user_info_frame, text="-")
        self.course_label.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=2)
        
        time_display_frame = ttk.Frame(main_container)
        time_display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        time_display_frame.grid_columnconfigure(0, weight=1)
        time_display_frame.grid_rowconfigure(0, weight=1)
        time_display_frame.grid_rowconfigure(4, weight=1)
        self.display_name_label = ttk.Label(time_display_frame, text="-", font=("Arial", 36, "bold"))
        self.display_name_label.grid(row=1, column=0, pady=10)
        
        self.status_time_label = ttk.Label(time_display_frame, text="-", font=("Arial", 36, "bold"))
        self.status_time_label.grid(row=2, column=0, pady=10)
        self.time_label = ttk.Label(time_display_frame, text="-", font=("Arial", 24))
        self.time_label.grid(row=3, column=0, pady=5)

        
        instructions_frame = ttk.LabelFrame(self.time_tab, text="Instructions", padding="10")
        instructions_frame.pack(fill=tk.X, pady=10)
        
        instructions_text = "Place your finger on the sensor to record attendance.\n"
        instructions_text += "Double beep indicates successful scan.\n"
        instructions_text += "Single long beep indicates failed scan or error."
        
        ttk.Label(instructions_frame, text=instructions_text).pack(anchor=tk.W)
    
    def setup_logs_tab(self):
        controls_frame = ttk.Frame(self.logs_tab)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(controls_frame, text="Filter by Date:").pack(side=tk.LEFT, padx=5)
        
        self.date_var = tk.StringVar()
        self.date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(controls_frame, textvariable=self.date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Today", command=self.set_today).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Export to CSV", command=self.export_logs).pack(side=tk.RIGHT, padx=5)
        columns = ("id", "student_id", "name", "course", "time_in", "time_out")
        self.logs_tree = ttk.Treeview(self.logs_tab, columns=columns, show="headings")
        
        self.logs_tree.heading("id", text="ID")
        self.logs_tree.heading("student_id", text="Student ID")
        self.logs_tree.heading("name", text="Name")
        self.logs_tree.heading("course", text="Course")
        self.logs_tree.heading("time_in", text="Time In")
        self.logs_tree.heading("time_out", text="Time Out")
        self.logs_tree.column("id", width=50)
        self.logs_tree.column("student_id", width=100)
        self.logs_tree.column("name", width=200)
        self.logs_tree.column("course", width=100)
        self.logs_tree.column("time_in", width=150)
        self.logs_tree.column("time_out", width=150)
        
        scrollbar = ttk.Scrollbar(self.logs_tab, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_tree.configure(yscroll=scrollbar.set)
        self.logs_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_registration_tab(self):
        left_frame = ttk.Frame(self.registration_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        user_list_frame = ttk.LabelFrame(left_frame, text="User List", padding="5")
        user_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("id", "student_id", "name", "course", "registered")
        self.user_tree = ttk.Treeview(user_list_frame, columns=columns, show="headings")
        
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("student_id", text="Student ID")
        self.user_tree.heading("name", text="Name")
        self.user_tree.heading("course", text="Course")
        self.user_tree.heading("registered", text="Registered")
        
        self.user_tree.column("id", width=50)
        self.user_tree.column("student_id", width=100)
        self.user_tree.column("name", width=200)
        self.user_tree.column("course", width=100)
        self.user_tree.column("registered", width=80)
        
        scrollbar = ttk.Scrollbar(user_list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscroll=scrollbar.set)
        
        self.user_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        user_buttons_frame = ttk.Frame(left_frame)
        user_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(user_buttons_frame, text="Add User", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_buttons_frame, text="Edit User", command=self.edit_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_buttons_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_buttons_frame, text="Refresh", command=self.refresh_users).pack(side=tk.RIGHT, padx=5)
        
        right_frame = ttk.Frame(self.registration_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        fp_frame = ttk.LabelFrame(right_frame, text="Fingerprint Registration", padding="10")
        fp_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(fp_frame, text="Selected User:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.selected_user_label = ttk.Label(fp_frame, text="None")
        self.selected_user_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(fp_frame, text="Fingerprint ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fp_id_label = ttk.Label(fp_frame, text="-")
        self.fp_id_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(fp_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.fp_status_label = ttk.Label(fp_frame, text="-")
        self.fp_status_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        reg_buttons_frame = ttk.Frame(fp_frame)
        reg_buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.register_button = ttk.Button(reg_buttons_frame, text="Register Fingerprint", command=self.register_fingerprint)
        self.register_button.pack(side=tk.LEFT, padx=5)
        self.register_button.config(state=tk.DISABLED)
        
        self.delete_fp_button = ttk.Button(reg_buttons_frame, text="Delete Fingerprint", command=self.delete_fingerprint)
        self.delete_fp_button.pack(side=tk.LEFT, padx=5)
        self.delete_fp_button.config(state=tk.DISABLED)
        
        instructions_text = "1. Select a user from the list\n"
        instructions_text += "2. Click 'Register Fingerprint'\n"
        instructions_text += "3. Follow the instructions on the LCD display\n"
        instructions_text += "4. Place your finger on the sensor when prompted"
        
        ttk.Label(fp_frame, text=instructions_text).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_selected)
    
    def connect_to_arduino(self):
        try:
            ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9']
            
            for port in ports:
                try:
                    self.arduino = serial.Serial(port, 9600, timeout=1)
                    time.sleep(2)  
                    self.update_status(f"Arduino connected on {port}")
                    self.connection_label.config(text=f"Arduino: Connected ({port}) | Database: Not Connected")
                    
                    self.arduino_thread_running = True
                    self.arduino_thread = threading.Thread(target=self.read_from_arduino)
                    self.arduino_thread.daemon = True
                    self.arduino_thread.start()
                    
                    return
                except (OSError, serial.SerialException):
                    continue
            
            self.update_status("Could not connect to Arduino. Check connections.")
            messagebox.showerror("Connection Error", "Could not connect to Arduino. Check connections.")
        
        except Exception as e:
            self.update_status(f"Arduino connection error: {str(e)}")
            messagebox.showerror("Connection Error", f"Arduino connection error: {str(e)}")
    
    def connect_to_database(self):
        try:
            self.db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            
            if self.db_connection.is_connected():
                self.db_cursor = self.db_connection.cursor()
                
                self.db_cursor.execute("SHOW DATABASES LIKE 'fingerprint_attendance'")
                result = self.db_cursor.fetchone()
                
                if not result:
                    self.db_cursor.execute("CREATE DATABASE fingerprint_attendance")
                    self.update_status("Database created successfully")
                
                self.db_cursor.execute("USE fingerprint_attendance")
                
                self.update_status("Database connected")
                self.connection_label.config(text=f"{self.connection_label.cget('text').split(' | ')[0]} | Database: Connected")
            
        except Error as e:
            self.update_status(f"Database connection error: {str(e)}")
            messagebox.showerror("Database Error", f"Could not connect to database: {str(e)}")
    
    def create_tables(self):
        if self.db_connection and self.db_connection.is_connected():
            try:
                self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT PRIMARY KEY,
                    student_id VARCHAR(50) UNIQUE,
                    fname VARCHAR(50),
                    mname VARCHAR(50),
                    lname VARCHAR(50),
                    course VARCHAR(50),
                    is_registered BOOLEAN DEFAULT FALSE
                )
                """)
                
                self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    time_in DATETIME,
                    time_out DATETIME,
                    attendance_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """)
                
                self.db_connection.commit()
                self.update_status("Database tables created/verified")
                
                self.refresh_users()
                self.refresh_logs()
                
            except Error as e:
                self.update_status(f"Database table creation error: {str(e)}")
                messagebox.showerror("Database Error", f"Could not create tables: {str(e)}")
    
    def read_from_arduino(self):
        while self.arduino_thread_running:
            try:
                if self.arduino and self.arduino.is_open and self.arduino.in_waiting > 0:
                    data = self.arduino.readline().decode('utf-8').strip()
                    
                    if data:
                        self.process_arduino_data(data)
            except Exception as e:
                print(f"Error reading from Arduino: {str(e)}")
            
            time.sleep(0.1)  
    
    def process_arduino_data(self, data):
        print(f"Arduino data: {data}")
        
        if data.startswith("ID:"):
            fp_id = int(data.split(":")[1])
            self.process_fingerprint_scan(fp_id)
        
        elif data.startswith("ENROLL:"):
            result = data.split(":")[1]
            
            if result == "SUCCESS":
                self.fp_status_label.config(text="Registration successful")
                messagebox.showinfo("Registration", "Fingerprint registered successfully!")
                self.refresh_users()
            
            elif result == "FAILED":
                self.fp_status_label.config(text="Registration failed")
                messagebox.showerror("Registration Error", "Fingerprint registration failed. Please try again.")
            
            elif result == "CANCELLED":
                self.fp_status_label.config(text="Registration cancelled")
                messagebox.showinfo("Registration", "Fingerprint registration was cancelled.")
        
        elif data.startswith("DELETE:") or data.startswith("DELETE_ALL:"):
            result = data.split(":")[1]
            
            if result == "SUCCESS":
                self.fp_status_label.config(text="Deletion successful")
                messagebox.showinfo("Deletion", "Fingerprint(s) deleted successfully!")
                self.refresh_users()
            
            elif result == "FAILED":
                self.fp_status_label.config(text="Deletion failed")
                messagebox.showerror("Deletion Error", "Fingerprint deletion failed. Please try again.")
    
    def process_fingerprint_scan(self, fp_id):
        if not self.db_connection or not self.db_connection.is_connected():
            self.update_status("Database not connected")
            return
        
        try:
            self.db_cursor.execute("SELECT * FROM users WHERE id = %s", (fp_id,))
            user = self.db_cursor.fetchone()
            
            if not user:
                self.update_status(f"Unknown fingerprint ID: {fp_id}")
                return
            
            user_id = user[0]
            student_id = user[1]
            full_name = f"{user[2]} {user[3]} {user[4]}".strip()
            course = user[5]
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            self.db_cursor.execute("""
                SELECT * FROM attendance 
                WHERE user_id = %s AND attendance_date = %s 
                ORDER BY attendance_id DESC LIMIT 1
            """, (user_id, today))
            
            attendance_record = self.db_cursor.fetchone()
            current_time = datetime.datetime.now()
            
            if attendance_record and attendance_record[3] is None:  
                self.db_cursor.execute("""
                    UPDATE attendance 
                    SET time_out = %s 
                    WHERE attendance_id = %s
                """, (current_time, attendance_record[0]))
                
                self.db_connection.commit()
                status = "Timed Out"
            else:
                self.db_cursor.execute("""
                    INSERT INTO attendance (user_id, time_in, attendance_date) 
                    VALUES (%s, %s, %s)
                """, (user_id, current_time, today))
                
                self.db_connection.commit()
                status = "Timed In"
            
            self.last_scanned_label.config(text=str(fp_id))
            self.student_id_label.config(text=student_id)
            self.name_label.config(text=full_name)
            self.display_name_label.config(text=full_name)  
            self.course_label.config(text=course)
            self.status_time_label.config(text=status)
            self.time_label.config(text=current_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            self.update_status(f"{full_name} {status} at {current_time.strftime('%H:%M:%S')}")
            
            if self.notebook.index(self.notebook.select()) == 1:  
                self.refresh_logs()
        
        except Exception as e:
            self.update_status(f"Error processing fingerprint: {str(e)}")
            messagebox.showerror("Processing Error", f"Error processing fingerprint: {str(e)}")
    
    def on_tab_changed(self, event):
        tab_index = self.notebook.index(self.notebook.select())
        
        if tab_index == 0: 
            if self.arduino and self.arduino.is_open:
                self.arduino.write(b"MODE:NORMAL\n")
        
        elif tab_index == 1:  
            self.refresh_logs()
        
        elif tab_index == 2:
            if self.arduino and self.arduino.is_open:
                self.arduino.write(b"MODE:REGISTER\n")
            
            self.refresh_users()
    
    def refresh_logs(self):
        if not self.db_connection or not self.db_connection.is_connected():
            self.update_status("Database not connected")
            return
        
        try:
            for item in self.logs_tree.get_children():
                self.logs_tree.delete(item)
            
            date_filter = self.date_var.get()
            
            self.db_cursor.execute("""
                SELECT a.attendance_id, u.student_id, 
                       CONCAT(u.fname, ' ', u.mname, ' ', u.lname) as full_name, 
                       u.course, a.time_in, a.time_out, a.user_id
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE a.attendance_date = %s
                ORDER BY a.time_in DESC
            """, (date_filter,))
            
            records = self.db_cursor.fetchall()
            
            for record in records:
                attendance_id = record[0]
                student_id = record[1]
                full_name = record[2].strip()
                course = record[3]
                time_in = record[4].strftime("%H:%M:%S") if record[4] else "-"
                time_out = record[5].strftime("%H:%M:%S") if record[5] else "-"
                
                self.logs_tree.insert("", tk.END, values=(attendance_id, student_id, full_name, course, time_in, time_out))
            
            self.update_status(f"Loaded {len(records)} attendance records for {date_filter}")
        
        except Exception as e:
            self.update_status(f"Error refreshing logs: {str(e)}")
            messagebox.showerror("Refresh Error", f"Error refreshing logs: {str(e)}")
    
    def refresh_users(self):
        if not self.db_connection or not self.db_connection.is_connected():
            self.update_status("Database not connected")
            return
        
        try:
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            
            self.db_cursor.execute("""
                SELECT id, student_id, 
                       CONCAT(fname, ' ', mname, ' ', lname) as full_name, 
                       course, is_registered
                FROM users
                ORDER BY id
            """)
            
            users = self.db_cursor.fetchall()
            
            for user in users:
                user_id = user[0]
                student_id = user[1]
                full_name = user[2].strip()
                course = user[3]
                is_registered = "Yes" if user[4] else "No"
                
                self.user_tree.insert("", tk.END, values=(user_id, student_id, full_name, course, is_registered))
            
            self.update_status(f"Loaded {len(users)} users")
        
        except Exception as e:
            self.update_status(f"Error refreshing users: {str(e)}")
            messagebox.showerror("Refresh Error", f"Error refreshing users: {str(e)}")
    
    def set_today(self):
        self.date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))
        self.refresh_logs()
    
    def export_logs(self):
        if not self.db_connection or not self.db_connection.is_connected():
            self.update_status("Database not connected")
            return
        
        try:
            date_filter = self.date_var.get()
            filename = f"attendance_logs_{date_filter}.csv"
            
            with open(filename, 'w') as f:
                f.write("ID,Student ID,Name,Course,Time In,Time Out\n")
                
                for item_id in self.logs_tree.get_children():
                    values = self.logs_tree.item(item_id, 'values')
                    f.write(f"{values[0]},{values[1]},\"{values[2]}\",{values[3]},{values[4]},{values[5]}\n")
            
            self.update_status(f"Exported logs to {filename}")
            messagebox.showinfo("Export Successful", f"Logs exported to {filename}")
        
        except Exception as e:
            self.update_status(f"Error exporting logs: {str(e)}")
            messagebox.showerror("Export Error", f"Error exporting logs: {str(e)}")
    
    def add_user(self):
        add_dialog = tk.Toplevel(self.root)
        add_dialog.title("Add New User")
        add_dialog.geometry("400x350")
        add_dialog.transient(self.root)  
        add_dialog.grab_set()
        
        ttk.Label(add_dialog, text="ID (1-255):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_var = tk.StringVar()
        id_entry = ttk.Entry(add_dialog, textvariable=id_var, width=30)
        id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(add_dialog, text="Student ID:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        student_id_var = tk.StringVar()
        student_id_entry = ttk.Entry(add_dialog, textvariable=student_id_var, width=30)
        student_id_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(add_dialog, text="First Name:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        fname_var = tk.StringVar()
        fname_entry = ttk.Entry(add_dialog, textvariable=fname_var, width=30)
        fname_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(add_dialog, text="Middle Name:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        mname_var = tk.StringVar()
        mname_entry = ttk.Entry(add_dialog, textvariable=mname_var, width=30)
        mname_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(add_dialog, text="Last Name:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        lname_var = tk.StringVar()
        lname_entry = ttk.Entry(add_dialog, textvariable=lname_var, width=30)
        lname_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(add_dialog, text="Course:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        course_var = tk.StringVar()
        course_entry = ttk.Entry(add_dialog, textvariable=course_var, width=30)
        course_entry.grid(row=5, column=1, padx=10, pady=5)
        
        status_var = tk.StringVar()
        status_label = ttk.Label(add_dialog, textvariable=status_var, foreground="red")
        status_label.grid(row=6, column=0, columnspan=2, pady=10)
        
        def save_user():
            try:
                user_id = int(id_var.get())
                if user_id < 1 or user_id > 255:
                    status_var.set("ID must be between 1 and 255")
                    return
                
                student_id = student_id_var.get().strip()
                fname = fname_var.get().strip()
                mname = mname_var.get().strip()
                lname = lname_var.get().strip()
                course = course_var.get().strip()
                
                if not student_id or not fname or not lname or not course:
                    status_var.set("Please fill all required fields")
                    return
                
                self.db_cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if self.db_cursor.fetchone():
                    status_var.set(f"ID {user_id} already exists")
                    return
                
                self.db_cursor.execute("SELECT student_id FROM users WHERE student_id = %s", (student_id,))
                if self.db_cursor.fetchone():
                    status_var.set(f"Student ID {student_id} already exists")
                    return
                
                self.db_cursor.execute("""
                    INSERT INTO users (id, student_id, fname, mname, lname, course, is_registered)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, student_id, fname, mname, lname, course, False))
                
                self.db_connection.commit()
                self.update_status(f"Added user: {fname} {lname} (ID: {user_id})")
                self.refresh_users()
                add_dialog.destroy()
                
            except ValueError:
                status_var.set("ID must be a number")
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
        
        button_frame = ttk.Frame(add_dialog)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_user(self):
        selected_items = self.user_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a user to edit")
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        user_id = values[0]
        
        self.db_cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = self.db_cursor.fetchone()
        
        if not user:
            messagebox.showerror("Error", "User not found in database")
            return
        
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title(f"Edit User: {user[2]} {user[4]}")
        edit_dialog.geometry("400x350")
        edit_dialog.transient(self.root)  
        edit_dialog.grab_set()
        
        ttk.Label(edit_dialog, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        id_var = tk.StringVar(value=user[0])
        id_entry = ttk.Entry(edit_dialog, textvariable=id_var, width=30, state="readonly")
        id_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(edit_dialog, text="Student ID:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        student_id_var = tk.StringVar(value=user[1])
        student_id_entry = ttk.Entry(edit_dialog, textvariable=student_id_var, width=30)
        student_id_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(edit_dialog, text="First Name:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        fname_var = tk.StringVar(value=user[2])
        fname_entry = ttk.Entry(edit_dialog, textvariable=fname_var, width=30)
        fname_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(edit_dialog, text="Middle Name:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        mname_var = tk.StringVar(value=user[3])
        mname_entry = ttk.Entry(edit_dialog, textvariable=mname_var, width=30)
        mname_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(edit_dialog, text="Last Name:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        lname_var = tk.StringVar(value=user[4])
        lname_entry = ttk.Entry(edit_dialog, textvariable=lname_var, width=30)
        lname_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(edit_dialog, text="Course:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        course_var = tk.StringVar(value=user[5])
        course_entry = ttk.Entry(edit_dialog, textvariable=course_var, width=30)
        course_entry.grid(row=5, column=1, padx=10, pady=5)
        
        status_var = tk.StringVar()
        status_label = ttk.Label(edit_dialog, textvariable=status_var, foreground="red")
        status_label.grid(row=6, column=0, columnspan=2, pady=10)
        
        def update_user():
            try:
                student_id = student_id_var.get().strip()
                fname = fname_var.get().strip()
                mname = mname_var.get().strip()
                lname = lname_var.get().strip()
                course = course_var.get().strip()
                
                if not student_id or not fname or not lname or not course:
                    status_var.set("Please fill all required fields")
                    return

                self.db_cursor.execute("SELECT id FROM users WHERE student_id = %s AND id != %s", (student_id, user_id))
                if self.db_cursor.fetchone():
                    status_var.set(f"Student ID {student_id} already exists")
                    return
                
                self.db_cursor.execute("""
                    UPDATE users 
                    SET student_id = %s, fname = %s, mname = %s, lname = %s, course = %s
                    WHERE id = %s
                """, (student_id, fname, mname, lname, course, user_id))
                
                self.db_connection.commit()
                self.update_status(f"Updated user: {fname} {lname} (ID: {user_id})")
                self.refresh_users()
                edit_dialog.destroy()
                
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
        
        button_frame = ttk.Frame(edit_dialog)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Update", command=update_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_user(self):
        selected_items = self.user_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a user to delete")
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        user_id = values[0]
        user_name = values[2]
        
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {user_name} (ID: {user_id})?\n\nThis will also delete all attendance records for this user."):
            return
        
        try:
            self.db_cursor.execute("DELETE FROM attendance WHERE user_id = %s", (user_id,))
            
            self.db_cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            if values[4] == "Yes" and self.arduino and self.arduino.is_open:
                self.arduino.write(f"DELETE:{user_id}\n".encode())
            
            self.db_connection.commit()
            self.update_status(f"Deleted user: {user_name} (ID: {user_id})")
            self.refresh_users()
            
        except Exception as e:
            self.update_status(f"Error deleting user: {str(e)}")
            messagebox.showerror("Deletion Error", f"Error deleting user: {str(e)}")
    
    def on_user_selected(self, event):
        selected_items = self.user_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        user_id = values[0]
        user_name = values[2]
        is_registered = values[4] == "Yes"
        
        self.selected_user_label.config(text=f"{user_name} (ID: {user_id})")
        self.fp_id_label.config(text=user_id)
        
        if is_registered:
            self.fp_status_label.config(text="Fingerprint registered")
            self.register_button.config(state=tk.DISABLED)
            self.delete_fp_button.config(state=tk.NORMAL)
        else:
            self.fp_status_label.config(text="Not registered")
            self.register_button.config(state=tk.NORMAL)
            self.delete_fp_button.config(state=tk.DISABLED)
    
    def register_fingerprint(self):
        selected_items = self.user_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a user to register")
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        user_id = values[0]
        user_name = values[2]
        
        if not messagebox.askyesno("Confirm Registration", f"Register fingerprint for {user_name}?\n\nFollow the instructions on the LCD display."):
            return
        
        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.write(f"ENROLL:{user_id}\n".encode())
                self.fp_status_label.config(text="Registration in progress...")
                
                self.db_cursor.execute("UPDATE users SET is_registered = TRUE WHERE id = %s", (user_id,))
                self.db_connection.commit()
            else:
                messagebox.showerror("Connection Error", "Arduino not connected")
        
        except Exception as e:
            self.update_status(f"Error registering fingerprint: {str(e)}")
            messagebox.showerror("Registration Error", f"Error registering fingerprint: {str(e)}")
    
    def delete_fingerprint(self):
        selected_items = self.user_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a user to delete fingerprint")
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        user_id = values[0]
        user_name = values[2]
        
        if not messagebox.askyesno("Confirm Deletion", f"Delete fingerprint for {user_name}?"):
            return
        
        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.write(f"DELETE:{user_id}\n".encode())
                self.fp_status_label.config(text="Deletion in progress...")
                
                self.db_cursor.execute("UPDATE users SET is_registered = FALSE WHERE id = %s", (user_id,))
                self.db_connection.commit()
            else:
                messagebox.showerror("Connection Error", "Arduino not connected")
        
        except Exception as e:
            self.update_status(f"Error deleting fingerprint: {str(e)}")
            messagebox.showerror("Deletion Error", f"Error deleting fingerprint: {str(e)}")
    
    def update_status(self, message):
        self.status_label.config(text=message)
        print(message)  
    
    def on_closing(self):
        if self.arduino:
            self.arduino_thread_running = False
            time.sleep(0.5)  
            self.arduino.close()
        
        if self.db_connection and self.db_connection.is_connected():
            self.db_cursor.close()
            self.db_connection.close()
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FingerprintAttendanceSystem(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  
    root.mainloop()