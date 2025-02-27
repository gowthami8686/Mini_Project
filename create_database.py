from server import db, Section, Hour, Student, app

time_slots = ["9-10", "10-11", "11-12", "1-2", "2-3", "3-4", "4-5"]

with app.app_context():
    db.create_all()

    # Add sections
    if not Section.query.first():
        section1 = Section(name="IT-A")
        section2 = Section(name="IT-B")
        db.session.add_all([section1, section2])
        db.session.commit()
        print("Sections added!")

    sections = Section.query.all()

    # Add hours for each section
    if not Hour.query.first():
        for section in sections:
            for slot in time_slots:
                db.session.add(Hour(time_slot=slot, section_id=section.id))
        db.session.commit()
        print("Hours added!")

    # Add students with correct registration numbers and names
    if not Student.query.first():
        student_data = [
            {"reg_no": "22331A1201", "name": "Aditya", "section": "IT-A"},
            {"reg_no": "22331A1202", "name": "Aravind", "section": "IT-A"},
            {"reg_no": "22331A1203", "name": "Vamsi", "section": "IT-A"},
            {"reg_no": "22331A1204", "name": "Mohan", "section": "IT-A"},
            {"reg_no": "22331A1205", "name": "Harika", "section": "IT-A"},

            {"reg_no": "22331A1267", "name": "kavya", "section": "IT-B"},
            {"reg_no": "22331A1268", "name": "Bala Aditya", "section": "IT-B"},
            {"reg_no": "22331A1269", "name": "Praveenya", "section": "IT-B"},
            {"reg_no": "22331A1270", "name": "Yuva Priya", "section": "IT-B"},
            {"reg_no": "22331A1271", "name": "Sampath", "section": "IT-B"},

        ]
        
        for student in student_data:
            section = Section.query.filter_by(name=student["section"]).first()
            if section:
                db.session.add(Student(reg_no=student["reg_no"], name=student["name"], section_id=section.id))
        
        db.session.commit()
        print("Students added!")
