import cv2
import os
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
from datetime import datetime
import shutil
import threading
import time
from deepface import DeepFace
import pandas as pd
from tkinter import ttk
import json
from tkinter import messagebox
from tkcalendar import Calendar  # Perlu install: pip install tkcalendar
from tkinter import filedialog
import glob
from gtts import gTTS
from playsound import playsound

# Konstanta global
WAJAH_DIR = 'datawajah'
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
MIN_CONFIDENCE = 0.6  # Threshold untuk verifikasi wajah
SIMILARITY_THRESHOLD = 0.3  # Nilai lebih kecil = lebih ketat

# Konstanta untuk file penyimpanan data
STUDENT_DATA_FILE = 'student_data.json'
SUBJECTS_FILE = 'subjects.json'
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin'
}

class SubjectManager:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Manajemen Mata Pelajaran")
        self.window.geometry("600x400")
        self.window.configure(bg="#242526")
        
        # Form tambah mata pelajaran
        form_frame = tk.Frame(self.window, bg="#242526")
        form_frame.pack(pady=10, padx=10, fill='x')
        
        # Mata Pelajaran
        tk.Label(form_frame, text="Mata Pelajaran:", 
                bg="#242526", fg="white").grid(row=0, column=0, padx=5, pady=5)
        self.subject_entry = tk.Entry(form_frame)
        self.subject_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Guru Pengampu
        tk.Label(form_frame, text="Guru Pengampu:", 
                bg="#242526", fg="white").grid(row=1, column=0, padx=5, pady=5)
        self.teacher_entry = tk.Entry(form_frame)
        self.teacher_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Tambah button
        tk.Button(form_frame, text="Tambah", 
                 command=self.add_subject,
                 bg="#20bebe", fg="white").grid(row=2, column=0, columnspan=2, pady=10)
        
        # Treeview untuk daftar mata pelajaran
        columns = ('Mata Pelajaran', 'Guru Pengampu')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        # Konfigurasi kolom
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=250)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, 
                                 command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack elements
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tombol hapus
        tk.Button(self.window, text="Hapus Terpilih", 
                 command=self.delete_subject,
                 bg="#FF0000", fg="white").pack(pady=10)
        
        self.load_subjects()
    
    def load_subjects(self):
        try:
            if os.path.exists(SUBJECTS_FILE):
                with open(SUBJECTS_FILE, 'r') as f:
                    subjects = json.load(f)
                for subject in subjects:
                    self.tree.insert('', tk.END, values=(subject['name'], subject['teacher']))
        except Exception as e:
            messagebox.showerror("Error", f"Error loading subjects: {str(e)}")
    
    def save_subjects(self):
        subjects = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            subjects.append({
                'name': values[0],
                'teacher': values[1]
            })
        try:
            with open(SUBJECTS_FILE, 'w') as f:
                json.dump(subjects, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving subjects: {str(e)}")
    
    def add_subject(self):
        subject = self.subject_entry.get().strip()
        teacher = self.teacher_entry.get().strip()
        
        if subject and teacher:
            self.tree.insert('', tk.END, values=(subject, teacher))
            self.save_subjects()
            self.subject_entry.delete(0, tk.END)
            self.teacher_entry.delete(0, tk.END)
            messagebox.showinfo("Sukses", "Mata pelajaran berhasil ditambahkan!")
        else:
            messagebox.showwarning("Warning", "Semua field harus diisi!")
    
    def delete_subject(self):
        selected = self.tree.selection()
        if selected:
            if messagebox.askyesno("Konfirmasi", "Hapus mata pelajaran terpilih?"):
                for item in selected:
                    self.tree.delete(item)
                self.save_subjects()
                messagebox.showinfo("Sukses", "Mata pelajaran berhasil dihapus!")
        else:
            messagebox.showwarning("Warning", "Pilih mata pelajaran yang akan dihapus!")

class AdminPanel:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Admin Panel")
        self.window.geometry("1200x700")
        self.window.configure(bg="#242526")

        # Main container
        self.main_container = tk.Frame(self.window, bg="#242526")
        self.main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Left Frame - Menu Buttons
        left_frame = tk.Frame(self.main_container, bg="#242526", width=200)
        left_frame.pack(side='left', fill='y', padx=(0, 10))

        # Right Frame - Content Area
        self.right_frame = tk.Frame(self.main_container, bg="#242526")
        self.right_frame.pack(side='left', fill='both', expand=True)

        # Initialize frames dictionary
        self.frames = {}
        
        # Create menu buttons with consistent style
        button_style = {
            'width': 20,
            'height': 2,
            'bg': '#20bebe',
            'fg': 'white',
            'font': ('Roboto', 10),
            'relief': 'flat'
        }

        tk.Button(left_frame, text="Data Absensi", 
                 command=lambda: self.show_frame("absensi"), 
                 **button_style).pack(pady=5)
        
        tk.Button(left_frame, text="Data Siswa", 
                 command=lambda: self.show_frame("siswa"), 
                 **button_style).pack(pady=5)
        
        tk.Button(left_frame, text="Mata Pelajaran", 
                 command=lambda: self.show_frame("mapel"), 
                 **button_style).pack(pady=5)

        # Create all frames
        self.create_absensi_frame()
        self.create_siswa_frame()
        self.create_mapel_frame()

        # Show default frame
        self.show_frame("absensi")

        # Tambahkan timer untuk auto refresh
        self.start_auto_refresh()

    def start_auto_refresh(self):
        self.refresh_data()
        # Refresh setiap 5 detik
        self.window.after(5000, self.start_auto_refresh)

    def refresh_data(self):
        # Refresh data siswa jika frame siswa sedang aktif
        if self.frames.get("siswa") and self.frames["siswa"].winfo_viewable():
            self.load_siswa_data()

    def create_absensi_frame(self):
        frame = tk.Frame(self.right_frame, bg="#242526")
        
        # Title
        tk.Label(frame, text="Data Absensi Siswa",
                font=("Roboto", 16, "bold"),
                bg="#242526", fg="#20bebe").pack(pady=10)

        # Treeview Frame
        tree_frame = tk.Frame(frame, bg="#242526")
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Define columns
        columns = ('Tanggal Absen', 'Nama', 'NIS', 'Kelas', 
                  'Waktu Kedatangan', 'Mata Pelajaran')
        
        self.attendance_tree = ttk.Treeview(tree_frame, columns=columns, 
                                          show='headings', height=20)

        # Configure scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient='vertical', 
                                command=self.attendance_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', 
                                command=self.attendance_tree.xview)
        
        self.attendance_tree.configure(yscrollcommand=y_scroll.set, 
                                     xscrollcommand=x_scroll.set)

        # Configure column widths and headings
        column_widths = {
            'Tanggal Absen': 150,
            'Nama': 200,
            'NIS': 100,
            'Kelas': 100,
            'Waktu Kedatangan': 150,
            'Mata Pelajaran': 200
        }

        for col in columns:
            self.attendance_tree.heading(col, text=col)
            self.attendance_tree.column(col, width=column_widths[col], 
                                     minwidth=column_widths[col])

        # Grid layout
        self.attendance_tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self.frames["absensi"] = frame
        self.load_attendance_data()

    def load_attendance_data(self):
        try:
            # Clear existing items
            for item in self.attendance_tree.get_children():
                self.attendance_tree.delete(item)
            
            if os.path.exists('Attendance.csv'):
                df = pd.read_csv('Attendance.csv')
                for _, row in df.iterrows():
                    values = []
                    for col in self.attendance_tree['columns']:
                        val = row.get(col, '')
                        values.append('' if pd.isna(val) else str(val))
                    self.attendance_tree.insert('', 'end', values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data absensi: {str(e)}")

    def show_frame(self, frame_name):
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()
        
        # Show selected frame
        if frame_name in self.frames:
            self.frames[frame_name].pack(fill='both', expand=True)

    def create_siswa_frame(self):
        frame = tk.Frame(self.right_frame, bg="#242526")
        
        # Title
        tk.Label(frame, text="Data Siswa",
                font=("Roboto", 16, "bold"),
                bg="#242526", fg="#20bebe").pack(pady=10)

        # Input Frame
        input_frame = tk.Frame(frame, bg="#242526")
        input_frame.pack(fill='x', pady=10, padx=20)

        # Input fields
        labels = ['NIS:', 'Nama:', 'Kelas:']
        self.siswa_entries = []

        for i, label in enumerate(labels):
            tk.Label(input_frame, text=label, 
                    bg="#242526", fg="white").grid(row=i, column=0, 
                    sticky='e', padx=5, pady=5)
            entry = tk.Entry(input_frame)
            entry.grid(row=i, column=1, sticky='w', padx=5, pady=5)
            self.siswa_entries.append(entry)

        # Button Frame
        button_frame = tk.Frame(input_frame, bg="#242526")
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Tambah",
                  command=self.add_siswa).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Hapus",
                  command=self.delete_siswa).pack(side='left', padx=5)

        # Treeview Frame
        tree_frame = tk.Frame(frame, bg="#242526")
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Setup Treeview
        columns = ('NIS', 'Nama', 'Kelas')
        self.siswa_tree = ttk.Treeview(tree_frame, columns=columns, 
                                      show='headings', height=15)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", 
                                command=self.siswa_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", 
                                command=self.siswa_tree.xview)
        
        self.siswa_tree.configure(yscrollcommand=y_scroll.set, 
                                 xscrollcommand=x_scroll.set)

        # Configure columns
        column_widths = {
            'NIS': 100,
            'Nama': 200,
            'Kelas': 100
        }

        for col in columns:
            self.siswa_tree.heading(col, text=col)
            self.siswa_tree.column(col, width=column_widths[col], 
                                  minwidth=column_widths[col])

        # Grid layout
        self.siswa_tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.frames["siswa"] = frame
        self.load_siswa_data()

    def add_siswa(self):
        try:
            nis = self.siswa_entries[0].get().strip()
            nama = self.siswa_entries[1].get().strip()
            kelas = self.siswa_entries[2].get().strip()
            
            if all([nis, nama, kelas]):
                self.siswa_tree.insert('', 'end', values=(nis, nama, kelas))
                # Clear entries
                for entry in self.siswa_entries:
                    entry.delete(0, 'end')
                # Save to file
                self.save_siswa_data()
            else:
                messagebox.showwarning("Peringatan", "Semua field harus diisi!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menambah data: {str(e)}")

    def delete_siswa(self):
        try:
            selected_item = self.siswa_tree.selection()[0]
            self.siswa_tree.delete(selected_item)
            self.save_siswa_data()
        except IndexError:
            messagebox.showwarning("Peringatan", "Pilih data yang akan dihapus!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {str(e)}")

    def load_siswa_data(self):
        try:
            # Clear existing items
            for item in self.siswa_tree.get_children():
                self.siswa_tree.delete(item)

            if os.path.exists('siswa.csv'):
                df = pd.read_csv('siswa.csv')
                # Urutkan berdasarkan NIS
                df = df.sort_values('NIS')
                for _, row in df.iterrows():
                    values = []
                    for col in ['NIS', 'Nama', 'Kelas']:
                        val = row.get(col, '')
                        values.append('' if pd.isna(val) else str(val))
                    self.siswa_tree.insert('', 'end', values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data siswa: {str(e)}")

    def save_siswa_data(self):
        try:
            data = []
            for item in self.siswa_tree.get_children():
                data.append(self.siswa_tree.item(item)['values'])
            
            df = pd.DataFrame(data, columns=['NIS', 'Nama', 'Kelas'])
            # Urutkan sebelum menyimpan
            df = df.sort_values('NIS')
            df.to_csv('siswa.csv', index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan data siswa: {str(e)}")

    def create_mapel_frame(self):
        frame = tk.Frame(self.right_frame, bg="#242526")
        
        # Title
        tk.Label(frame, text="Data Mata Pelajaran",
                font=("Roboto", 16, "bold"),
                bg="#242526", fg="#20bebe").pack(pady=10)

        # Input Frame
        input_frame = tk.Frame(frame, bg="#242526")
        input_frame.pack(fill='x', pady=10, padx=20)

        # Input fields
        tk.Label(input_frame, text="Kode:", 
                bg="#242526", fg="white").grid(row=0, column=0, 
                sticky='e', padx=5, pady=5)
        self.kode_mapel_entry = tk.Entry(input_frame)
        self.kode_mapel_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        tk.Label(input_frame, text="Nama Mata Pelajaran:", 
                bg="#242526", fg="white").grid(row=1, column=0, 
                sticky='e', padx=5, pady=5)
        self.nama_mapel_entry = tk.Entry(input_frame)
        self.nama_mapel_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Button Frame
        button_frame = tk.Frame(input_frame, bg="#242526")
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Tambah",
                  command=self.add_mapel).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Hapus",
                  command=self.delete_mapel).pack(side='left', padx=5)

        # Treeview Frame
        tree_frame = tk.Frame(frame, bg="#242526")
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Setup Treeview
        columns = ('Kode', 'Nama Mata Pelajaran')
        self.mapel_tree = ttk.Treeview(tree_frame, columns=columns, 
                                      show='headings', height=15)

        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", 
                                command=self.mapel_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", 
                                command=self.mapel_tree.xview)
        
        self.mapel_tree.configure(yscrollcommand=y_scroll.set, 
                                 xscrollcommand=x_scroll.set)

        # Configure columns
        column_widths = {
            'Kode': 100,
            'Nama Mata Pelajaran': 300
        }

        for col in columns:
            self.mapel_tree.heading(col, text=col)
            self.mapel_tree.column(col, width=column_widths[col], 
                                  minwidth=column_widths[col])

        # Grid layout
        self.mapel_tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.frames["mapel"] = frame
        self.load_mapel_data()

    def add_mapel(self):
        try:
            kode = self.kode_mapel_entry.get().strip()
            nama = self.nama_mapel_entry.get().strip()
            
            if all([kode, nama]):
                self.mapel_tree.insert('', 'end', values=(kode, nama))
                # Clear entries
                self.kode_mapel_entry.delete(0, 'end')
                self.nama_mapel_entry.delete(0, 'end')
                # Save to file
                self.save_mapel_data()
            else:
                messagebox.showwarning("Peringatan", "Semua field harus diisi!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menambah data: {str(e)}")

    def delete_mapel(self):
        try:
            selected_item = self.mapel_tree.selection()[0]
            self.mapel_tree.delete(selected_item)
            self.save_mapel_data()
        except IndexError:
            messagebox.showwarning("Peringatan", "Pilih data yang akan dihapus!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {str(e)}")

    def load_mapel_data(self):
        try:
            # Clear existing items
            for item in self.mapel_tree.get_children():
                self.mapel_tree.delete(item)
                
            if os.path.exists('mapel.csv'):
                df = pd.read_csv('mapel.csv')
                for _, row in df.iterrows():
                    values = []
                    for col in ['Kode', 'Nama Mata Pelajaran']:
                        val = row.get(col, '')
                        values.append('' if pd.isna(val) else str(val))
                    self.mapel_tree.insert('', 'end', values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data mata pelajaran: {str(e)}")

    def save_mapel_data(self):
        try:
            data = []
            for item in self.mapel_tree.get_children():
                data.append(self.mapel_tree.item(item)['values'])
            
            df = pd.DataFrame(data, columns=['Kode', 'Nama Mata Pelajaran'])
            df.to_csv('mapel.csv', index=False)
            
            # Update combo box di main window jika ada
            self.update_mapel_combo()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan data mata pelajaran: {str(e)}")

class LoginPage:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Login - Face Recognition Attendance System")
        self.window.geometry("400x300")
        self.window.configure(bg="#242526")
        
        # Tambahkan protocol handler untuk event window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Inisialisasi TTS
        self.tts = TTSManager()
        
        # Header
        tk.Label(self.window, 
                text="LOGIN",
                font=("Roboto", 24, "bold"),
                bg="#242526",
                fg="#20bebe").pack(pady=20)
        
        # Login frame
        login_frame = tk.Frame(self.window, bg="#242526")
        login_frame.pack(pady=20)
        
        # Username
        tk.Label(login_frame, text="Username:",
                bg="#242526", fg="white",
                font=("Roboto", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.username = tk.Entry(login_frame, font=("Roboto", 12))
        self.username.grid(row=0, column=1, padx=5, pady=5)
        
        # Password
        tk.Label(login_frame, text="Password:",
                bg="#242526", fg="white",
                font=("Roboto", 12)).grid(row=1, column=0, padx=5, pady=5)
        self.password = tk.Entry(login_frame, show="*", font=("Roboto", 12))
        self.password.grid(row=1, column=1, padx=5, pady=5)
        
        # Login button
        tk.Button(self.window,
                 text="Login",
                 command=self.login,
                 bg="#20bebe",
                 fg="white",
                 font=("Roboto", 12),
                 width=15).pack(pady=20)
        
        # Error label
        self.error_label = tk.Label(self.window,
                                  text="",
                                  bg="#242526",
                                  fg="red",
                                  font=("Roboto", 10))
        self.error_label.pack()

    def on_closing(self):
        """Handler untuk event window closing"""
        self.tts.speak("Terima kasih telah menggunakan aplikasi ini. Sampai jumpa!")
        # Tunggu sebentar agar TTS selesai berbicara
        time.sleep(2)
        self.window.destroy()

    def login(self):
        username = self.username.get()
        password = self.password.get()
        
        # Ganti dengan kredensial yang diinginkan
        if username == "admin" and password == "admin123":
            self.tts.speak("Selamat datang admin, login berhasil, Program ini dibuat oleh komunitas unggulan dengan sepenuh hati")
            
            # Buat window selamat datang
            welcome = tk.Toplevel()
            welcome.title("Selamat Datang")
            welcome.geometry("400x300")
            welcome.configure(bg="#242526")
            
            # Tambahkan logo atau icon (opsional)
            try:
                logo = Image.open("logo.png")  # Sesuaikan dengan path logo Anda
                logo = logo.resize((100, 100))
                logo_tk = ImageTk.PhotoImage(logo)
                logo_label = tk.Label(welcome, image=logo_tk, bg="#242526")
                logo_label.image = logo_tk
                logo_label.pack(pady=20)
            except:
                pass  # Jika tidak ada logo, lewati
            
            # Pesan selamat datang
            tk.Label(welcome, 
                    text="Selamat Datang, Admin!",
                    font=("Roboto", 24, "bold"),
                    bg="#242526",
                    fg="#20bebe").pack(pady=10)
            
            tk.Label(welcome, 
                    text="Smart Attendance System",
                    font=("Roboto", 16),
                    bg="#242526",
                    fg="white").pack(pady=5)
            
            # Tambahkan waktu login
            current_time = datetime.now().strftime("%d %B %Y, %H:%M:%S")
            tk.Label(welcome, 
                    text=f"Login pada: {current_time}",
                    font=("Roboto", 12),
                    bg="#242526",
                    fg="#888888").pack(pady=20)
            
            # Tombol mulai
            tk.Button(welcome,
                     text="Mulai",
                     command=lambda: self.start_main_app(welcome),
                     bg="#20bebe",
                     fg="white",
                     font=("Roboto", 12),
                     width=15).pack(pady=20)
            
            # Posisikan di tengah screen
            welcome.update_idletasks()
            width = welcome.winfo_width()
            height = welcome.winfo_height()
            x = (welcome.winfo_screenwidth() // 2) - (width // 2)
            y = (welcome.winfo_screenheight() // 2) - (height // 2)
            welcome.geometry(f'{width}x{height}+{x}+{y}')
            
            # Buat window modal
            welcome.transient(self.window)
            welcome.grab_set()
            
        else:
            self.tts.speak("Username atau Password salah")
            self.error_label.config(text="Username atau Password salah!")

    def start_main_app(self, welcome_window):
        """Fungsi untuk memulai aplikasi utama"""
        welcome_window.destroy()  # Tutup window selamat datang
        self.window.destroy()     # Tutup window login
        app = AttendanceSystem()
        app.run()

class AttendanceSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Recognition Attendance System")
        
        # Tambahkan protocol handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Inisialisasi TTS
        self.tts = TTSManager()
        
        # Window size
        window_width = 700
        window_height = 400
        
        # Mengatur canvas
        self.canvas = tk.Canvas(self.root, width=window_width, height=window_height)
        self.canvas.grid(columnspan=4, rowspan=8)
        self.canvas.configure(bg="black")
        
        # Judul
        self.judul = tk.Label(self.root, text="Face Recognition Attendance System", 
                            font=("Roboto",28), bg="#242526", fg="white")
        self.canvas.create_window(350, 80, window=self.judul)
        
        # Credit
        self.made = tk.Label(self.root, text="Made by Morgan Tumanggor 'n Friends", 
                            font=("Times New Roman",13), bg="black", fg="white")
        self.canvas.create_window(360, 20, window=self.made)
        
        # Entry fields
        self.setup_entry_fields()
        
        # Instructions label
        self.instructions = tk.Label(self.root, text="Welcome", 
                                   font=("Roboto",15), fg="white", bg="black")
        self.canvas.create_window(370, 340, window=self.instructions)
        
        # Button frame
        button_frame = tk.Frame(self.root, bg="black")
        button_frame.grid(row=7, column=0, columnspan=4, pady=10)
        
        # Setup buttons dalam frame
        self.setup_buttons(button_frame)

        # Update combo box values from file
        self.update_mapel_combo_values()

    def on_closing(self):
        """Handler untuk event window closing"""
        if messagebox.askokcancel("Keluar", "Anda yakin ingin keluar dari aplikasi?"):
            self.tts.speak("Terima kasih telah menggunakan aplikasi ini. Sampai jumpa!")
            # Tunggu sebentar agar TTS selesai berbicara
            time.sleep(2)
            self.root.destroy()

    def setup_entry_fields(self):
        # Nama Siswa
        self.entry1 = tk.Entry(self.root, font=("Roboto", 10))
        self.canvas.create_window(457, 170, height=25, width=411, window=self.entry1)
        self.label1 = tk.Label(self.root, text="Nama Siswa", 
                              font=("Roboto", 10), fg="white", bg="black")
        self.canvas.create_window(90,170, window=self.label1)
        
        # NIS (bukan NIM)
        self.entry2 = tk.Entry(self.root, font=("Roboto", 10))
        self.canvas.create_window(457, 210, height=25, width=411, window=self.entry2)
        self.label2 = tk.Label(self.root, text="NIS", 
                              font=("Roboto", 10), fg="white", bg="black")
        self.canvas.create_window(60, 210, window=self.label2)
        
        # Kelas
        self.entry3 = tk.Entry(self.root, font=("Roboto", 10))
        self.canvas.create_window(457, 250, height=25, width=411, window=self.entry3)
        self.label3 = tk.Label(self.root, text="Kelas", 
                              font=("Roboto", 10), fg="white", bg="black")
        self.canvas.create_window(65, 250, window=self.label3)
        
        # Tambah combobox untuk mata pelajaran
        self.label4 = tk.Label(self.root, text="Mata Pelajaran", 
                             font=("Roboto", 10), fg="white", bg="black")
        self.canvas.create_window(95, 290, window=self.label4)
        
        self.mapel_combo = ttk.Combobox(self.root, font=("Roboto", 10),
                                       values=["Dasar Pemrograman", 
                                              "Matematika",
                                              "Fisika",
                                              "Kimia",
                                              "Biologi"])
        self.mapel_combo.set("Dasar Pemrograman")  # Default value
        self.canvas.create_window(457, 290, height=25, width=411, window=self.mapel_combo)

        # Bind enter key dan validasi
        self.entry1.bind('<Return>', lambda e: self.validate_and_next(self.entry1, self.entry2))
        self.entry2.bind('<Return>', lambda e: self.validate_and_next(self.entry2, self.entry3))
        self.entry3.bind('<Return>', lambda e: self.validate_and_next(self.entry3, None))

    def validate_and_next(self, current_entry, next_entry):
        value = current_entry.get().strip()
        if value:
            if next_entry:
                next_entry.focus()
            else:
                self.root.focus()
        else:
            self.tts.speak("Field tidak boleh kosong")
            messagebox.showwarning("Peringatan", "Field tidak boleh kosong!")
            current_entry.focus()

    def setup_buttons(self, button_frame):
        button_style = {
            "font": ("Roboto", 10),
            "width": 15,
            "height": 1,
            "relief": tk.RAISED,
            "cursor": "hand2"
        }
        
        # Take Images
        self.Rekam_btn = tk.Button(button_frame, 
                                  text="Take Images",
                                  bg="#20bebe",
                                  fg="white",
                                  command=self.rekamDataWajah,
                                  **button_style)
        self.Rekam_btn.pack(side=tk.LEFT, padx=5)
        
        # Face Attendance
        self.Rekam_btn2 = tk.Button(button_frame,
                                   text="Face Attendance",
                                   bg="#20bebe",
                                   fg="white",
                                   command=self.absensiWajah,
                                   **button_style)
        self.Rekam_btn2.pack(side=tk.LEFT, padx=5)
        
        # Delete Data
        self.Rekam_btn3 = tk.Button(button_frame,
                                   text="Delete Data",
                                   bg="#FF0000",
                                   fg="white",
                                   command=self.hapusDataWajah,
                                   **button_style)
        self.Rekam_btn3.pack(side=tk.LEFT, padx=5)
        
        # Admin Panel
        self.admin_btn = tk.Button(button_frame,
                                  text="Admin Panel",
                                  bg="#20bebe",
                                  fg="white",
                                  command=lambda: AdminPanel(),
                                  **button_style)
        self.admin_btn.pack(side=tk.LEFT, padx=5)
        
        # Tambah tombol Delete All Data
        self.delete_all_btn = tk.Button(button_frame,
                                      text="Delete All Data",
                                      bg="#FF0000",
                                      fg="white",
                                      command=self.delete_all_data,
                                      **button_style)
        self.delete_all_btn.pack(side=tk.LEFT, padx=5)

    def show_loading_screen(self):
        loading_window = tk.Toplevel(self.root)
        loading_window.title("Loading")
        loading_window.geometry("300x150")
        loading_window.configure(bg="#242526")
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        loading_label = tk.Label(loading_window, 
                               text="Mohon Tunggu...", 
                               font=("Roboto", 12),
                               bg="#242526", 
                               fg="white")
        loading_label.pack(pady=20)
        
        progress_bar = ttk.Progressbar(loading_window, 
                                     mode='indeterminate',
                                     length=200)
        progress_bar.pack(pady=20)
        progress_bar.start(10)
        
        return loading_window

    def hapusDataWajah(self):
        try:
            nama = self.entry1.get()
            nim = self.entry2.get()
            kelas = self.entry3.get()
            
            if not all([nama, nim, kelas]):
                messagebox.showwarning("Warning", "Semua field harus diisi!")
                return
            
            if messagebox.askyesno("Konfirmasi", f"Hapus data wajah untuk {nama}?"):
                delete_student_data(nim, nama, kelas)
                self.entry1.delete(0, tk.END)
                self.entry2.delete(0, tk.END)
                self.entry3.delete(0, tk.END)
                self.instructions.config(text="Data berhasil dihapus!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {str(e)}")

    def markAttendance(self, nama):
        try:
            now = datetime.now()
            tanggal = now.strftime('%d %B %Y')  # Format: 18 December 2024
            waktu = now.strftime('%H:%M:%S')
            
            # Ambil data dari entry
            nama = nama.strip()
            nis = self.entry2.get().strip()
            kelas = self.entry3.get().strip()
            mapel = self.mapel_combo.get()
            
            # Validasi data
            if not all([nama, nis, kelas, mapel]):
                raise Exception("Semua field harus diisi!")
            
            # Data baru
            new_data = pd.DataFrame({
                'Tanggal Absen': [tanggal],
                'Nama': [nama],
                'NIS': [nis],
                'Kelas': [kelas],
                'Waktu Kedatangan': [waktu],
                'Mata Pelajaran': [mapel]
            })
            
            if os.path.exists('Attendance.csv'):
                # Baca file yang ada dan gabungkan dengan data baru
                df = pd.read_csv('Attendance.csv')
                df = pd.concat([df, new_data], ignore_index=True)
            else:
                # Jika file belum ada, gunakan data baru
                df = new_data
            
            # Simpan ke CSV
            df.to_csv('Attendance.csv', index=False)
            self.tts.speak(f"Absensi berhasil dicatat untuk {nama}")
            return True
            
        except Exception as e:
            self.tts.speak("Terjadi kesalahan dalam mencatat absensi")
            messagebox.showerror("Error", f"Gagal mencatat absensi: {str(e)}")
            return False

    def rekamDataWajah(self):
        loading_screen = self.show_loading_screen()
        cam = None
        
        try:
            if not os.path.exists(WAJAH_DIR):
                os.makedirs(WAJAH_DIR)
            
            nama = self.entry1.get()
            nim = self.entry2.get()
            kelas = self.entry3.get()
            
            if not all([nama, nim, kelas]):
                self.instructions.config(text="Error: Semua field harus diisi!")
                loading_screen.destroy()
                return

            # Inisialisasi kamera dengan resolusi lebih tinggi
            cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            cam.set(cv2.CAP_PROP_BRIGHTNESS, 150)
            
            if not cam.isOpened():
                raise Exception("Tidak dapat mengakses kamera!")
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            img_counter = 0
            face_detected = False
            delay_counter = 0
            
            # Tambahkan TTS di awal
            self.tts.speak("Memulai proses perekaman data wajah. Silakan posisikan wajah Anda di depan kamera.")
            
            while True:
                ret, frame = cam.read()
                if not ret:
                    raise Exception("Gagal mengambil frame dari kamera")
                
                # Revert/flip kamera horizontal
                frame = cv2.flip(frame, 1)
                
                # Preprocessing gambar
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.05,
                    minNeighbors=2,
                    minSize=(80, 80),
                    maxSize=(600, 600)
                )
                
                face_detected = len(faces) > 0
                
                # Gambar kotak di sekitar wajah yang terdeteksi
                for (x, y, w, h) in faces:
                    # Perbesar area yang diambil (20% lebih besar)
                    margin = int(0.2 * w)
                    x1 = max(0, x - margin)
                    y1 = max(0, y - margin)
                    x2 = min(frame.shape[1], x + w + margin)
                    y2 = min(frame.shape[0], y + h + margin)
                    
                    # Gambar kotak utama dengan warna yang lebih mencolok
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    
                    # Tambahkan landmark wajah
                    center_x = x + w//2
                    center_y = y + h//2
                    cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)  # Titik tengah
                    cv2.circle(frame, (x + w//3, y + h//3), 5, (0, 0, 255), -1)  # Mata kiri
                    cv2.circle(frame, (x + 2*w//3, y + h//3), 5, (0, 0, 255), -1)  # Mata kanan
                
                # Tampilkan informasi pada frame
                cv2.putText(frame, f"Foto tersimpan: {img_counter}/20", (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Guide box yang lebih besar
                height, width = frame.shape[:2]
                center_x, center_y = width // 2, height // 2
                guide_size = 400  # Guide box lebih besar
                guide_color = (0, 255, 0) if face_detected else (0, 0, 255)
                
                # Gambar guide box dengan garis putus-putus
                for i in range(0, 360, 30):  # Membuat efek garis putus-putus
                    start_angle = i
                    end_angle = min(i + 20, 360)
                    pts = cv2.ellipse2Poly(
                        (center_x, center_y),
                        (guide_size//2, guide_size//2),
                        0, start_angle, end_angle, 1
                    )
                    cv2.polylines(frame, [pts], False, guide_color, 2)
                
                if face_detected:
                    cv2.putText(frame, "Wajah Terdeteksi!", (10, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Ambil foto dengan delay lebih pendek
                    delay_counter += 1
                    if delay_counter >= 3:  # Delay lebih pendek
                        img_name = f"{WAJAH_DIR}/{nim}_{nama}_{kelas}_{img_counter+1}.jpg"
                        
                        # Simpan gambar wajah yang diperbesar
                        face_img = frame[y1:y2, x1:x2]
                        face_img = cv2.resize(face_img, (300, 300))  # Ukuran lebih besar
                        cv2.imwrite(img_name, face_img)
                        
                        print(f"Image saved: {img_name}")
                        img_counter += 1
                        delay_counter = 0
                        
                        if img_counter >= 20:
                            # Tambahkan TTS untuk keberhasilan
                            self.tts.speak("Perekaman data wajah selesai.")
                            break
                else:
                    cv2.putText(frame, "Posisikan wajah di dalam area", (10, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, "dan lihat ke kamera", (10, 90), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    delay_counter = 0
                    self.tts.speak("Wajah tidak terdeteksi. Silakan posisikan wajah Anda dengan benar.")
                
                # Tampilkan frame
                cv2.imshow("Rekam Data Wajah", frame)
                
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    break
            
            if img_counter > 0:
                save_student_data(nim, nama, kelas)
                self.instructions.config(text="Rekam Data Telah Selesai!")
            else:
                self.instructions.config(text="Tidak ada foto yang diambil!")
                
        except Exception as e:
            print(f"Error in rekamDataWajah: {str(e)}")
            self.instructions.config(text=f"Error: {str(e)}")
        finally:
            if cam is not None:
                cam.release()
            cv2.destroyAllWindows()
            loading_screen.destroy()

    def absensiWajah(self):
        loading_screen = self.show_loading_screen()
        cam = None
        attendance_marked = False
        failed_attempts = 0
        
        try:
            if not os.path.exists(WAJAH_DIR):
                raise Exception("Folder data wajah tidak ditemukan!")
            
            nama = self.entry1.get().strip()
            nim = self.entry2.get().strip()
            kelas = self.entry3.get().strip()
            
            if not all([nama, nim, kelas]):
                raise Exception("Semua field harus diisi!")

            # Cek file wajah tersimpan
            face_files = glob.glob(f"{WAJAH_DIR}/{nim}_{nama}_{kelas}_*.jpg")
            if not face_files:
                raise Exception("Data wajah tidak ditemukan!")

            # Inisialisasi kamera dengan resolusi yang lebih baik
            cam = cv2.VideoCapture(0)
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Resolusi lebih tinggi
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cam.set(cv2.CAP_PROP_FPS, 30)
            cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Aktifkan autofocus
            
            if not cam.isOpened():
                raise Exception("Tidak dapat mengakses kamera!")

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Load semua wajah tersimpan
            stored_faces = [cv2.imread(face) for face in face_files]
            stored_faces = [face for face in stored_faces if face is not None]
            
            verification_count = 0
            max_verifications = 3
            
            # Tambahkan TTS di awal
            self.tts.speak("Memulai proses absensi wajah. Silakan posisikan wajah Anda di depan kamera.")
            
            while True:
                ret, frame = cam.read()
                if not ret:
                    raise Exception("Gagal mengambil frame dari kamera")
                
                frame = cv2.flip(frame, 1)
                
                # Deteksi wajah dengan parameter yang lebih sensitif
                faces = face_cascade.detectMultiScale(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                    scaleFactor=1.1,  # Lebih sensitif
                    minNeighbors=4,   # Lebih toleran
                    minSize=(60, 60),
                    maxSize=(300, 300)
                )
                
                if len(faces) == 1:
                    (x, y, w, h) = faces[0]
                    # Perbesar area wajah sedikit
                    margin = int(0.2 * w)
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    w = min(frame.shape[1] - x, w + 2*margin)
                    h = min(frame.shape[0] - y, h + 2*margin)
                    
                    face_img = frame[y:y+h, x:x+w]
                    
                    try:
                        is_verified = False
                        max_similarity = 0
                        
                        for stored_face in stored_faces:
                            result = DeepFace.verify(
                                face_img,
                                stored_face,
                                model_name="VGG-Face",
                                enforce_detection=False,
                                detector_backend="opencv",
                                distance_metric="cosine",
                                align=True  # Aktifkan alignment
                            )
                            
                            similarity = 1 - result.get("distance", 1)
                            max_similarity = max(max_similarity, similarity)
                            
                            # Turunkan threshold untuk verifikasi
                            if result["verified"] and similarity > 0.5:  # Threshold lebih rendah
                                is_verified = True
                                break
                        
                        if is_verified:
                            failed_attempts = 0
                            verification_count += 1
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            cv2.putText(frame, 
                                      f"Terverifikasi ({verification_count}/{max_verifications}) - {max_similarity:.2f}", 
                                      (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            
                            if verification_count >= max_verifications and not attendance_marked:
                                if self.markAttendance(nama):
                                    attendance_marked = True
                                    self.instructions.config(text="Absensi berhasil!")
                                    # Tambahkan TTS untuk keberhasilan
                                    self.tts.speak(f"Absensi berhasil untuk {nama}")
                                    break
                        else:
                            failed_attempts += 1
                            verification_count = max(0, verification_count - 1)
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                            cv2.putText(frame, 
                                      f"Tidak Dikenali ({failed_attempts}/5) - {max_similarity:.2f}", 
                                      (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                            
                            if failed_attempts >= 5:
                                # Tambahkan TTS untuk kegagalan
                                self.tts.speak("Verifikasi gagal. Silakan coba lagi nanti.")
                                messagebox.showerror("Verifikasi Gagal", 
                                    "Wajah tidak dikenali setelah 5 kali percobaan.\nSilakan coba lagi nanti.")
                                break
                
                    except Exception as e:
                        print(f"Verification error: {str(e)}")
                        continue
                
                cv2.imshow('Absensi Wajah', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
        except Exception as e:
            print(f"Error in absensiWajah: {str(e)}")
            self.instructions.config(text=f"Error: {str(e)}")
        finally:
            if cam is not None:
                cam.release()
            cv2.destroyAllWindows()
            loading_screen.destroy()

    def delete_all_data(self):
        if messagebox.askyesno("Konfirmasi", "Anda yakin ingin menghapus SEMUA data?\nTindakan ini tidak dapat dibatalkan!"):
            try:
                # Backup data lama
                if os.path.exists('Attendance.csv'):
                    backup_name = f'Attendance_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                    shutil.copy2('Attendance.csv', backup_name)
                
                # Hapus file attendance
                if os.path.exists('Attendance.csv'):
                    os.remove('Attendance.csv')
                
                # Hapus semua file wajah
                if os.path.exists(WAJAH_DIR):
                    for file in os.listdir(WAJAH_DIR):
                        file_path = os.path.join(WAJAH_DIR, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                
                # Tambahkan TTS untuk keberhasilan
                self.tts.speak("Semua data telah berhasil dihapus")
                messagebox.showinfo("Sukses", "Semua data berhasil dihapus!")
                
                # Reset entry fields
                self.entry1.delete(0, tk.END)
                self.entry2.delete(0, tk.END)
                self.entry3.delete(0, tk.END)
                self.mapel_combo.set("Dasar Pemrograman")
                
            except Exception as e:
                self.tts.speak("Terjadi kesalahan dalam menghapus data")
                messagebox.showerror("Error", f"Gagal menghapus data: {str(e)}")

    def run(self):
        self.root.mainloop()

    def update_mapel_combo_values(self):
        try:
            if os.path.exists('mapel_list.txt'):
                with open('mapel_list.txt', 'r') as f:
                    mapel_list = [line.strip() for line in f.readlines()]
                    if mapel_list:
                        self.mapel_combo['values'] = mapel_list
                        self.mapel_combo.set(mapel_list[0])
        except Exception as e:
            print(f"Error loading mapel list: {str(e)}")

class StudentManager:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Manajemen Data Siswa")
        self.window.geometry("1000x600")
        self.window.configure(bg="#242526")
        
        # Header
        header_frame = tk.Frame(self.window, bg="#242526")
        header_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(header_frame, 
                text="Manajemen Data Siswa",
                font=("Roboto", 20, "bold"),
                bg="#242526",
                fg="#20bebe").pack(side='left')
        
        # Treeview
        columns = ('NIM', 'Nama', 'Kelas', 'Status')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        
        self.tree.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Buttons frame
        btn_frame = tk.Frame(self.window, bg="#242526")
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(btn_frame, text="Hapus Data Wajah",
                  command=self.delete_face_data).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="Reset Data",
                  command=self.reset_student_data).pack(side='left', padx=5)
        
        self.load_student_data()

    def load_student_data(self):
        try:
            if os.path.exists(STUDENT_DATA_FILE):
                with open(STUDENT_DATA_FILE, 'r') as f:
                    data = json.load(f)
                for student in data:
                    has_face = "✓" if os.path.exists(f"{WAJAH_DIR}/{student['nim']}_{student['nama']}_{student['kelas']}_1.jpg") else "✗"
                    self.tree.insert('', tk.END, values=(student['nim'], 
                                                       student['nama'], 
                                                       student['kelas'],
                                                       has_face))
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data: {str(e)}")

    def delete_face_data(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih siswa terlebih dahulu!")
            return
            
        if messagebox.askyesno("Konfirmasi", "Hapus data wajah siswa terpilih?"):
            for item in selected:
                values = self.tree.item(item)['values']
                face_path = f"{WAJAH_DIR}/{values[0]}_{values[1]}_{values[2]}_1.jpg"
                if os.path.exists(face_path):
                    os.remove(face_path)
            self.load_student_data()

    def reset_student_data(self):
        if messagebox.askyesno("Konfirmasi", "Reset semua data siswa?"):
            try:
                if os.path.exists(STUDENT_DATA_FILE):
                    os.remove(STUDENT_DATA_FILE)
                if os.path.exists(WAJAH_DIR):
                    shutil.rmtree(WAJAH_DIR)
                    os.makedirs(WAJAH_DIR)
                self.tree.delete(*self.tree.get_children())
                messagebox.showinfo("Sukses", "Data siswa berhasil direset!")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal reset data: {str(e)}")

class ReportGenerator:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Generate Laporan")
        self.window.geometry("400x300")
        self.window.configure(bg="#242526")
        
        # Header
        tk.Label(self.window, 
                text="Generate Laporan Absensi",
                font=("Roboto", 16, "bold"),
                bg="#242526",
                fg="#20bebe").pack(pady=20)
        
        # Filter options
        filter_frame = tk.Frame(self.window, bg="#242526")
        filter_frame.pack(pady=20)
        
        tk.Label(filter_frame, text="Dari Tanggal:",
                bg="#242526", fg="white").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = tk.Entry(filter_frame)
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Sampai Tanggal:",
                bg="#242526", fg="white").grid(row=1, column=0, padx=5, pady=5)
        self.end_date = tk.Entry(filter_frame)
        self.end_date.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Kelas:",
                bg="#242526", fg="white").grid(row=2, column=0, padx=5, pady=5)
        self.class_entry = tk.Entry(filter_frame)
        self.class_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Generate button
        tk.Button(self.window, text="Generate Report",
                 command=self.generate_report,
                 bg="#20bebe", fg="white",
                 font=("Roboto", 10)).pack(pady=20)

    def generate_report(self):
        try:
            df = pd.read_csv('Attendance.csv')
            
            # Apply filters
            if self.start_date.get():
                df = df[df['Tanggal'] >= self.start_date.get()]
            if self.end_date.get():
                df = df[df['Tanggal'] <= self.end_date.get()]
            if self.class_entry.get():
                df = df[df['Kelas'] == self.class_entry.get()]
            
            # Save dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[("Excel files", "*.xlsx")],
                title="Simpan Laporan"
            )
            
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Sukses", "Laporan berhasil dibuat!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuat laporan: {str(e)}")

class Settings:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Pengaturan Sistem")
        self.window.geometry("400x300")
        self.window.configure(bg="#242526")
        
        # Header
        tk.Label(self.window, 
                text="Pengaturan Sistem",
                font=("Roboto", 16, "bold"),
                bg="#242526",
                fg="#20bebe").pack(pady=20)
        
        # Settings options
        settings_frame = tk.Frame(self.window, bg="#242526")
        settings_frame.pack(pady=20)
        
        # Camera settings
        tk.Label(settings_frame, text="Resolusi Kamera:",
                bg="#242526", fg="white").grid(row=0, column=0, padx=5, pady=5)
        
        resolutions = ["640x480", "1280x720", "1920x1080"]
        self.resolution_var = tk.StringVar(value=resolutions[0])
        ttk.Combobox(settings_frame, 
                    textvariable=self.resolution_var,
                    values=resolutions).grid(row=0, column=1, padx=5, pady=5)
        
        # Save button
        tk.Button(self.window, text="Simpan Pengaturan",
                 command=self.save_settings,
                 bg="#20bebe", fg="white",
                 font=("Roboto", 10)).pack(pady=20)

    def save_settings(self):
        try:
            # Implement settings save logic here
            messagebox.showinfo("Sukses", "Pengaturan berhasil disimpan!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan pengaturan: {str(e)}")

class TTSManager:
    def __init__(self):
        self.tts_thread = None
        self.counter = 0
    
    def speak(self, text, language='id'):
        """
        Mengubah teks menjadi suara dan memutarnya secara asynchronous
        """
        def tts_worker():
            try:
                # Buat nama file unik
                filename = f'tts_temp_{self.counter}.mp3'
                self.counter += 1
                
                # Generate audio
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(filename)
                
                # Putar audio
                playsound(filename)
                
                # Hapus file temporary
                os.remove(filename)
            except Exception as e:
                print(f"TTS Error: {str(e)}")
        
        # Jalankan TTS dalam thread terpisah
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_thread.join()  # Tunggu thread sebelumnya selesai
        
        self.tts_thread = threading.Thread(target=tts_worker)
        self.tts_thread.daemon = True
        self.tts_thread.start()

def save_student_data(nim, nama, kelas):
    try:
        data = []
        if os.path.exists(STUDENT_DATA_FILE):
            with open(STUDENT_DATA_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        
        # Tambahkan data baru sebagai dictionary
        new_data = {
            'nim': nim,
            'nama': nama,
            'kelas': kelas
        }
        
        # Append ke list
        data.append(new_data)
        
        # Simpan kembali ke file
        with open(STUDENT_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        raise Exception(f"Gagal menyimpan data siswa: {str(e)}")

def delete_student_data(nim, nama, kelas):
    try:
        data = []
        if os.path.exists(STUDENT_DATA_FILE):
            with open(STUDENT_DATA_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        
        # Filter data yang akan dihapus
        data = [s for s in data if not (s['nim'] == nim and 
                                      s['nama'] == nama and 
                                      s['kelas'] == kelas)]
        
        # Simpan kembali ke file
        with open(STUDENT_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        
        # Hapus file wajah
        pattern = f"{WAJAH_DIR}/{nim}_{nama}_{kelas}_*.jpg"
        for file in glob.glob(pattern):
            os.remove(file)
            
    except Exception as e:
        raise Exception(f"Gagal menghapus data siswa: {str(e)}")

def is_student_registered(nim, nama, kelas):
    try:
        if os.path.exists(STUDENT_DATA_FILE):
            with open(STUDENT_DATA_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        return any(s['nim'] == nim and 
                                 s['nama'] == nama and 
                                 s['kelas'] == kelas for s in data)
                except json.JSONDecodeError:
                    return False
        return False
    except Exception as e:
        print(f"Error checking student registration: {str(e)}")
        return False

# Jalankan aplikasi
if __name__ == "__main__":
    login = LoginPage()
    login.window.mainloop()

