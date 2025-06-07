from flask import Flask, render_template, request, redirect, url_for, session
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Configure MySQL connection
# MySQL Connection
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

# --- Email OTP Sending Function ---
def send_otp(email):
    otp = random.randint(1111, 9999)
    subject = 'OTP for Registration'
    body = f"Hello!\n\nYour OTP is: {otp}"

    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    return otp
def send_student_confirmation_email(roll, name, age, email, branch, college):
    subject = f'Student Registration Successful'
    body = (
        f"Hello {name},\n\n"
        f"Welcome to {college}!\n"
        f"Here are your registration details:\n"
        f"Roll Number: {roll}\n"
        f"Age: {age}\n"
        f"Branch: {branch}\n\n"
        f"Thank you for registering."
    )

    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
def send_teacher_confirmation_email(name, age, email, department, college):
    subject = f'Teacher Registration Successful'
    body = (
        f"Hello {name},\n\n"
        f"Welcome to {college}!\n"
        f"Here are your registration details:\n"
        f"Age: {age}\n"
        f"Department: {department}\n\n"
        f"Thank you for registering."
    )

    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create_college', methods=['GET', 'POST'])
def create_college():
    if request.method == 'POST':
        name = request.form['college_name']
        cursor.execute("INSERT INTO colleges (name) VALUES (%s)", (name,))
        conn.commit()
        return redirect(url_for('home'))
    return render_template('create_college.html')

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        session['student_data'] = {
            'college': request.form['college'],
            'roll': request.form['roll'],
            'name': request.form['name'],
            'age': request.form['age'],
            'email': request.form['email'],
            'branch': request.form['branch']
        }
        session['otp'] = send_otp(request.form['email'])
        return redirect(url_for('verify_otp_student'))
    return render_template('add_student.html')

@app.route('/verify_otp_student', methods=['GET', 'POST'])
def verify_otp_student():
    if request.method == 'POST':
        if int(request.form['otp']) == session['otp']:
            data = session['student_data']
            college_name = data['college']
            cursor.execute("SELECT name FROM colleges WHERE name = %s", (college_name,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO colleges (name) VALUES (%s)", (college_name,))
                conn.commit()
            cursor.execute(
                "INSERT INTO students (roll, name, age, email, branch, college_name) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['roll'], data['name'], data['age'], data['email'], data['branch'], college_name)
            )
            conn.commit()

            send_student_confirmation_email(
                data['roll'], data['name'], data['age'], data['email'], data['branch'], college_name
            )

            session.pop('student_data', None)
            session.pop('otp', None)
            return "Student Registered Successfully. Check your email."
        else:
            return "Incorrect OTP. Try again."
    return render_template('verify_otp_student.html')

@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    students = []
    if request.method == 'POST':
        college = request.form['college'].strip()

        # Print the entered college name in terminal
        print(f"College entered by user: {college}")

        cursor.execute(
            "SELECT roll, name, age, email, branch, college_name FROM students WHERE LOWER(college_name) = LOWER(%s)",
            (college,)
        )
        rows = cursor.fetchall()
        print(f"Fetched rows: {rows}")

        students = [
            {
                'roll': r[0],
                'name': r[1],
                'age': r[2],
                'email': r[3],
                'branch': r[4],
                'college': r[5]
            }
            for r in rows
        ]
    return render_template('view_students.html', students=students)


@app.route('/view_teachers', methods=['GET', 'POST'])
def view_teachers():
    teachers = []
    if request.method == 'POST':
        college = request.form['college'].strip()
        cursor.execute(
               "SELECT id, name, age, email, subject, college_name FROM teachers WHERE LOWER(college_name) = LOWER(%s)", 
                  (college,)
        )

        rows = cursor.fetchall()
        teachers = [
            {
                'id': r[0],
                'name': r[1],
                'age': r[2],
                'email': r[3],
                'subject': r[4],
                'college_name': r[5]
            } for r in rows
        ]
    return render_template('view_teachers.html', teachers=teachers)


@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        session['teacher_data'] = {
            'college': request.form['college'],
            'name': request.form['name'],
            'age': request.form['age'],
            'email': request.form['email'],
            'department': request.form['department']
        }
        session['otp'] = send_otp(request.form['email'])
        return redirect(url_for('verify_otp_teacher'))
    return render_template('add_teacher.html')

@app.route('/verify_otp_teacher', methods=['GET', 'POST'])
def verify_otp_teacher():
    if request.method == 'POST':
        if int(request.form['otp']) == session['otp']:
            data = session['teacher_data']
            cursor.execute(
                "INSERT INTO teachers (name, age, email, department, college_name) VALUES (%s, %s, %s, %s, %s)",
                (data['name'], data['age'], data['email'], data['department'], data['college'])
            )
            conn.commit()

            send_teacher_confirmation_email(
                data['name'], data['age'], data['email'], data['department'], data['college']
            )

            session.pop('teacher_data', None)
            session.pop('otp', None)
            return "Teacher Registered Successfully. Check your email."
        else:
            return "Incorrect OTP. Try again."
    return render_template('verify_otp_teacher.html')

if __name__ == '__main__':
    app.run(debug=True)
