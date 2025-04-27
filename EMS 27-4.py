import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import requests
import hashlib
import random
from datetime import datetime

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Tạo file json nếu chưa tồn tại

def initialize_json_files():
    files = {
        'users.json': {'teachers': [], 'students': []},
        'questions.json': {'questions': []},
        'exams.json': {'exams': []},
        'results.json': {'results': []}
    }

    for filename, default_data in files.items():
        filepath = os.path.join('data', filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)


initialize_json_files()

# Base User class

class User:
    def __init__(self, username, password, full_name):
        self.username = username
        # Hash the password for security
        self.password = hashlib.sha256(password.encode()).hexdigest()
        self.full_name = full_name

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
            'full_name': self.full_name
        }

    @classmethod
    def from_dict(cls, data):
        user = cls(data['username'], '', data['full_name'])
        user.password = data['password']  # Already hashed
        return user

# Teacher class


class Teacher(User):
    def __init__(self, username, password, full_name):
        super().__init__(username, password, full_name)
        self.role = 'teacher'

    def to_dict(self):
        data = super().to_dict()
        data['role'] = self.role
        return data

# Student class


class Student(User):
    def __init__(self, username, password, full_name):
        super().__init__(username, password, full_name)
        self.role = 'student'

    def to_dict(self):
        data = super().to_dict()
        data['role'] = self.role
        return data

# Question class


class Question:
    def __init__(self, id=None, text='', options=None, correct_answer=0, category=''):
        self.id = id if id else self._generate_id()
        self.text = text
        self.options = options if options else ['', '', '', '']
        self.correct_answer = correct_answer
        self.category = category

    def _generate_id(self):
        return f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'category': self.category
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            text=data['text'],
            options=data['options'],
            correct_answer=data['correct_answer'],
            category=data['category']
        )

# Exam class


class Exam:
    def __init__(self, id=None, title='', description='', questions=None, time_limit=60):
        self.id = id if id else self._generate_id()
        self.title = title
        self.description = description
        self.questions = questions if questions else []
        self.time_limit = time_limit  # in minutes

    def _generate_id(self):
        return f"e_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

    def add_question(self, question_id):
        if question_id not in self.questions:
            self.questions.append(question_id)

    def remove_question(self, question_id):
        if question_id in self.questions:
            self.questions.remove(question_id)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'questions': self.questions,
            'time_limit': self.time_limit
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            questions=data['questions'],
            time_limit=data['time_limit']
        )

# Result class


class Result:
    def __init__(self, student_username, exam_id, score, answers=None, date=None):
        self.student_username = student_username
        self.exam_id = exam_id
        self.score = score
        self.answers = answers if answers else {}
        self.date = date if date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            'student_username': self.student_username,
            'exam_id': self.exam_id,
            'score': self.score,
            'answers': self.answers,
            'date': self.date
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            student_username=data['student_username'],
            exam_id=data['exam_id'],
            score=data['score'],
            answers=data['answers'],
            date=data['date']
        )

# Database handler


class Database:
    @staticmethod
    def load_data(filename):
        filepath = os.path.join('data', filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty data if file doesn't exist or is invalid
            if filename == 'users.json':
                return {'teachers': [], 'students': []}
            elif filename == 'questions.json':
                return {'questions': []}
            elif filename == 'exams.json':
                return {'exams': []}
            elif filename == 'results.json':
                return {'results': []}
            return {}

    @staticmethod
    def save_data(filename, data):
        filepath = os.path.join('data', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def authenticate_user(username, password):
        data = Database.load_data('users.json')
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check teachers
        for teacher_data in data['teachers']:
            if teacher_data['username'] == username and teacher_data['password'] == hashed_password:
                return Teacher.from_dict(teacher_data)

        # Check students
        for student_data in data['students']:
            if student_data['username'] == username and student_data['password'] == hashed_password:
                return Student.from_dict(student_data)

        return None

    @staticmethod
    def add_user(user):
        data = Database.load_data('users.json')

        # Check if username already exists
        for teacher in data['teachers']:
            if teacher['username'] == user.username:
                return False

        for student in data['students']:
            if student['username'] == user.username:
                return False

        # Add user to appropriate list
        if user.role == 'teacher':
            data['teachers'].append(user.to_dict())
        else:
            data['students'].append(user.to_dict())

        Database.save_data('users.json', data)
        return True

    @staticmethod
    def get_all_users():
        data = Database.load_data('users.json')
        teachers = [Teacher.from_dict(t) for t in data['teachers']]
        students = [Student.from_dict(s) for s in data['students']]
        return teachers, students

    @staticmethod
    def update_user(user):
        data = Database.load_data('users.json')

        if user.role == 'teacher':
            for i, teacher in enumerate(data['teachers']):
                if teacher['username'] == user.username:
                    data['teachers'][i] = user.to_dict()
                    Database.save_data('users.json', data)
                    return True
        else:
            for i, student in enumerate(data['students']):
                if student['username'] == user.username:
                    data['students'][i] = user.to_dict()
                    Database.save_data('users.json', data)
                    return True

        return False

    @staticmethod
    def delete_user(username, role):
        data = Database.load_data('users.json')

        if role == 'teacher':
            data['teachers'] = [t for t in data['teachers']
                                if t['username'] != username]
        else:
            data['students'] = [s for s in data['students']
                                if s['username'] != username]

        Database.save_data('users.json', data)

    @staticmethod
    def add_question(question):
        data = Database.load_data('questions.json')
        data['questions'].append(question.to_dict())
        Database.save_data('questions.json', data)

    @staticmethod
    def get_all_questions():
        data = Database.load_data('questions.json')
        return [Question.from_dict(q) for q in data['questions']]

    @staticmethod
    def get_question_by_id(question_id):
        data = Database.load_data('questions.json')
        for q in data['questions']:
            if q['id'] == question_id:
                return Question.from_dict(q)
        return None

    @staticmethod
    def update_question(question):
        data = Database.load_data('questions.json')
        for i, q in enumerate(data['questions']):
            if q['id'] == question.id:
                data['questions'][i] = question.to_dict()
                Database.save_data('questions.json', data)
                return True
        return False

    @staticmethod
    def delete_question(question_id):
        data = Database.load_data('questions.json')
        data['questions'] = [
            q for q in data['questions'] if q['id'] != question_id]
        Database.save_data('questions.json', data)

        # Also remove this question from any exams
        exams_data = Database.load_data('exams.json')
        for exam in exams_data['exams']:
            if question_id in exam['questions']:
                exam['questions'].remove(question_id)
        Database.save_data('exams.json', exams_data)

    @staticmethod
    def add_exam(exam):
        data = Database.load_data('exams.json')
        data['exams'].append(exam.to_dict())
        Database.save_data('exams.json', data)

    @staticmethod
    def get_all_exams():
        data = Database.load_data('exams.json')
        return [Exam.from_dict(e) for e in data['exams']]

    @staticmethod
    def get_exam_by_id(exam_id):
        data = Database.load_data('exams.json')
        for e in data['exams']:
            if e['id'] == exam_id:
                return Exam.from_dict(e)
        return None

    @staticmethod
    def update_exam(exam):
        data = Database.load_data('exams.json')
        for i, e in enumerate(data['exams']):
            if e['id'] == exam.id:
                data['exams'][i] = exam.to_dict()
                Database.save_data('exams.json', data)
                return True
        return False

    @staticmethod
    def delete_exam(exam_id):
        data = Database.load_data('exams.json')
        data['exams'] = [e for e in data['exams'] if e['id'] != exam_id]
        Database.save_data('exams.json', data)

        # Also remove results for this exam
        results_data = Database.load_data('results.json')
        results_data['results'] = [
            r for r in results_data['results'] if r['exam_id'] != exam_id]
        Database.save_data('results.json', results_data)

    @staticmethod
    def add_result(result):
        data = Database.load_data('results.json')
        data['results'].append(result.to_dict())
        Database.save_data('results.json', data)

    @staticmethod
    def get_results_by_student(student_username):
        data = Database.load_data('results.json')
        return [Result.from_dict(r) for r in data['results'] if r['student_username'] == student_username]

    @staticmethod
    def get_results_by_exam(exam_id):
        data = Database.load_data('results.json')
        return [Result.from_dict(r) for r in data['results'] if r['exam_id'] == exam_id]

# Data crawler


class DataCrawler:
    @staticmethod
    def fetch_trivia_questions(amount=10, category=None):
        """Fetch trivia questions from Open Trivia Database API"""
        url = "https://opentdb.com/api.php?amount=50&difficulty=easy&type=multiple"
        params = {
            "amount": amount,
            "type": "multiple"
        }

        if category:
            params["category"] = category

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data["response_code"] == 0:
                questions = []
                for item in data["results"]:
                    # Create a list with all options, correct answer first
                    options = [item["correct_answer"]] + \
                        item["incorrect_answers"]
                    # Shuffle the options
                    random.shuffle(options)
                    # Find the index of the correct answer
                    correct_index = options.index(item["correct_answer"])

                    question = Question(
                        text=item["question"],
                        options=options,
                        correct_answer=correct_index,
                        category=item["category"]
                    )
                    questions.append(question)

                return questions
            else:
                print(f"API Error: {data['response_code']}")
                return []
        except Exception as e:
            print(f"Error fetching questions: {e}")
            return []

# Main Application


class ExamApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Exam Management System")
        self.geometry("1000x600")
        self.current_user = None

        # Set up the main container
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize frames dictionary
        self.frames = {}

        # Show login page
        self.show_frame(LoginPage)

    def show_frame(self, page_class, *args, **kwargs):
        # Destroy existing frame if it exists
        if page_class in self.frames:
            self.frames[page_class].destroy()

        # Create a new frame
        frame = page_class(self.container, self, *args, **kwargs)
        self.frames[page_class] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        frame.tkraise()

# Login Page


class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f5f5f5")
        
        # Main container frame
        container = tk.Frame(self, bg="#ffffff", bd=2, relief="groove", padx=40, pady=30)
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title with modern font and color
        title_label = tk.Label(
            container, 
            text="Exam Management System", 
            font=("Segoe UI", 24, "bold"), 
            bg="#ffffff",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 30))
        
        # Form frame
        form_frame = tk.Frame(container, bg="#ffffff")
        form_frame.pack()
        
        # Username field
        username_frame = tk.Frame(form_frame, bg="#ffffff")
        username_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(
            username_frame, 
            text="Username:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.username_entry = tk.Entry(
            username_frame, 
            width=25,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.username_entry.pack(side=tk.RIGHT)
        
        # Password field
        password_frame = tk.Frame(form_frame, bg="#ffffff")
        password_frame.pack(pady=10, fill=tk.X)
        
        tk.Label(
            password_frame, 
            text="Password:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.password_entry = tk.Entry(
            password_frame, 
            width=25,
            font=("Segoe UI", 10),
            show="*",
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.password_entry.pack(side=tk.RIGHT)
        
        # Login button with modern style
        login_button = tk.Button(
            container,
            text="Login",
            command=self.login,
            font=("Segoe UI", 10, "bold"),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            bd=0,
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        login_button.pack(pady=(20, 10), fill=tk.X)
        
        # Register link
        register_link = tk.Label(
            container,
            text="Create account",
            font=("Segoe UI", 9, "underline"),
            bg="#ffffff",
            fg="#3498db",
            cursor="hand2"
        )
        register_link.pack(pady=(10, 0))
        register_link.bind("<Button-1>", lambda e: self.show_register())

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror(
                "Error", "Please enter both username and password")
            return

        user = Database.authenticate_user(username, password)

        if user:
            self.controller.current_user = user
            if user.role == 'teacher':
                self.controller.show_frame(TeacherDashboard)
            else:
                self.controller.show_frame(StudentDashboard)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def show_register(self):
        self.controller.show_frame(RegisterPage)

# Register Page


class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f5f5f5")
        
        # Main container frame
        container = tk.Frame(self, bg="#ffffff", bd=2, relief="groove", padx=40, pady=30)
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title with modern font and color
        title_label = tk.Label(
            container, 
            text="Create Account", 
            font=("Segoe UI", 24, "bold"), 
            bg="#ffffff",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 20))
        
        # Form frame
        form_frame = tk.Frame(container, bg="#ffffff")
        form_frame.pack()
        
        # Full Name field
        fullname_frame = tk.Frame(form_frame, bg="#ffffff")
        fullname_frame.pack(pady=8, fill=tk.X)
        
        tk.Label(
            fullname_frame, 
            text="Full Name:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.fullname_entry = tk.Entry(
            fullname_frame, 
            width=25,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.fullname_entry.pack(side=tk.RIGHT)
        
        # Username field
        username_frame = tk.Frame(form_frame, bg="#ffffff")
        username_frame.pack(pady=8, fill=tk.X)
        
        tk.Label(
            username_frame, 
            text="Username:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.username_entry = tk.Entry(
            username_frame, 
            width=25,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.username_entry.pack(side=tk.RIGHT)
        
        # Password field
        password_frame = tk.Frame(form_frame, bg="#ffffff")
        password_frame.pack(pady=8, fill=tk.X)
        
        tk.Label(
            password_frame, 
            text="Password:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.password_entry = tk.Entry(
            password_frame, 
            width=25,
            font=("Segoe UI", 10),
            show="*",
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.password_entry.pack(side=tk.RIGHT)
        
        # Confirm Password field
        confirm_frame = tk.Frame(form_frame, bg="#ffffff")
        confirm_frame.pack(pady=8, fill=tk.X)
        
        tk.Label(
            confirm_frame, 
            text="Confirm Password:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.confirm_password_entry = tk.Entry(
            confirm_frame, 
            width=25,
            font=("Segoe UI", 10),
            show="*",
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.confirm_password_entry.pack(side=tk.RIGHT)
        
        # Role selection with modern radio buttons
        role_frame = tk.Frame(form_frame, bg="#ffffff")
        role_frame.pack(pady=12, fill=tk.X)
        
        tk.Label(
            role_frame, 
            text="Role:", 
            font=("Segoe UI", 10), 
            bg="#ffffff",
            fg="#34495e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.role_var = tk.StringVar(value="student")
        
        student_radio = tk.Radiobutton(
            role_frame,
            text="Student",
            variable=self.role_var,
            value="student",
            font=("Segoe UI", 9),
            bg="#ffffff",
            activebackground="#ffffff",
            selectcolor="#ffffff"
        )
        student_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        teacher_radio = tk.Radiobutton(
            role_frame,
            text="Teacher",
            variable=self.role_var,
            value="teacher",
            font=("Segoe UI", 9),
            bg="#ffffff",
            activebackground="#ffffff",
            selectcolor="#ffffff"
        )
        teacher_radio.pack(side=tk.LEFT)
        
        # Register button with modern style
        register_button = tk.Button(
            container,
            text="Register",
            command=self.register,
            font=("Segoe UI", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            bd=0,
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        register_button.pack(pady=(15, 10), fill=tk.X)
        
        # Back to login link
        login_link = tk.Label(
            container,
            text="Already have an account? Login here",
            font=("Segoe UI", 9, "underline"),
            bg="#ffffff",
            fg="#3498db",
            cursor="hand2"
        )
        login_link.pack(pady=(5, 0))
        login_link.bind("<Button-1>", lambda e: self.controller.show_frame(LoginPage))

    def register(self):
        fullname = self.fullname_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        role = self.role_var.get()

        # Validate inputs
        if not fullname or not username or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return

        # Create user object
        if role == 'teacher':
            user = Teacher(username, password, fullname)
        else:
            user = Student(username, password, fullname)

        # Add user to database
        if Database.add_user(user):
            messagebox.showinfo(
                "Success", "Registration successful! You can now login.")
            self.controller.show_frame(LoginPage)
        else:
            messagebox.showerror("Error", "Username already exists")

# Teacher Dashboard


class TeacherDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f5f7fa")

        # Check if user is logged in and is a teacher
        if not controller.current_user or controller.current_user.role != 'teacher':
            controller.show_frame(LoginPage)
            return

        # Create main layout
        self.create_layout()

    def create_layout(self):
        # Top bar with user info and logout button
        top_frame = tk.Frame(self, bg="#2c3e50", padx=15, pady=10)
        top_frame.pack(fill=tk.X)
        
        # Welcome label with user info
        welcome_label = tk.Label(
            top_frame, 
            text=f"Welcome, {self.controller.current_user.full_name}", 
            bg="#2c3e50", 
            fg="white",
            font=("Segoe UI", 12, "bold")
        )
        welcome_label.pack(side=tk.LEFT)
        
        # Logout button with modern style
        logout_button = tk.Button(
            top_frame, 
            text="Logout", 
            command=self.logout,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            bd=0,
            padx=12,
            pady=4,
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2"
        )
        logout_button.pack(side=tk.RIGHT)

        # Main content area with tabs
        tab_control = ttk.Notebook(self)
        style = ttk.Style()
        style.configure("TNotebook", background="#f5f7fa")
        style.configure("TNotebook.Tab", 
                       font=("Segoe UI", 10, "bold"),
                       padding=[10, 5],
                       background="#dfe6e9",
                       foreground="#2d3436")
        style.map("TNotebook.Tab", 
                 background=[("selected", "#3498db")],
                 foreground=[("selected", "black")])

        # Students tab
        students_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(students_tab, text=" Students ")
        self.setup_students_tab(students_tab)

        # Questions tab
        questions_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(questions_tab, text=" Questions ")
        self.setup_questions_tab(questions_tab)

        # Exams tab
        exams_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(exams_tab, text=" Exams ")
        self.setup_exams_tab(exams_tab)

        # Results tab
        results_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(results_tab, text=" Results ")
        self.setup_results_tab(results_tab)

        tab_control.pack(expand=1, fill=tk.BOTH, padx=10, pady=10)

    def setup_students_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search frame with modern styling
        search_frame = tk.Frame(container, bg="#f5f7fa")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame, 
            text="Search:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.student_search_entry = tk.Entry(
            search_frame, 
            width=30,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.student_search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(
            search_frame, 
            text="Search",
            command=self.search_students,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT)

        # Student list container with card-like styling
        list_container = tk.Frame(container, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with modern styling
        style = ttk.Style()
        style.configure("Treeview",
                        font=("Segoe UI", 10),
                        rowheight=25,
                        background="white",
                        fieldbackground="white",
                        foreground="#2d3436")
        style.configure("Treeview.Heading",
                       font=("Segoe UI", 10, "bold"),
                       background="#3498db",
                       foreground="black",
                       relief="flat")
        style.map("Treeview", background=[("selected", "#2980b9")])

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('username', 'full_name')
        self.student_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.student_tree.heading('username', text='Username')
        self.student_tree.heading('full_name', text='Full Name')
        self.student_tree.column('username', width=150, anchor=tk.W)
        self.student_tree.column('full_name', width=250, anchor=tk.W)

        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.student_tree.yview)

        # Action buttons frame with modern styling
        buttons_frame = tk.Frame(container, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        add_button = tk.Button(
            buttons_frame, 
            text="Add Student",
            command=self.add_student,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = tk.Button(
            buttons_frame, 
            text="Edit Student",
            command=self.edit_student,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = tk.Button(
            buttons_frame, 
            text="Delete Student",
            command=self.delete_student,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            **button_style
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_students,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load students
        self.load_students()

    def setup_questions_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split into two frames
        left_frame = tk.Frame(container, bg="#f5f7fa")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(container, bg="#f5f7fa")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.config(width=350)  # Đặt width sau khi frame đã được pack

        # Left frame - Question list
        # Search frame
        search_frame = tk.Frame(left_frame, bg="#f5f7fa")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame, 
            text="Search:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.question_search_entry = tk.Entry(
            search_frame, 
            width=30,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.question_search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(
            search_frame, 
            text="Search",
            command=self.search_questions,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT)

        # Question list container
        list_container = tk.Frame(left_frame, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for questions
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('id', 'text', 'category')
        self.question_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.question_tree.heading('id', text='ID')
        self.question_tree.heading('text', text='Question')
        self.question_tree.heading('category', text='Category')
        self.question_tree.column('id', width=80, anchor=tk.W)
        self.question_tree.column('text', width=300, anchor=tk.W)
        self.question_tree.column('category', width=120, anchor=tk.W)

        self.question_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.question_tree.yview)

        # Action buttons
        buttons_frame = tk.Frame(left_frame, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        add_button = tk.Button(
            buttons_frame, 
            text="Add Question",
            command=self.add_question,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = tk.Button(
            buttons_frame, 
            text="Edit Question",
            command=self.edit_question,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = tk.Button(
            buttons_frame, 
            text="Delete Question",
            command=self.delete_question,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            **button_style
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        import_button = tk.Button(
            buttons_frame, 
            text="Import Questions",
            command=self.import_questions,
            bg="#9b59b6",
            fg="white",
            activebackground="#8e44ad",
            **button_style
        )
        import_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_questions,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load questions
        self.load_questions()

        # Right frame - Question preview (card style)
        preview_frame = tk.LabelFrame(
            right_frame, 
            text="Question Preview", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold"),
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question text preview
        self.preview_question_text = tk.Text(
            preview_frame, 
            wrap=tk.WORD, 
            height=5, 
            width=40,
            font=("Segoe UI", 10),
            bg="white",
            fg="#2d3436",
            bd=1,
            relief="solid",
            padx=5,
            pady=5
        )
        self.preview_question_text.pack(fill=tk.X, pady=(0, 10))
        self.preview_question_text.config(state=tk.DISABLED)

        # Options preview
        options_frame = tk.Frame(preview_frame, bg="white")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.option_vars = []
        self.option_labels = []

        for i in range(4):
            var = tk.StringVar()
            self.option_vars.append(var)

            option_frame = tk.Frame(options_frame, bg="white")
            option_frame.pack(fill=tk.X, pady=2)
            
            # Radio button with modern style
            radio = tk.Radiobutton(
                option_frame, 
                variable=tk.IntVar(), 
                value=i,
                bg="white",
                activebackground="white",
                selectcolor="#3498db"
            )
            radio.pack(side=tk.LEFT)

            # Option label with card-like appearance
            label = tk.Label(
                option_frame, 
                textvariable=var,
                wraplength=300, 
                justify=tk.LEFT,
                bg="#f8f9fa",
                fg="#2d3436",
                font=("Segoe UI", 9),
                bd=1,
                relief="solid",
                padx=5,
                pady=3,
                anchor="w"
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.option_labels.append(label)    

    def setup_exams_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split into two frames
        left_frame = tk.Frame(container, bg="#f5f7fa")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(container, bg="#f5f7fa")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.config(width=350)

        # Left frame - Exam list
        # Search frame
        search_frame = tk.Frame(left_frame, bg="#f5f7fa")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame, 
            text="Search:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.exam_search_entry = tk.Entry(
            search_frame, 
            width=30,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.exam_search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(
            search_frame, 
            text="Search",
            command=self.search_exams,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT)

        # Exam list container
        list_container = tk.Frame(left_frame, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for exams
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('id', 'title', 'questions')
        self.exam_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.exam_tree.heading('id', text='ID')
        self.exam_tree.heading('title', text='Title')
        self.exam_tree.heading('questions', text='Questions')
        self.exam_tree.column('id', width=80, anchor=tk.W)
        self.exam_tree.column('title', width=250, anchor=tk.W)
        self.exam_tree.column('questions', width=80, anchor=tk.W)

        self.exam_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.exam_tree.yview)

        # Action buttons
        buttons_frame = tk.Frame(left_frame, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        add_button = tk.Button(
            buttons_frame, 
            text="Add Exam",
            command=self.add_exam,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = tk.Button(
            buttons_frame, 
            text="Edit Exam",
            command=self.edit_exam,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = tk.Button(
            buttons_frame, 
            text="Delete Exam",
            command=self.delete_exam,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            **button_style
        )
        delete_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_exams,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load exams
        self.load_exams()

        # Right frame - Exam preview (card style)
        preview_frame = tk.LabelFrame(
            right_frame, 
            text="Exam Preview", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold"),
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Exam title preview
        tk.Label(
            preview_frame, 
            text="Title:", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.preview_exam_title = tk.Label(
            preview_frame, 
            text="", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10),
            wraplength=300,
            justify=tk.LEFT,
            anchor="w"
        )
        self.preview_exam_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Exam description preview
        tk.Label(
            preview_frame, 
            text="Description:", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.preview_exam_desc = tk.Label(
            preview_frame, 
            text="", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10),
            wraplength=300,
            justify=tk.LEFT,
            anchor="w"
        )
        self.preview_exam_desc.pack(anchor=tk.W, pady=(0, 10))
        
        # Time limit preview
        tk.Label(
            preview_frame, 
            text="Time Limit:", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.preview_exam_time = tk.Label(
            preview_frame, 
            text="", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.preview_exam_time.pack(anchor=tk.W, pady=(0, 10))
        
        # Questions preview
        tk.Label(
            preview_frame, 
            text="Questions:", 
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Questions list with scrollbar
        questions_container = tk.Frame(preview_frame, bg="white")
        questions_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(questions_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_questions_list = tk.Listbox(
            questions_container, 
            yscrollcommand=scrollbar.set,
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 9),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            selectbackground="#3498db",
            selectforeground="white"
        )
        self.preview_questions_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.preview_questions_list.yview) 

    def setup_results_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search/filter frame
        search_frame = tk.Frame(container, bg="#f5f7fa")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Exam filter
        tk.Label(
            search_frame, 
            text="Filter by Exam:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.exam_filter_var = tk.StringVar()
        self.exam_filter_combobox = ttk.Combobox(
            search_frame, 
            textvariable=self.exam_filter_var,
            font=("Segoe UI", 10),
            width=28,
            state="readonly"
        )
        self.exam_filter_combobox.pack(side=tk.LEFT, padx=5)
        
        # Student filter
        tk.Label(
            search_frame, 
            text="Filter by Student:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=(15, 0))
        
        self.student_filter_var = tk.StringVar()
        self.student_filter_combobox = ttk.Combobox(
            search_frame, 
            textvariable=self.student_filter_var,
            font=("Segoe UI", 10),
            width=28,
            state="readonly"
        )
        self.student_filter_combobox.pack(side=tk.LEFT, padx=5)
        
        # Filter buttons
        apply_button = tk.Button(
            search_frame, 
            text="Apply Filters",
            command=self.filter_results,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        apply_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = tk.Button(
            search_frame, 
            text="Clear Filters",
            command=self.clear_result_filters,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT)

        # Results list container
        list_container = tk.Frame(container, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for results
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('student', 'exam', 'score', 'date')
        self.results_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.results_tree.heading('student', text='Student')
        self.results_tree.heading('exam', text='Exam')
        self.results_tree.heading('score', text='Score')
        self.results_tree.heading('date', text='Date')
        self.results_tree.column('student', width=150, anchor=tk.W)
        self.results_tree.column('exam', width=200, anchor=tk.W)
        self.results_tree.column('score', width=100, anchor=tk.CENTER)
        self.results_tree.column('date', width=150, anchor=tk.CENTER)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_tree.yview)

        # Action buttons
        buttons_frame = tk.Frame(container, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        details_button = tk.Button(
            buttons_frame, 
            text="View Details",
            command=self.view_result_details,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        details_button.pack(side=tk.LEFT, padx=5)
        
        export_button = tk.Button(
            buttons_frame, 
            text="Export Results",
            command=self.export_results,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_results,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load data for filters
        self.load_filter_data()
        # Load results
        self.load_results()

    def load_students(self):
        try:
            # Clear existing items with animation effect
            for item in self.student_tree.get_children():
                self.student_tree.delete(item)
            
            # Show loading state
            self.update()
            
            # Get all users
            teachers, students = Database.get_all_users()

            # Add students to the tree with alternating colors
            for i, student in enumerate(students):
                self.student_tree.insert('', tk.END, values=(
                    student.username, student.full_name),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load students: {str(e)}")

    def search_students(self):
        search_term = self.student_search_entry.get().strip().lower()
        
        if not search_term:
            self.load_students()
            return
            
        try:
            # Clear existing items
            for item in self.student_tree.get_children():
                self.student_tree.delete(item)
                
            # Show searching state
            self.update()
            
            # Get all users
            teachers, students = Database.get_all_users()

            # Add matching students to the tree
            matches = []
            for student in students:
                if (search_term in student.username.lower() or
                    search_term in student.full_name.lower()):
                    matches.append(student)
                    
            if not matches:
                self.student_tree.insert('', tk.END, values=("No results found", ""))
            else:
                for i, student in enumerate(matches):
                    self.student_tree.insert('', tk.END, values=(
                        student.username, student.full_name),
                        tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def add_student(self):
        try:
            dialog = StudentDialog(self, "Add Student")
            if dialog.result:
                username, password, full_name = dialog.result
                
                # Validate inputs
                if not all([username, password, full_name]):
                    messagebox.showwarning("Warning", "All fields are required")
                    return
                    
                if len(password) < 6:
                    messagebox.showwarning("Warning", "Password must be at least 6 characters")
                    return
                
                student = Student(username, password, full_name)
                
                # Show processing state
                self.update()
                
                if Database.add_user(student):
                    messagebox.showinfo("Success", "Student added successfully")
                    self.load_students()
                else:
                    messagebox.showerror("Error", "Username already exists")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add student: {str(e)}")

    def edit_student(self):
        try:
            selected = self.student_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a student to edit")
                return

            username = self.student_tree.item(selected[0], 'values')[0]
            teachers, students = Database.get_all_users()
            
            student = next((s for s in students if s.username == username), None)
            
            if not student:
                messagebox.showerror("Error", "Student not found")
                return

            dialog = StudentDialog(self, "Edit Student", student)
            if dialog.result:
                username, password, full_name = dialog.result
                
                # Validate inputs
                if not all([username, full_name]):
                    messagebox.showwarning("Warning", "Username and full name are required")
                    return
                    
                student.full_name = full_name
                if password:
                    if len(password) < 6:
                        messagebox.showwarning("Warning", "Password must be at least 6 characters")
                        return
                    student.password = hashlib.sha256(password.encode()).hexdigest()

                # Show processing state
                self.update()
                
                if Database.update_user(student):
                    messagebox.showinfo("Success", "Student updated successfully")
                    self.load_students()
                else:
                    messagebox.showerror("Error", "Failed to update student")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit student: {str(e)}")

    def delete_student(self):
        try:
            selected = self.student_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a student to delete")
                return

            username = self.student_tree.item(selected[0], 'values')[0]
            
            # Custom confirmation dialog
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete student '{username}'?",
                icon='warning'
            )
            
            if confirm:
                # Show processing state
                self.update()
                
                Database.delete_user(username, 'student')
                messagebox.showinfo("Success", "Student deleted successfully")
                self.load_students()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete student: {str(e)}")

    def load_questions(self):
        try:
            for item in self.question_tree.get_children():
                self.question_tree.delete(item)
                
            # Show loading state
            self.update()
            
            questions = Database.get_all_questions()
            
            for i, question in enumerate(questions):
                text = question.text[:50] + "..." if len(question.text) > 50 else question.text
                self.question_tree.insert('', tk.END, values=(
                    question.id, text, question.category),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                    
            self.question_tree.bind('<<TreeviewSelect>>', self.on_question_select)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load questions: {str(e)}")

    def on_question_select(self, event):
        try:
            selected = self.question_tree.selection()
            if not selected:
                return

            question_id = self.question_tree.item(selected[0], 'values')[0]
            question = Database.get_question_by_id(question_id)
            
            if not question:
                return

            # Update preview with animation
            self.preview_question_text.config(state=tk.NORMAL)
            self.preview_question_text.delete(1.0, tk.END)
            self.preview_question_text.insert(tk.END, question.text)
            self.preview_question_text.config(state=tk.DISABLED)
            
            # Highlight correct answer
            for i, option in enumerate(question.options):
                self.option_vars[i].set(option)
                self.option_labels[i].config(
                    bg="#e8f5e9" if i == question.correct_answer else "#f5f5f5"
                )
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load question details: {str(e)}")

    def search_questions(self):
        search_term = self.question_search_entry.get().strip().lower()
        
        if not search_term:
            self.load_questions()
            return
            
        try:
            for item in self.question_tree.get_children():
                self.question_tree.delete(item)
                
            # Show searching state
            self.question_tree.insert('', tk.END, values=("Searching...", "", ""))
            self.update()
            
            questions = Database.get_all_questions()
            matches = []
            
            for question in questions:
                if (search_term in question.text.lower() or
                    search_term in question.category.lower()):
                    matches.append(question)
                    
            if not matches:
                self.question_tree.insert('', tk.END, values=("No results found", "", ""))
            else:
                for i, question in enumerate(matches):
                    text = question.text[:50] + "..." if len(question.text) > 50 else question.text
                    self.question_tree.insert('', tk.END, values=(
                        question.id, text, question.category),
                        tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def add_question(self):
        try:
            dialog = QuestionDialog(self, "Add Question")
            if dialog.result:
                text, options, correct_answer, category = dialog.result
                
                # Validate inputs
                if not all([text, category]) or not all(options):
                    messagebox.showwarning("Warning", "All fields are required")
                    return
                    
                question = Question(text=text, options=options,
                                  correct_answer=correct_answer, category=category)
                
                # Show processing state
                messagebox.showinfo("Processing", "Adding question...")
                self.update()
                
                Database.add_question(question)
                messagebox.showinfo("Success", "Question added successfully")
                self.load_questions()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add question: {str(e)}")

    def edit_question(self):
        try:
            selected = self.question_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a question to edit")
                return

            question_id = self.question_tree.item(selected[0], 'values')[0]
            question = Database.get_question_by_id(question_id)
            
            if not question:
                messagebox.showerror("Error", "Question not found")
                return

            dialog = QuestionDialog(self, "Edit Question", question)
            if dialog.result:
                text, options, correct_answer, category = dialog.result
                
                # Validate inputs
                if not all([text, category]) or not all(options):
                    messagebox.showwarning("Warning", "All fields are required")
                    return
                    
                question.text = text
                question.options = options
                question.correct_answer = correct_answer
                question.category = category
                
                # Show processing state
                messagebox.showinfo("Processing", "Updating question...")
                self.update()
                
                if Database.update_question(question):
                    messagebox.showinfo("Success", "Question updated successfully")
                    self.load_questions()
                else:
                    messagebox.showerror("Error", "Failed to update question")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit question: {str(e)}")

    def delete_question(self):
        try:
            selected = self.question_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a question to delete")
                return

            question_id = self.question_tree.item(selected[0], 'values')[0]
            
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                "Are you sure you want to delete this question?",
                icon='warning'
            )
            
            if confirm:
                # Show processing state
                messagebox.showinfo("Processing", "Deleting question...")
                self.update()
                
                Database.delete_question(question_id)
                messagebox.showinfo("Success", "Question deleted successfully")
                self.load_questions()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete question: {str(e)}")

    def import_questions(self):
        try:
            dialog = ImportQuestionsDialog(self)
            if dialog.result:
                amount, category = dialog.result
                
                # Validate amount
                if not amount or amount <= 0 or amount > 50:
                    messagebox.showwarning("Warning", "Please enter a valid number between 1-50")
                    return
                
                # Custom progress dialog
                progress = tk.Toplevel()
                progress.title("Importing Questions")
                progress.geometry("300x100")
                progress.resizable(False, False)
                
                tk.Label(progress, text="Importing questions...").pack(pady=10)
                progress_bar = ttk.Progressbar(progress, length=250, mode='indeterminate')
                progress_bar.pack()
                progress_bar.start()
                self.update()
                
                questions = DataCrawler.fetch_trivia_questions(amount, category)
                
                if questions:
                    success_count = 0
                    for question in questions:
                        try:
                            Database.add_question(question)
                            success_count += 1
                        except:
                            continue
                            
                    progress.destroy()
                    messagebox.showinfo(
                        "Success", 
                        f"Successfully imported {success_count}/{len(questions)} questions"
                    )
                    self.load_questions()
                else:
                    progress.destroy()
                    messagebox.showerror("Error", "Failed to import questions")
                    
        except Exception as e:
            if 'progress' in locals():
                progress.destroy()
            messagebox.showerror("Error", f"Import failed: {str(e)}")

    def load_exams(self):
        try:
            for item in self.exam_tree.get_children():
                self.exam_tree.delete(item)
                
            # Show loading state
            #self.exam_tree.insert('', tk.END, values=("Loading...", "", ""))
            self.update()
            
            exams = Database.get_all_exams()
            
            for i, exam in enumerate(exams):
                self.exam_tree.insert('', tk.END, values=(
                    exam.id, exam.title, len(exam.questions)),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                    
            self.exam_tree.bind('<<TreeviewSelect>>', self.on_exam_select)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exams: {str(e)}")


    def on_exam_select(self, event):
        try:
            selected = self.exam_tree.selection()
            if not selected:
                return

            exam_values = self.exam_tree.item(selected[0], 'values')
            if not exam_values:
                return

            exam_id = exam_values[0]
            exam = Database.get_exam_by_id(exam_id)
            
            if not exam:
                return

            # Update preview with animation
            self.preview_exam_title.config(text=exam.title)
            self.preview_exam_desc.config(text=exam.description)
            self.preview_exam_time.config(text=f"{exam.time_limit} minutes")
            
            # Clear and update questions list
            self.preview_questions_list.delete(0, tk.END)
            
            for question_id in exam.questions:
                question = Database.get_question_by_id(question_id)
                if question:
                    text = question.text[:50] + "..." if len(question.text) > 50 else question.text
                    self.preview_questions_list.insert(tk.END, text)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exam details: {str(e)}")

    def search_exams(self):
        try:
            search_term = self.exam_search_entry.get().strip().lower()
            
            # Clear existing items with animation
            for item in self.exam_tree.get_children():
                self.exam_tree.delete(item)
                
            # Show searching state
            self.exam_tree.insert('', tk.END, values=("Searching...", "", ""))
            self.update()
            
            exams = Database.get_all_exams()
            matches = []
            
            for exam in exams:
                if (search_term in exam.title.lower() or 
                    search_term in exam.description.lower()):
                    matches.append(exam)
                    
            if not matches:
                self.exam_tree.insert('', tk.END, values=("No results found", "", ""))
            else:
                for i, exam in enumerate(matches):
                    self.exam_tree.insert('', tk.END, values=(
                        exam.id, exam.title, len(exam.questions)),
                        tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def add_exam(self):
        try:
            dialog = ExamDialog(self, "Add Exam")
            if dialog.result:
                title, description, questions, time_limit = dialog.result

                # Validate inputs
                if not all([title, description, questions, time_limit]):
                    messagebox.showwarning(
                        "Input Error", 
                        "Please fill all fields.",
                        icon='warning'
                    )
                    return
                    
                if len(questions) == 0:
                    messagebox.showwarning(
                        "Input Error",
                        "Please select at least one question.",
                        icon='warning'
                    )
                    return

                # Show processing state
                processing_window = tk.Toplevel()
                processing_window.title("Processing")
                tk.Label(processing_window, text="Creating exam...").pack(pady=10)
                progress = ttk.Progressbar(processing_window, mode='indeterminate')
                progress.pack(pady=5)
                progress.start()
                self.update()
                
                exam = Exam(
                    title=title, 
                    description=description,
                    questions=questions, 
                    time_limit=time_limit
                )

                Database.add_exam(exam)
                processing_window.destroy()
                
                messagebox.showinfo(
                    "Success", 
                    "Exam added successfully",
                    icon='info'
                )
                self.load_exams()
                
        except Exception as e:
            if 'processing_window' in locals():
                processing_window.destroy()
            messagebox.showerror(
                "Error", 
                f"Failed to add exam: {str(e)}",
                icon='error'
            )

    def edit_exam(self):
        try:
            selected = self.exam_tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Warning", 
                    "Please select an exam to edit",
                    icon='warning'
                )
                return

            exam_id = self.exam_tree.item(selected[0], 'values')[0]
            exam = Database.get_exam_by_id(exam_id)
            
            if not exam:
                messagebox.showerror(
                    "Error", 
                    "Exam not found",
                    icon='error'
                )
                return

            dialog = ExamDialog(self, "Edit Exam", exam)
            if dialog.result:
                title, description, questions, time_limit = dialog.result
                
                if not all([title, description, questions, time_limit]):
                    messagebox.showwarning(
                        "Input Error", 
                        "Please fill all fields.",
                        icon='warning'
                    )
                    return
                    
                if len(questions) == 0:
                    messagebox.showwarning(
                        "Input Error",
                        "Please select at least one question.",
                        icon='warning'
                    )
                    return

                # Show processing state
                processing_window = tk.Toplevel()
                processing_window.title("Processing")
                tk.Label(processing_window, text="Updating exam...").pack(pady=10)
                progress = ttk.Progressbar(processing_window, mode='indeterminate')
                progress.pack(pady=5)
                progress.start()
                self.update()
                
                exam.title = title
                exam.description = description
                exam.questions = questions
                exam.time_limit = time_limit

                if Database.update_exam(exam):
                    processing_window.destroy()
                    messagebox.showinfo(
                        "Success", 
                        "Exam updated successfully",
                        icon='info'
                    )
                    self.load_exams()
                else:
                    processing_window.destroy()
                    messagebox.showerror(
                        "Error", 
                        "Failed to update exam",
                        icon='error'
                    )
                    
        except Exception as e:
            if 'processing_window' in locals():
                processing_window.destroy()
            messagebox.showerror(
                "Error", 
                f"Failed to edit exam: {str(e)}",
                icon='error'
            )

    def delete_exam(self):
        try:
            selected = self.exam_tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Warning", 
                    "Please select an exam to delete",
                    icon='warning'
                )
                return

            exam_id = self.exam_tree.item(selected[0], 'values')[0]
            
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                "Are you sure you want to delete this exam?\nThis will also delete all related results.",
                icon='warning'
            )
            
            if confirm:
                # Show processing state
                processing_window = tk.Toplevel()
                processing_window.title("Processing")
                tk.Label(processing_window, text="Deleting exam...").pack(pady=10)
                progress = ttk.Progressbar(processing_window, mode='indeterminate')
                progress.pack(pady=5)
                progress.start()
                self.update()
                
                Database.delete_exam(exam_id)
                processing_window.destroy()
                
                messagebox.showinfo(
                    "Success", 
                    "Exam deleted successfully",
                    icon='info'
                )
                self.load_exams()
                
        except Exception as e:
            if 'processing_window' in locals():
                processing_window.destroy()
            messagebox.showerror(
                "Error", 
                f"Failed to delete exam: {str(e)}",
                icon='error'
            )

    def load_filter_data(self):
        try:
            # Show loading state
            self.exam_filter_combobox['values'] = ["Loading..."]
            self.student_filter_combobox['values'] = ["Loading..."]
            self.update()
            
            exams = Database.get_all_exams()
            exam_titles = ["All Exams"] + [exam.title for exam in exams]
            self.exam_filter_combobox['values'] = exam_titles
            self.exam_filter_combobox.current(0)

            teachers, students = Database.get_all_users()
            student_names = ["All Students"] + \
                [f"{student.full_name} ({student.username})" for student in students]
            self.student_filter_combobox['values'] = student_names
            self.student_filter_combobox.current(0)
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to load filter data: {str(e)}",
                icon='error'
            )

    def load_results(self):
        try:
            # Clear existing items with animation
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Show loading state
            #self.results_tree.insert('', tk.END, values=("Loading...", "", "", ""))
            self.update()
            
            exams = {exam.id: exam for exam in Database.get_all_exams()}
            teachers, students = Database.get_all_users()
            students_dict = {student.username: student for student in students}

            results_data = Database.load_data('results.json')
            
            if not results_data['results']:
                self.results_tree.insert('', tk.END, values=("No results found", "", "", ""))
                return
                
            for i, result_data in enumerate(results_data['results']):
                result = Result.from_dict(result_data)
                student = students_dict.get(result.student_username)
                exam = exams.get(result.exam_id)

                if student and exam:
                    self.results_tree.insert('', tk.END, values=(
                        student.full_name, 
                        exam.title, 
                        f"{result.score}%", 
                        result.date
                    ), tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                    
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to load results: {str(e)}",
                icon='error'
            )

    def filter_results(self):
        try:
            exam_filter = self.exam_filter_var.get()
            student_filter = self.student_filter_var.get()
            
            # Clear existing items with animation
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Show filtering state
            self.results_tree.insert('', tk.END, values=("Filtering...", "", "", ""))
            self.update()
            
            exams = {exam.id: exam for exam in Database.get_all_exams()}
            teachers, students = Database.get_all_users()
            students_dict = {student.username: student for student in students}

            results_data = Database.load_data('results.json')
            matches = []
            
            for result_data in results_data['results']:
                result = Result.from_dict(result_data)
                student = students_dict.get(result.student_username)
                exam = exams.get(result.exam_id)

                if student and exam:
                    exam_match = (exam_filter == "All Exams" or exam.title == exam_filter)
                    student_match = (student_filter == "All Students" or 
                                    f"{student.full_name} ({student.username})" == student_filter)
                    
                    if exam_match and student_match:
                        matches.append((student, exam, result))
                        
            if not matches:
                self.results_tree.insert('', tk.END, values=("No matching results", "", "", ""))
            else:
                for i, (student, exam, result) in enumerate(matches):
                    self.results_tree.insert('', tk.END, values=(
                        student.full_name, 
                        exam.title, 
                        f"{result.score}%", 
                        result.date
                    ), tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                    
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Filtering failed: {str(e)}",
                icon='error'
            )

    def clear_result_filters(self):
        try:
            self.exam_filter_combobox.current(0)
            self.student_filter_combobox.current(0)
            self.load_results()
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to clear filters: {str(e)}",
                icon='error'
            )

    def view_result_details(self):
        try:
            selected = self.results_tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Warning", 
                    "Please select a result to view",
                    icon='warning'
                )
                return

            student_name, exam_title, score, date = self.results_tree.item(
                selected[0], 'values')

            results_data = Database.load_data('results.json')
            exams = {exam.id: exam.title for exam in Database.get_all_exams()}
            exam_ids = {title: id for id, title in exams.items()}
            teachers, students = Database.get_all_users()
            student_usernames = {
                student.full_name: student.username for student in students}

            result = None
            for result_data in results_data['results']:
                r = Result.from_dict(result_data)
                if (r.student_username in student_usernames.values() and
                    r.exam_id in exam_ids.values() and
                    r.date == date):
                    result = r
                    break

            if result:
                ResultDetailsDialog(self, result)
            else:
                messagebox.showerror(
                    "Error", 
                    "Result details not found",
                    icon='error'
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to view details: {str(e)}",
                icon='error'
            )

    def export_results(self):
        try:
            results = []
            for item in self.results_tree.get_children():
                student_name, exam_title, score, date = self.results_tree.item(
                    item, 'values')
                results.append({
                    'Student': student_name,
                    'Exam': exam_title,
                    'Score': score,
                    'Date': date
                })

            if not results:
                messagebox.showwarning(
                    "Warning", 
                    "No results to export",
                    icon='warning'
                )
                return

            filename = simpledialog.askstring(
                "Export Results",
                "Enter filename (without extension):",
                parent=self
            )
            
            if not filename:
                return

            # Show export progress
            export_window = tk.Toplevel()
            export_window.title("Exporting")
            tk.Label(export_window, text="Exporting results...").pack(pady=10)
            progress = ttk.Progressbar(export_window, mode='indeterminate')
            progress.pack(pady=5)
            progress.start()
            self.update()
            
            with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.DictWriter(
                    f, fieldnames=['Student', 'Exam', 'Score', 'Date'])
                writer.writeheader()
                writer.writerows(results)

            export_window.destroy()
            messagebox.showinfo(
                "Success", 
                f"Results exported to {filename}.csv",
                icon='info'
            )
            
        except Exception as e:
            if 'export_window' in locals():
                export_window.destroy()
            messagebox.showerror(
                "Error", 
                f"Export failed: {str(e)}",
                icon='error'
            )

    def logout(self):
        confirm = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to logout?",
            icon='question'
        )
        if confirm:
            self.controller.current_user = None
            self.controller.show_frame(LoginPage)

# Student Dashboard


class StudentDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f5f7fa")  # Set background color
        
        # Check if user is logged in and is a student
        if not controller.current_user or controller.current_user.role != 'student':
            controller.show_frame(LoginPage)
            return

        # Create main layout
        self.create_layout()

    def create_layout(self):
        # Top bar with user info and logout button
        top_frame = tk.Frame(self, bg="#2c3e50", padx=15, pady=10)
        top_frame.pack(fill=tk.X)
        
        # Welcome label with modern styling
        welcome_label = tk.Label(
            top_frame, 
            text=f"Welcome, {self.controller.current_user.full_name}", 
            bg="#2c3e50", 
            fg="white",
            font=("Segoe UI", 12, "bold")
        )
        welcome_label.pack(side=tk.LEFT)
        
        # Modern logout button
        logout_button = tk.Button(
            top_frame, 
            text="Logout", 
            command=self.logout,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            bd=0,
            padx=12,
            pady=4,
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2"
        )
        logout_button.pack(side=tk.RIGHT)

        # Main content area with styled tabs
        style = ttk.Style()
        style.configure("TNotebook", background="#f5f7fa")
        style.configure("TNotebook.Tab", 
                       font=("Segoe UI", 10, "bold"),
                       padding=[10, 5],
                       background="#dfe6e9",
                       foreground="#2d3436")
        style.map("TNotebook.Tab", 
                 background=[("selected", "#3498db")],
                 foreground=[("selected", "black")])

        tab_control = ttk.Notebook(self)

        # Available Exams tab
        exams_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(exams_tab, text=" Available Exams ")
        self.setup_exams_tab(exams_tab)

        # My Results tab
        results_tab = tk.Frame(tab_control, bg="#f5f7fa")
        tab_control.add(results_tab, text=" My Results ")
        self.setup_results_tab(results_tab)

        tab_control.pack(expand=1, fill=tk.BOTH, padx=10, pady=10)

    def setup_exams_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search frame with modern styling
        search_frame = tk.Frame(container, bg="#f5f7fa")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            search_frame, 
            text="Search:", 
            bg="#f5f7fa",
            fg="#2d3436",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self.exam_search_entry = tk.Entry(
            search_frame, 
            width=30,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightbackground="#bdc3c7",
            highlightcolor="#3498db",
            highlightthickness=1
        )
        self.exam_search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(
            search_frame, 
            text="Search",
            command=self.search_exams,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT)

        # Exams list container with card-like styling
        list_container = tk.Frame(container, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with modern styling
        style = ttk.Style()
        style.configure("Treeview",
                      font=("Segoe UI", 10),
                      rowheight=25,
                      background="white",
                      fieldbackground="white",
                      foreground="#2d3436")
        style.configure("Treeview.Heading",
                     font=("Segoe UI", 10, "bold"),
                     background="#3498db",
                     foreground="black",
                     relief="flat")
        style.map("Treeview", background=[("selected", "#2980b9")])

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('id', 'title', 'questions', 'time_limit')
        self.exam_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.exam_tree.heading('id', text='ID')
        self.exam_tree.heading('title', text='Title')
        self.exam_tree.heading('questions', text='Questions')
        self.exam_tree.heading('time_limit', text='Time Limit (min)')
        
        self.exam_tree.column('id', width=80, anchor=tk.W)
        self.exam_tree.column('title', width=250, anchor=tk.W)
        self.exam_tree.column('questions', width=80, anchor=tk.CENTER)
        self.exam_tree.column('time_limit', width=120, anchor=tk.CENTER)

        self.exam_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.exam_tree.yview)

        # Action buttons frame with modern styling
        buttons_frame = tk.Frame(container, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        take_button = tk.Button(
            buttons_frame, 
            text="Take Exam",
            command=self.take_exam,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        take_button.pack(side=tk.LEFT, padx=5)
        
        details_button = tk.Button(
            buttons_frame, 
            text="View Details",
            command=self.view_exam_details,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        details_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_exams,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load exams
        self.load_exams()

    def setup_results_tab(self, parent):
        # Main container frame
        container = tk.Frame(parent, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results list container with card-like styling
        list_container = tk.Frame(container, bg="white", bd=1, relief="solid", highlightbackground="#dfe6e9")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with modern styling
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('exam', 'score', 'date')
        self.results_tree = ttk.Treeview(
            list_container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        self.results_tree.heading('exam', text='Exam')
        self.results_tree.heading('score', text='Score')
        self.results_tree.heading('date', text='Date')
        
        self.results_tree.column('exam', width=300, anchor=tk.W)
        self.results_tree.column('score', width=100, anchor=tk.CENTER)
        self.results_tree.column('date', width=150, anchor=tk.CENTER)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_tree.yview)

        # Action buttons frame
        buttons_frame = tk.Frame(container, bg="#f5f7fa")
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "cursor": "hand2"
        }
        
        details_button = tk.Button(
            buttons_frame, 
            text="View Details",
            command=self.view_result_details,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            **button_style
        )
        details_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(
            buttons_frame, 
            text="Refresh",
            command=self.load_results,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Load results
        self.load_results()

    def load_exams(self):
        try:
            # Clear existing items with animation
            for item in self.exam_tree.get_children():
                self.exam_tree.delete(item)
                
            # Show loading state
            #self.exam_tree.insert('', tk.END, values=("Loading...", "", "", ""))
            self.update()
            
            exams = Database.get_all_exams()
            
            for i, exam in enumerate(exams):
                self.exam_tree.insert('', tk.END, values=(
                    exam.id, exam.title, len(exam.questions), exam.time_limit),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load exams: {str(e)}")

    def search_exams(self):
        try:
            search_term = self.exam_search_entry.get().strip().lower()
            
            # Clear existing items with animation
            for item in self.exam_tree.get_children():
                self.exam_tree.delete(item)
                
            # Show searching state
            #self.exam_tree.insert('', tk.END, values=("Searching...", "", "", ""))
            self.update()
            
            exams = Database.get_all_exams()
            matches = []
            
            for exam in exams:
                if (search_term in exam.title.lower() or 
                    search_term in exam.description.lower()):
                    matches.append(exam)
                    
            if not matches:
                self.exam_tree.insert('', tk.END, values=("No results found", "", "", ""))
            else:
                for i, exam in enumerate(matches):
                    self.exam_tree.insert('', tk.END, values=(
                        exam.id, exam.title, len(exam.questions), exam.time_limit),
                        tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def view_exam_details(self):
        try:
            selected = self.exam_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select an exam to view", icon='warning')
                return

            exam_id = self.exam_tree.item(selected[0], 'values')[0]
            exam = Database.get_exam_by_id(exam_id)
            
            if not exam:
                messagebox.showerror("Error", "Exam not found", icon='error')
                return

            # Create a styled details dialog
            details = tk.Toplevel()
            details.title("Exam Details")
            details.geometry("400x300")
            details.resizable(False, False)
            
            # Header
            header = tk.Frame(details, bg="#3498db", height=50)
            header.pack(fill=tk.X)
            tk.Label(header, 
                    text="Exam Details", 
                    bg="#3498db", 
                    fg="white",
                    font=("Segoe UI", 12, "bold")).pack(pady=10)
            
            # Content
            content = tk.Frame(details, padx=20, pady=15)
            content.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(content, 
                    text=f"Title: {exam.title}", 
                    font=("Segoe UI", 10, "bold"),
                    anchor="w").pack(fill=tk.X, pady=5)
            
            tk.Label(content, 
                    text="Description:", 
                    font=("Segoe UI", 9, "bold"),
                    anchor="w").pack(fill=tk.X, pady=(10,0))
            desc_text = tk.Text(content, 
                              height=4, 
                              wrap=tk.WORD,
                              font=("Segoe UI", 9),
                              padx=5,
                              pady=5)
            desc_text.insert(tk.END, exam.description)
            desc_text.config(state=tk.DISABLED)
            desc_text.pack(fill=tk.X)
            
            tk.Label(content, 
                    text=f"Number of Questions: {len(exam.questions)}", 
                    font=("Segoe UI", 9),
                    anchor="w").pack(fill=tk.X, pady=5)
            
            tk.Label(content, 
                    text=f"Time Limit: {exam.time_limit} minutes", 
                    font=("Segoe UI", 9),
                    anchor="w").pack(fill=tk.X, pady=5)
            
            # Close button
            tk.Button(details, 
                     text="Close", 
                     command=details.destroy,
                     bg="#95a5a6",
                     fg="white",
                     bd=0,
                     padx=15,
                     pady=5).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show details: {str(e)}")

    def take_exam(self):
        try:
            selected = self.exam_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select an exam to take", icon='warning')
                return

            exam_id = self.exam_tree.item(selected[0], 'values')[0]
            exam = Database.get_exam_by_id(exam_id)
            
            if not exam:
                messagebox.showerror("Error", "Exam not found", icon='error')
                return

            # Check if already taken
            results = Database.get_results_by_student(self.controller.current_user.username)
            for result in results:
                if result.exam_id == exam_id:
                    confirm = messagebox.askyesno(
                        "Already Taken",
                        "You have already taken this exam. Do you want to take it again?",
                        icon='question'
                    )
                    if not confirm:
                        return
                    break

            # Start the exam with a confirmation
            confirm = messagebox.askyesno(
                "Start Exam",
                f"Are you ready to start '{exam.title}'?\n\n"
                f"Questions: {len(exam.questions)}\n"
                f"Time Limit: {exam.time_limit} minutes",
                icon='question'
            )
            
            if confirm:
                self.controller.show_frame(ExamPage, exam)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start exam: {str(e)}")

    def load_results(self):
        try:
            # Clear existing items with animation
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
                
            # Show loading state
            #self.results_tree.insert('', tk.END, values=("Loading...", "", ""))
            self.update()
            
            results = Database.get_results_by_student(self.controller.current_user.username)
            exams = {exam.id: exam for exam in Database.get_all_exams()}
            
            if not results:
                self.results_tree.insert('', tk.END, values=("No results found", "", ""))
                return
                
            for i, result in enumerate(results):
                exam = exams.get(result.exam_id)
                if exam:
                    self.results_tree.insert('', tk.END, values=(
                        exam.title, f"{result.score}%", result.date),
                        tags=('evenrow' if i % 2 == 0 else 'oddrow'))
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results: {str(e)}")

    def view_result_details(self):
        try:
            selected = self.results_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a result to view", icon='warning')
                return

            exam_title, score, date = self.results_tree.item(selected[0], 'values')
            
            results = Database.get_results_by_student(self.controller.current_user.username)
            exams = {exam.id: exam.title for exam in Database.get_all_exams()}
            exam_ids = {title: id for id, title in exams.items()}

            result = None
            for r in results:
                if r.exam_id in exam_ids and exams[r.exam_id] == exam_title and r.date == date:
                    result = r
                    break

            if result:
                ResultDetailsDialog(self, result)
            else:
                messagebox.showerror("Error", "Result details not found", icon='error')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view details: {str(e)}")

    def logout(self):
        confirm = messagebox.askyesno(
            "Confirm Logout",
            "Are you sure you want to logout?",
            icon='question'
        )
        if confirm:
            self.controller.current_user = None
            self.controller.show_frame(LoginPage)

# Exam Page


class ExamPage(tk.Frame):
    def __init__(self, parent, controller, exam):
        super().__init__(parent)
        self.controller = controller
        self.exam = exam
        self.configure(bg="#f5f7fa")  # Set background color

        # Load questions
        self.questions = []
        for question_id in exam.questions:
            question = Database.get_question_by_id(question_id)
            if question:
                self.questions.append(question)

        # Initialize variables
        self.current_question_index = 0
        self.answers = {}
        self.remaining_time = exam.time_limit * 60  # Convert to seconds

        # Create layout
        self.create_layout()

        # Start timer
        self.update_timer()

    def create_layout(self):
        # Top bar with exam info and timer
        top_frame = tk.Frame(self, bg="#2c3e50", padx=15, pady=10)
        top_frame.pack(fill=tk.X)
        
        # Exam title with modern styling
        exam_label = tk.Label(
            top_frame, 
            text=f"Exam: {self.exam.title}", 
            bg="#2c3e50", 
            fg="white",
            font=("Segoe UI", 12, "bold")
        )
        exam_label.pack(side=tk.LEFT)

        # Timer with modern styling
        self.timer_label = tk.Label(
            top_frame, 
            text="Time Remaining: 00:00:00", 
            bg="#2c3e50", 
            fg="white",
            font=("Segoe UI", 12)
        )
        self.timer_label.pack(side=tk.RIGHT)

        # Main content area with card-like styling
        content_frame = tk.Frame(self, bg="white", bd=1, relief="solid", padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Question number with modern styling
        self.question_number_label = tk.Label(
            content_frame, 
            text=f"Question 1 of {len(self.questions)}", 
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#2d3436"
        )
        self.question_number_label.pack(anchor=tk.W, pady=(0, 15))

        # Question text with card-like styling
        question_text_frame = tk.Frame(content_frame, bg="#f8f9fa", bd=1, relief="solid")
        question_text_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.question_text = tk.Text(
            question_text_frame, 
            wrap=tk.WORD, 
            height=5, 
            width=60, 
            font=("Segoe UI", 11),
            bg="#f8f9fa",
            fg="#2d3436",
            padx=10,
            pady=10,
            bd=0,
            highlightthickness=0
        )
        self.question_text.pack(fill=tk.BOTH, expand=True)
        self.question_text.config(state=tk.DISABLED)

        # Options frame
        self.options_frame = tk.Frame(content_frame, bg="white")
        self.options_frame.pack(fill=tk.X, pady=(0, 20))

        self.option_var = tk.IntVar()
        self.option_buttons = []

        for i in range(4):
            option_frame = tk.Frame(self.options_frame, bg="white")
            option_frame.pack(fill=tk.X, pady=5)

            # Modern radio button
            radio = tk.Radiobutton(
                option_frame, 
                variable=self.option_var, 
                value=i,
                bg="white",
                activebackground="white",
                selectcolor="#3498db"
            )
            radio.pack(side=tk.LEFT, padx=(0, 10))

            # Option text with card-like styling
            text = tk.Label(
                option_frame, 
                text="", 
                wraplength=500,
                justify=tk.LEFT, 
                font=("Segoe UI", 11),
                bg="#f8f9fa",
                fg="#2d3436",
                bd=1,
                relief="solid",
                padx=10,
                pady=8
            )
            text.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.option_buttons.append((radio, text))

        # Navigation buttons frame
        nav_frame = tk.Frame(content_frame, bg="white")
        nav_frame.pack(fill=tk.X, pady=(20, 0))

        # Previous button with modern styling
        self.prev_button = tk.Button(
            nav_frame, 
            text="← Previous", 
            command=self.prev_question,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            font=("Segoe UI", 10),
            bd=0,
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        self.prev_button.pack(side=tk.LEFT)

        # Next button with modern styling
        self.next_button = tk.Button(
            nav_frame, 
            text="Next →", 
            command=self.next_question,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 10),
            bd=0,
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Submit button with modern styling
        self.submit_button = tk.Button(
            nav_frame, 
            text="Submit Exam", 
            command=self.confirm_submit,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        self.submit_button.pack(side=tk.RIGHT)

        # Question navigation buttons frame
        nav_questions_frame = tk.Frame(content_frame, bg="white")
        nav_questions_frame.pack(fill=tk.X, pady=(20, 0))

        tk.Label(
            nav_questions_frame,
            text="Jump to question:",
            bg="white",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)

        self.question_buttons_frame = tk.Frame(nav_questions_frame, bg="white")
        self.question_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create question number buttons with modern styling
        self.question_buttons = []
        row, col = 0, 0
        for i in range(len(self.questions)):
            btn = tk.Button(
                self.question_buttons_frame, 
                text=str(i+1), 
                width=3,
                command=lambda idx=i: self.jump_to_question(idx),
                bg="#ecf0f1",
                fg="#2d3436",
                activebackground="#bdc3c7",
                font=("Segoe UI", 9),
                bd=0,
                relief="flat"
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.question_buttons.append(btn)

            col += 1
            if col > 9:  # 10 buttons per row
                col = 0
                row += 1

        # Show first question
        self.show_question(0)

    def show_question(self, index):
        if 0 <= index < len(self.questions):
            self.current_question_index = index
            question = self.questions[index]

            # Update question number
            self.question_number_label.config(
                text=f"Question {index+1} of {len(self.questions)}")

            # Update question text
            self.question_text.config(state=tk.NORMAL)
            self.question_text.delete(1.0, tk.END)
            self.question_text.insert(tk.END, question.text)
            self.question_text.config(state=tk.DISABLED)

            # Update options
            for i, (radio, text) in enumerate(self.option_buttons):
                if i < len(question.options):
                    text.config(text=question.options[i])
                    radio.config(state=tk.NORMAL)
                else:
                    text.config(text="")
                    radio.config(state=tk.DISABLED)

            # Set selected option if previously answered
            if index in self.answers:
                self.option_var.set(self.answers[index])
            else:
                self.option_var.set(-1)  # No selection

            # Update navigation buttons
            self.prev_button.config(
                state=tk.NORMAL if index > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if index < len(
                self.questions) - 1 else tk.DISABLED)

            # Update question buttons
            for i, btn in enumerate(self.question_buttons):
                if i == index:
                    btn.config(bg="#3498db", fg="white")  # Current question
                elif i in self.answers:
                    btn.config(bg="#2ecc71", fg="white")  # Answered
                else:
                    btn.config(bg="#ecf0f1", fg="#2d3436")  # Not answered

    def prev_question(self):
        # Save current answer
        self.save_current_answer()

        # Show previous question
        if self.current_question_index > 0:
            self.show_question(self.current_question_index - 1)

    def next_question(self):
        # Save current answer
        self.save_current_answer()

        # Show next question
        if self.current_question_index < len(self.questions) - 1:
            self.show_question(self.current_question_index + 1)

    def jump_to_question(self, index):
        # Save current answer
        self.save_current_answer()

        # Show selected question
        self.show_question(index)

    def save_current_answer(self):
        # Get selected option
        selected = self.option_var.get()

        # Save answer if an option is selected
        if selected != -1:
            self.answers[self.current_question_index] = selected

    def update_timer(self):
        # Update timer display
        hours = self.remaining_time // 3600
        minutes = (self.remaining_time % 3600) // 60
        seconds = self.remaining_time % 60

        self.timer_label.config(
            text=f"Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")

        # Decrement time
        self.remaining_time -= 1

        # Check if time is up
        if self.remaining_time < 0:
            messagebox.showinfo(
                "Time's Up", "Your time is up! The exam will be submitted automatically.")
            self.submit_exam()
            return

        # Schedule next update
        self.after(1000, self.update_timer)

    def confirm_submit(self):
        # Save current answer
        self.save_current_answer()

        # Count unanswered questions
        unanswered = len(self.questions) - len(self.answers)

        # Confirm submission
        if unanswered > 0:
            if not messagebox.askyesno("Confirm Submission",
                                       f"You have {unanswered} unanswered questions. Are you sure you want to submit?"):
                return
        else:
            if not messagebox.askyesno("Confirm Submission", "Are you sure you want to submit your exam?"):
                return

        # Submit exam
        self.submit_exam()

    def submit_exam(self):
        # Calculate score
        correct = 0
        for i, question in enumerate(self.questions):
            if i in self.answers and self.answers[i] == question.correct_answer:
                correct += 1

        score = round((correct / len(self.questions))
                      * 100, 2) if self.questions else 0

        # Create result
        result = Result(
            student_username=self.controller.current_user.username,
            exam_id=self.exam.id,
            score=score,
            answers=self.answers
        )

        # Save result
        Database.add_result(result)

        # Show score
        messagebox.showinfo("Exam Completed", f"Your score: {score}%")

        # Return to dashboard
        self.controller.show_frame(StudentDashboard)

# Student Dialog

class StudentDialog:
    def __init__(self, parent, title, student=None):
        self.result = None

        # Create dialog window with modern styling
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set background color
        self.dialog.configure(bg="#f5f5f5")

        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Main container with card-like styling
        container = tk.Frame(self.dialog, bg="white", bd=1, relief="solid", padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Form styling
        label_style = {"font": ("Segoe UI", 10), "bg": "white", "fg": "#34495e"}
        entry_style = {
            "font": ("Segoe UI", 10),
            "bd": 1,
            "relief": "solid",
            "highlightbackground": "#bdc3c7",
            "highlightcolor": "#3498db",
            "highlightthickness": 1
        }

        # Username field
        tk.Label(container, text="Username:", **label_style).grid(
            row=0, column=0, sticky=tk.W, pady=8)
        self.username_entry = tk.Entry(container, width=25, **entry_style)
        self.username_entry.grid(row=0, column=1, pady=8, sticky=tk.W)

        # Password field
        tk.Label(container, text="Password:", **label_style).grid(
            row=1, column=0, sticky=tk.W, pady=8)
        self.password_entry = tk.Entry(container, width=25, show="*", **entry_style)
        self.password_entry.grid(row=1, column=1, pady=8, sticky=tk.W)

        if student:
            tk.Label(container, 
                    text="(Leave blank to keep current password)", 
                    font=("Segoe UI", 8), 
                    bg="white", 
                    fg="#7f8c8d").grid(
                row=2, column=1, sticky=tk.W)

        # Full Name field
        tk.Label(container, text="Full Name:", **label_style).grid(
            row=3, column=0, sticky=tk.W, pady=8)
        self.fullname_entry = tk.Entry(container, width=25, **entry_style)
        self.fullname_entry.grid(row=3, column=1, pady=8, sticky=tk.W)

        # Buttons frame
        buttons_frame = tk.Frame(container, bg="white")
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

        # Button styling
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "cursor": "hand2"
        }

        # Save button with modern style
        save_button = tk.Button(
            buttons_frame, 
            text="Save", 
            command=self.save,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        save_button.pack(side=tk.LEFT, padx=10)

        # Cancel button with modern style
        cancel_button = tk.Button(
            buttons_frame, 
            text="Cancel", 
            command=self.cancel,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        cancel_button.pack(side=tk.LEFT)

        # Fill form if editing
        if student:
            self.username_entry.insert(0, student.username)
            self.username_entry.config(state=tk.DISABLED)
            self.fullname_entry.insert(0, student.full_name)

        # Wait for dialog to close
        self.dialog.wait_window()

    def save(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        fullname = self.fullname_entry.get()

        if not username or not fullname:
            messagebox.showerror("Error", "Username and Full Name are required")
            return

        self.result = (username, password, fullname)
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

# Question Dialog


class QuestionDialog:
    def __init__(self, parent, title, question=None):
        self.result = None

        # Create dialog window with modern styling
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Set background color
        self.dialog.configure(bg="#f5f5f5")

        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Main container with card-like styling
        container = tk.Frame(self.dialog, bg="white", bd=1, relief="solid", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Form styling
        label_style = {"font": ("Segoe UI", 10), "bg": "white", "fg": "#34495e"}
        entry_style = {
            "font": ("Segoe UI", 10),
            "bd": 1,
            "relief": "solid",
            "highlightbackground": "#bdc3c7",
            "highlightcolor": "#3498db",
            "highlightthickness": 1
        }

        # Question text
        tk.Label(container, text="Question:", **label_style).grid(
            row=0, column=0, sticky=tk.NW, pady=8)
        
        self.question_text = tk.Text(
            container, 
            height=5, 
            width=50,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            bd=1,
            relief="solid",
            padx=5,
            pady=5
        )
        self.question_text.grid(row=0, column=1, pady=8, sticky=tk.W)

        # Category
        tk.Label(container, text="Category:", **label_style).grid(
            row=1, column=0, sticky=tk.W, pady=8)
        self.category_entry = tk.Entry(container, width=30, **entry_style)
        self.category_entry.grid(row=1, column=1, pady=8, sticky=tk.W)

        # Options
        tk.Label(container, text="Options:", **label_style).grid(
            row=2, column=0, sticky=tk.NW, pady=8)

        options_frame = tk.Frame(container, bg="white")
        options_frame.grid(row=2, column=1, pady=8, sticky=tk.W)

        self.option_entries = []
        self.correct_var = tk.IntVar()

        for i in range(4):
            option_frame = tk.Frame(options_frame, bg="white")
            option_frame.pack(fill=tk.X, pady=5)

            # Modern radio button
            radio = tk.Radiobutton(
                option_frame, 
                variable=self.correct_var, 
                value=i,
                bg="white",
                activebackground="white",
                selectcolor="#3498db"
            )
            radio.pack(side=tk.LEFT, padx=(0, 10))

            # Option entry with card-like styling
            entry = tk.Entry(
                option_frame, 
                width=40,
                **entry_style
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.option_entries.append(entry)

        # Buttons frame
        buttons_frame = tk.Frame(container, bg="white")
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        # Button styling
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "cursor": "hand2"
        }

        # Save button with modern style
        save_button = tk.Button(
            buttons_frame, 
            text="Save", 
            command=self.save,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        save_button.pack(side=tk.LEFT, padx=10)

        # Cancel button with modern style
        cancel_button = tk.Button(
            buttons_frame, 
            text="Cancel", 
            command=self.cancel,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        cancel_button.pack(side=tk.LEFT)

        # Fill form if editing
        if question:
            self.question_text.insert(tk.END, question.text)
            self.category_entry.insert(0, question.category)

            for i, option in enumerate(question.options):
                if i < len(self.option_entries):
                    self.option_entries[i].insert(0, option)

            self.correct_var.set(question.correct_answer)

        # Wait for dialog to close
        self.dialog.wait_window()

    def save(self):
        text = self.question_text.get(1.0, tk.END).strip()
        category = self.category_entry.get()

        options = [entry.get() for entry in self.option_entries]
        correct_answer = self.correct_var.get()

        if not text or not category:
            messagebox.showerror("Error", "Question text and category are required")
            return

        if not all(options):
            messagebox.showerror("Error", "All options must be filled")
            return

        self.result = (text, options, correct_answer, category)
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

# Exam Dialog
class ExamDialog:
    def __init__(self, parent, title, exam=None):
        self.result = None
        self.all_questions = Database.get_all_questions()
        
        # Create dialog window with modern styling
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("800x650")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#f5f5f5")
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Main container with card-like styling
        container = tk.Frame(self.dialog, bg="white", bd=1, relief="solid", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Form styling
        label_style = {"font": ("Segoe UI", 10), "bg": "white", "fg": "#34495e"}
        entry_style = {
            "font": ("Segoe UI", 10),
            "bd": 1,
            "relief": "solid",
            "highlightbackground": "#bdc3c7",
            "highlightcolor": "#3498db",
            "highlightthickness": 1
        }

        # Title
        tk.Label(container, text="Title:", **label_style).grid(
            row=0, column=0, sticky=tk.W, pady=8)
        self.title_entry = tk.Entry(container, width=50, **entry_style)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=8)
        
        # Description
        tk.Label(container, text="Description:", **label_style).grid(
            row=1, column=0, sticky=tk.NW, pady=8)
        self.description_text = tk.Text(
            container, 
            height=4, 
            width=50,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            bd=1,
            relief="solid",
            padx=5,
            pady=5
        )
        self.description_text.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=8)
        
        # Time limit
        tk.Label(container, text="Time Limit (minutes):", **label_style).grid(
            row=2, column=0, sticky=tk.W, pady=8)
        self.time_limit_var = tk.IntVar(value=60)
        self.time_limit_entry = tk.Entry(
            container, 
            width=10, 
            textvariable=self.time_limit_var,
            **entry_style
        )
        self.time_limit_entry.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        # Questions section header
        tk.Label(container, text="Available Questions:", **label_style).grid(
            row=3, column=0, sticky=tk.W, pady=8)
        tk.Label(container, text="Selected Questions:", **label_style).grid(
            row=3, column=2, sticky=tk.W, pady=8)
        
        # Search frame with modern styling
        search_frame = tk.Frame(container, bg="white")
        search_frame.grid(row=4, column=0, sticky=tk.W, pady=(0, 8))
        
        tk.Label(search_frame, text="Search:", **label_style).pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(
            search_frame, 
            width=20,
            **entry_style
        )
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = tk.Button(
            search_frame, 
            text="Search",
            command=self.search_questions,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 9),
            bd=0,
            padx=12,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        search_button.pack(side=tk.LEFT)

        # Available questions list with modern styling
        available_frame = tk.Frame(container, bg="white", bd=1, relief="solid")
        available_frame.grid(row=5, column=0, rowspan=3, sticky=tk.NSEW, pady=8)
        
        scrollbar1 = tk.Scrollbar(available_frame)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.available_listbox = tk.Listbox(
            available_frame, 
            width=30, 
            height=15, 
            yscrollcommand=scrollbar1.set,
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 9),
            bd=0,
            highlightthickness=0,
            selectbackground="#3498db",
            selectforeground="white"
        )
        self.available_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.config(command=self.available_listbox.yview)
        
        # Move buttons with modern styling
        buttons_frame = tk.Frame(container, bg="white")
        buttons_frame.grid(row=5, column=1, pady=8)
        
        add_button = tk.Button(
            buttons_frame, 
            text="➔",  # Right arrow symbol
            command=self.add_question,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            font=("Segoe UI", 12),
            bd=0,
            padx=8,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        add_button.pack(pady=5)
        
        remove_button = tk.Button(
            buttons_frame, 
            text="⬅",  # Left arrow symbol
            command=self.remove_question,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            font=("Segoe UI", 12),
            bd=0,
            padx=8,
            pady=3,
            relief="flat",
            cursor="hand2"
        )
        remove_button.pack(pady=5)
        
        # Selected questions list with modern styling
        selected_frame = tk.Frame(container, bg="white", bd=1, relief="solid")
        selected_frame.grid(row=5, column=2, rowspan=3, sticky=tk.NSEW, pady=8)
        
        scrollbar2 = tk.Scrollbar(selected_frame)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.selected_listbox = tk.Listbox(
            selected_frame, 
            width=30, 
            height=15, 
            yscrollcommand=scrollbar2.set,
            bg="white",
            fg="#2d3436",
            font=("Segoe UI", 9),
            bd=0,
            highlightthickness=0,
            selectbackground="#3498db",
            selectforeground="white"
        )
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.selected_listbox.yview)
        
        # Dictionary to map listbox indices to question IDs
        self.available_question_ids = {}
        self.selected_question_ids = {}
        
        # Action buttons frame
        action_buttons_frame = tk.Frame(container, bg="white")
        action_buttons_frame.grid(row=8, column=0, columnspan=3, pady=(15, 0))
        
        # Button styling
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "cursor": "hand2"
        }
        
        # Save button with modern style
        save_button = tk.Button(
            action_buttons_frame, 
            text="Save", 
            command=self.save,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        save_button.pack(side=tk.LEFT, padx=10)
        
        # Cancel button with modern style
        cancel_button = tk.Button(
            action_buttons_frame, 
            text="Cancel", 
            command=self.cancel,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        cancel_button.pack(side=tk.LEFT)
        
        # Fill form if editing
        self.exam_question_ids = []
        if exam:
            self.title_entry.insert(0, exam.title)
            self.description_text.insert(tk.END, exam.description)
            self.time_limit_var.set(exam.time_limit)
            self.exam_question_ids = exam.questions.copy()
        
        # Load questions
        self.load_questions()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def load_questions(self):
        # Clear listboxes and mappings
        self.available_listbox.delete(0, tk.END)
        self.selected_listbox.delete(0, tk.END)
        self.available_question_ids = {}
        self.selected_question_ids = {}
        
        # Add questions to appropriate listboxes
        for question in self.all_questions:
            # Truncate question text if too long
            text = question.text[:50] + "..." if len(question.text) > 50 else question.text
            
            if question.id in self.exam_question_ids:
                index = self.selected_listbox.size()
                self.selected_listbox.insert(tk.END, text)
                self.selected_listbox.itemconfig(index, {'bg': '#e8f5e9'})  # Light green background
                self.selected_question_ids[index] = question.id
            else:
                index = self.available_listbox.size()
                self.available_listbox.insert(tk.END, text)
                self.available_question_ids[index] = question.id
    
    def search_questions(self):
        search_term = self.search_entry.get().lower()
        
        # Clear available listbox and mapping
        self.available_listbox.delete(0, tk.END)
        self.available_question_ids = {}
        
        # Add matching questions to available listbox
        for question in self.all_questions:
            if question.id not in self.exam_question_ids and (
                search_term in question.text.lower() or 
                search_term in question.category.lower()):
                
                # Truncate question text if too long
                text = question.text[:50] + "..." if len(question.text) > 50 else question.text
                
                index = self.available_listbox.size()
                self.available_listbox.insert(tk.END, text)
                self.available_question_ids[index] = question.id
    
    def add_question(self):
        # Get selected question
        selected = self.available_listbox.curselection()
        if not selected:
            return
        
        # Get question index and ID
        index = selected[0]
        question_id = self.available_question_ids.get(index)
        
        if question_id and question_id not in self.exam_question_ids:
            self.exam_question_ids.append(question_id)
        
        # Reload questions
        self.load_questions()
    
    def remove_question(self):
        # Get selected question
        selected = self.selected_listbox.curselection()
        if not selected:
            return
        
        # Get question index and ID
        index = selected[0]
        question_id = self.selected_question_ids.get(index)
        
        if question_id and question_id in self.exam_question_ids:
            self.exam_question_ids.remove(question_id)
        
        # Reload questions
        self.load_questions()
    
    def save(self):
        title = self.title_entry.get()
        description = self.description_text.get(1.0, tk.END).strip()
        time_limit = self.time_limit_var.get()
        
        if not title:
            messagebox.showerror("Error", "Title is required")
            return
        
        if not self.exam_question_ids:
            messagebox.showerror("Error", "At least one question must be selected")
            return
        
        self.result = (title, description, self.exam_question_ids, time_limit)
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()

# Import Questions Dialog


class ImportQuestionsDialog:
    def __init__(self, parent):
        self.result = None

        # Create dialog window with modern styling
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Questions")
        self.dialog.geometry("450x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#f5f5f5")

        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Main container with card-like styling
        container = tk.Frame(self.dialog, bg="white", bd=1, relief="solid", padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Form styling
        label_style = {"font": ("Segoe UI", 10), "bg": "white", "fg": "#34495e"}
        entry_style = {
            "font": ("Segoe UI", 10),
            "bd": 1,
            "relief": "solid",
            "highlightbackground": "#bdc3c7",
            "highlightcolor": "#3498db",
            "highlightthickness": 1
        }

        # Number of questions
        tk.Label(container, text="Number of Questions (1-50):", **label_style).grid(
            row=0, column=0, sticky=tk.W, pady=10)
        self.amount_var = tk.IntVar(value=10)
        self.amount_entry = tk.Entry(
            container, 
            width=10, 
            textvariable=self.amount_var,
            **entry_style
        )
        self.amount_entry.grid(row=0, column=1, sticky=tk.W, pady=10)

        # Category
        tk.Label(container, text="Category:", **label_style).grid(
            row=1, column=0, sticky=tk.W, pady=10)
        self.category_var = tk.StringVar()

        # Categories from Open Trivia DB
        categories = [
            ("Any Category", ""),
            ("General Knowledge", "9"),
            ("Entertainment: Books", "10"),
            ("Entertainment: Film", "11"),
            ("Entertainment: Music", "12"),
            ("Entertainment: Television", "14"),
            ("Science & Nature", "17"),
            ("Science: Computers", "18"),
            ("Science: Mathematics", "19"),
            ("Mythology", "20"),
            ("Sports", "21"),
            ("Geography", "22"),
            ("History", "23"),
            ("Politics", "24"),
            ("Art", "25"),
            ("Animals", "27"),
            ("Vehicles", "28"),
            ("Science: Gadgets", "30")
        ]

        # Modern combobox styling
        style = ttk.Style()
        style.configure('TCombobox', 
                        font=("Segoe UI", 10),
                        borderwidth=1,
                        relief="solid",
                        padding=5)

        self.category_combobox = ttk.Combobox(
            container, 
            textvariable=self.category_var, 
            width=28,
            style='TCombobox'
        )
        self.category_combobox['values'] = [cat[0] for cat in categories]
        self.category_combobox.current(0)
        self.category_combobox.grid(row=1, column=1, sticky=tk.W, pady=10)

        # Store category IDs
        self.categories = {cat[0]: cat[1] for cat in categories}

        # Buttons frame
        buttons_frame = tk.Frame(container, bg="white")
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        # Button styling
        button_style = {
            "font": ("Segoe UI", 10),
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "cursor": "hand2"
        }

        # Import button with modern style
        import_button = tk.Button(
            buttons_frame, 
            text="Import", 
            command=self.import_questions,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            **button_style
        )
        import_button.pack(side=tk.LEFT, padx=10)

        # Cancel button with modern style
        cancel_button = tk.Button(
            buttons_frame, 
            text="Cancel", 
            command=self.cancel,
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            **button_style
        )
        cancel_button.pack(side=tk.LEFT)

        # Wait for dialog to close
        self.dialog.wait_window()

    def import_questions(self):
        amount = self.amount_var.get()
        category_name = self.category_var.get()
        category_id = self.categories.get(category_name, "")

        if amount <= 0 or amount > 50:
            messagebox.showerror(
                "Error", "Number of questions must be between 1 and 50")
            return

        self.result = (amount, category_id)
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

# Result Details Dialog


class ResultDetailsDialog:
    def __init__(self, parent, result):
        self.result = result

        # Create dialog window with modern styling
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Result Details")
        self.dialog.geometry("750x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg="#f5f5f5")

        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Get exam and questions
        self.exam = Database.get_exam_by_id(result.exam_id)
        self.questions = []

        if self.exam:
            for question_id in self.exam.questions:
                question = Database.get_question_by_id(question_id)
                if question:
                    self.questions.append(question)

        # Create layout
        self.create_layout()

        # Wait for dialog to close
        self.dialog.wait_window()

    def create_layout(self):
        # Main container with card-like styling
        main_frame = tk.Frame(self.dialog, bg="white", bd=1, relief="solid")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame with summary (header style)
        top_frame = tk.Frame(main_frame, bg="#3498db", padx=15, pady=10)
        top_frame.pack(fill=tk.X)

        # Exam title with modern styling
        if self.exam:
            tk.Label(top_frame, 
                    text=f"Exam: {self.exam.title}", 
                    font=("Segoe UI", 12, "bold"),
                    bg="#3498db",
                    fg="white").pack(anchor=tk.W)

        # Score and date in a horizontal frame
        info_frame = tk.Frame(top_frame, bg="#3498db")
        info_frame.pack(fill=tk.X, pady=(5, 0))

        # Score with modern styling
        tk.Label(info_frame, 
                text=f"Score: {self.result.score}%", 
                font=("Segoe UI", 11),
                bg="#3498db",
                fg="white").pack(side=tk.LEFT, padx=(0, 20))

        # Date with modern styling
        tk.Label(info_frame, 
                text=f"Date: {self.result.date}", 
                font=("Segoe UI", 11),
                bg="#3498db",
                fg="white").pack(side=tk.LEFT)

        # Questions frame with scrollbar
        questions_frame = tk.Frame(main_frame, bg="white")
        questions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas with modern scrollbar
        canvas = tk.Canvas(questions_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            questions_frame, 
            orient="vertical", 
            command=canvas.yview,
            style="Vertical.TScrollbar"
        )
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add questions with modern card styling
        for i, question in enumerate(self.questions):
            # Question frame with card-like styling
            question_frame = tk.Frame(
                scrollable_frame, 
                bg="white",
                bd=1,
                relief="solid",
                padx=10,
                pady=10
            )
            question_frame.pack(fill=tk.X, pady=5, padx=5)

            # Question number and text
            header_frame = tk.Frame(question_frame, bg="white")
            header_frame.pack(fill=tk.X, pady=(0, 10))

            tk.Label(header_frame, 
                    text=f"Question {i+1}", 
                    font=("Segoe UI", 10, "bold"),
                    bg="white").pack(side=tk.LEFT)

            # Show answer status
            if i in self.result.answers:
                if self.result.answers[i] == question.correct_answer:
                    status = "✓ Correct"
                    color = "#2ecc71"
                else:
                    status = "✗ Incorrect"
                    color = "#e74c3c"
            else:
                status = "Not answered"
                color = "#f39c12"

            tk.Label(header_frame, 
                    text=status, 
                    font=("Segoe UI", 10),
                    fg=color,
                    bg="white").pack(side=tk.RIGHT)

            # Question text with modern styling
            question_text = tk.Text(
                question_frame, 
                wrap=tk.WORD, 
                height=3, 
                width=70,
                font=("Segoe UI", 10),
                bg="#f8f9fa",
                padx=5,
                pady=5,
                bd=0,
                highlightthickness=0
            )
            question_text.insert(tk.END, question.text)
            question_text.config(state=tk.DISABLED)
            question_text.pack(fill=tk.X, pady=(0, 10))

            # Options with modern styling
            for j, option in enumerate(question.options):
                option_frame = tk.Frame(question_frame, bg="white")
                option_frame.pack(fill=tk.X, pady=2)

                # Determine option background color
                bg_color = "#f8f9fa"  # Default
                if j == question.correct_answer:
                    bg_color = "#e8f5e9"  # Light green for correct answer
                if i in self.result.answers and self.result.answers[i] == j:
                    if j == question.correct_answer:
                        bg_color = "#d4edda"  # Correct answer selected
                    else:
                        bg_color = "#f8d7da"  # Wrong answer selected

                # Option label with card-like styling
                option_label = tk.Label(
                    option_frame, 
                    text=option, 
                    wraplength=600,
                    justify=tk.LEFT, 
                    bg=bg_color,
                    fg="#2d3436",
                    font=("Segoe UI", 10),
                    padx=10,
                    pady=8,
                    bd=0,
                    relief="solid",
                    anchor="w"
                )
                option_label.pack(fill=tk.X, expand=True)

        # Close button with modern styling
        close_button = tk.Button(
            main_frame, 
            text="Close", 
            command=self.dialog.destroy,
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            font=("Segoe UI", 10),
            bd=0,
            padx=20,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        close_button.pack(pady=10)

# Main function


def main():
    app = ExamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
