from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Hour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time_slot = db.Column(db.String(20), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    hour_id = db.Column(db.Integer, db.ForeignKey('hour.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.Boolean, default=False)  # True for Present, False for Absent


@app.route('/sections')
def get_sections():
    sections = Section.query.all()
    return jsonify([{"id": sec.id, "name": sec.name} for sec in sections])

@app.route('/hours/<int:section_id>')
def get_hours(section_id):
    hours = Hour.query.filter_by(section_id=section_id).all()
    return jsonify([{"id": hour.id, "time_slot": hour.time_slot} for hour in hours])

@app.route('/hours')
def hours():
    return render_template('hours.html')

@app.route('/students')
def students():
    return render_template('students.html')


@app.route('/students/<int:section_id>')
def get_students(section_id):
    students = Student.query.filter_by(section_id=section_id).all()
    return jsonify([{"id": student.id, "reg_no": student.reg_no, "name": student.name} for student in students])

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    student_id = data.get("student_id")
    hour_id = data.get("hour_id")
    status = data.get("status")

    existing_attendance = Attendance.query.filter_by(student_id=student_id, hour_id=hour_id, date=datetime.utcnow().date()).first()
    if existing_attendance:
        existing_attendance.status = status
    else:
        new_attendance = Attendance(student_id=student_id, hour_id=hour_id, date=datetime.utcnow(), status=status)
        db.session.add(new_attendance)

    db.session.commit()
    return jsonify({"message": "Attendance marked successfully"})


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return render_template('index.html')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username already exists")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Ensure the database file exists
    if not os.path.exists('attendance.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)

