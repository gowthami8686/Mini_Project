from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from fpdf import FPDF
from flask import send_file
from flask_mail import Mail, Message
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure Flask-Mail for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'gowthami.seepana08@gmail.com'  # Replace with your Gmail ID
app.config['MAIL_PASSWORD'] = 'sodf jjgd kmtn hvaw'  # Replace with generated App Password
app.config['MAIL_DEFAULT_SENDER'] = 'gowthami.seepana08@gmail.com'

mail = Mail(app)

# ✅ List of recipient emails (Modify as needed)
email_recipients = [
    "lnawscloud@gmail.com",
    'lakshminarayana4848@gmail.com',
    'gowthami.seepana08@gmail.com',
    'seepanagowthami2005@gmail.com'
]

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

@app.route('/get_attendance/<int:hour_id>')
def get_attendance(hour_id):
    today = datetime.utcnow().date()
    attendance_data = Attendance.query.filter_by(hour_id=hour_id, date=today).all()

    results = []
    for record in attendance_data:
        student = Student.query.get(record.student_id)
        results.append({
            "id": student.id,
            "name": student.name,
            "reg_no": student.reg_no,
            "status": record.status  # True for Present, False for Absent
        })

    return jsonify(results)

@app.route('/attendance_summary/<int:section_id>/<int:hour_id>')
def attendance_summary(section_id, hour_id):
    today = datetime.utcnow().date()
    
    # Fetch students belonging to the selected section
    students = Student.query.filter_by(section_id=section_id).all()

    present_students = []
    absent_students = []

    for student in students:
        record = Attendance.query.filter_by(student_id=student.id, hour_id=hour_id, date=today).first()
        if record and record.status:
            present_students.append({"id": student.id, "name": student.name, "reg_no": student.reg_no})
        else:
            absent_students.append({"id": student.id, "name": student.name, "reg_no": student.reg_no})

    return jsonify({
        "present": present_students,
        "absent": absent_students
    })


@app.route('/view_stats')
def view_stats():
    return render_template('view_stats.html')


@app.route('/generate_report/<int:section_id>/<string:date>')
def generate_report(section_id, date):
    # Fetch section name
    section = db.session.get(Section, section_id)
    section_name = section.name if section else f"Section {section_id}"  # Fallback in case section is not found

    # Fetch attendance data grouped by hours
    hours = Hour.query.filter_by(section_id=section_id).all()
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, f"Attendance Report - {section_name} - {date}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for hour in hours:
        # Title for each hour
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, f"Hour: {hour.time_slot}", ln=True, align='L')
        pdf.ln(5)  # Spacing before the table

        # Table Header
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(50, 10, "Reg No", border=1, align='C')
        pdf.cell(80, 10, "Name", border=1, align='C')
        pdf.cell(40, 10, "Status", border=1, align='C')
        pdf.ln()  # Move to the next line
        
        # Fetch attendance records for this hour
        attendance_records = Attendance.query.filter_by(hour_id=hour.id, date=date).all()
        
        # Table Data
        pdf.set_font("Arial", size=12)
        for record in attendance_records:
            student = db.session.get(Student, record.student_id)
            status = "Present" if record.status else "Absent"
            pdf.cell(50, 10, student.reg_no, border=1, align='C')
            pdf.cell(80, 10, student.name, border=1, align='C')
            pdf.cell(40, 10, status, border=1, align='C')
            pdf.ln()  # Move to the next row
        
        pdf.ln(10)  # Add more spacing before the next hour table

    # Save PDF in static directory
    report_path = f"static/reports/attendance_report_{section_id}_{date}.pdf"
    os.makedirs("static/reports", exist_ok=True)  # Ensure directory exists
    pdf.output(report_path)

    return send_file(report_path, as_attachment=True)

# ✅ Function to Generate PDF Report
def generate_pdf(section_id, hour_id):
    today = datetime.utcnow().date()

    # Fetch section and hour details
    section = Section.query.get(section_id)
    hour = Hour.query.get(hour_id)
    section_name = section.name if section else f"Section {section_id}"
    hour_slot = hour.time_slot if hour else f"Hour {hour_id}"

    # Fetch attendance records
    attendance_records = Attendance.query.filter_by(hour_id=hour_id, date=today).all()

    # Fetch all students in one query for better performance
    student_dict = {s.id: s for s in Student.query.filter(Student.id.in_([r.student_id for r in attendance_records])).all()}

    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Attendance Report - {section_name} - for Hour {hour_slot} - {today}", ln=True, align='C')
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Reg No", border=1, align='C')
    pdf.cell(80, 10, "Name", border=1, align='C')
    pdf.cell(40, 10, "Status", border=1, align='C')
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=12)
    present_count = 0
    for record in attendance_records:
        student = student_dict.get(record.student_id)
        status = "Present" if record.status else "Absent"
        if record.status:
            present_count += 1
        pdf.cell(50, 10, student.reg_no, border=1, align='C')
        pdf.cell(80, 10, student.name, border=1, align='C')
        pdf.cell(40, 10, status, border=1, align='C')
        pdf.ln()

    absent_count = len(attendance_records) - present_count

    # Add summary at the bottom
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, f"Total Present: {present_count} | Total Absent: {absent_count}", ln=True, align='C')

    # Save PDF
    os.makedirs("static/reports", exist_ok=True)
    pdf_path = f"static/reports/attendance_report_{section_id}_{hour_id}_{today}.pdf"
    pdf.output(pdf_path)

    return pdf_path

# ✅ Function to Send Email with PDF Attachment
def send_email_with_attachment(section_id, hour_id, recipients):
    try:
        pdf_path = generate_pdf(section_id, hour_id)
        subject = f"Attendance Report - Section {section_id}"
        body = "Please find the attached attendance report."

        msg = Message(subject, recipients=recipients)
        msg.body = body

        with app.open_resource(pdf_path) as pdf:
            msg.attach(os.path.basename(pdf_path), "application/pdf", pdf.read())

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False  # Prevents app crash

# ✅ Submit Attendance and Send Email
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    """Handles attendance submission and sends an email with the report."""
    data = request.json
    today = datetime.utcnow().date()
    print("=================")
    print(data)

    if not data:
        return jsonify({"error": "No attendance data provided"}), 400

    section_id = data[0].get("section_id")
    hour_id = data[0].get("hour_id")

    if not section_id or not hour_id:
        return jsonify({"error": "Invalid section or hour ID"}), 400

    for record in data:
        student_id = record.get("student_id")
        status = record.get("status")

        existing_attendance = Attendance.query.filter_by(student_id=student_id, hour_id=hour_id, date=today).first()
        if existing_attendance:
            existing_attendance.status = status
        else:
            new_attendance = Attendance(student_id=student_id, hour_id=hour_id, date=today, status=status)
            db.session.add(new_attendance)

    db.session.commit()

    # Send email with PDF report
    email_sent = send_email_with_attachment(section_id, hour_id, email_recipients)

    if email_sent:
        return jsonify({"message": "Attendance submitted and emails sent successfully!"})
    else:
        return jsonify({"message": "Attendance submitted, but emails could not be sent."}), 500


if __name__ == '__main__':
    # Ensure the database file exists
    if not os.path.exists('attendance.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)

