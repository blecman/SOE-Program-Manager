import datetime, os, io, csv
from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
import roster

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_db.db'
db = SQLAlchemy(app)

from models import *

@app.route('/')
def home():
    return redirect(url_for('students_page'))

@app.route("/students", methods=['GET', 'POST'])
def students_page():
    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)


    q = request.args.get("q")
    programId = request.args.get("id")
    download = request.args.get("download")
    title = ""

    if programId != None:
        program = Program.query.get(programId)
        programType = program.type
        students = [attendance.student for attendance in program.attendances]
        programData = {attendance.student.ruid: attendance for attendance in program.attendances}
        title = program.string()
    elif q != None or q=="":
        students = Student.query.filter(Student.firstname.contains(q) | Student.lastname.contains(q) | Student.ruid.contains(q) | Student.classYear.contains(q)).all()
        title = "Filter: {}".format(q)
    else:
        q = ""
        students = Student.query.all()
    studentsData = []
    for student in students:
        studentData = {'First Name': student.firstname,
                        'Last Name': student.lastname,
                        'RUID': student.ruid,
                        'Class Year': student.classYear,
                        'Key Notes': 0,
                        'Service Learnings': 0,
                        'Book Clubs': 0,
                        'Discussions Lead': 0}

        #get counts for each type of program that the student has done
        programs = [attendance.program for attendance in student.attendances]
        for attendance in student.attendances:
            if attendance.leader:
                studentData['Discussions Lead'] += 1

            program = attendance.program
            if program.type == 'keynote':
                studentData['Key Notes'] += 1
            if program.type == 'serviceLearning':
                studentData['Service Learnings'] += 1
            if program.type == 'bookclub':
                studentData['Book Clubs'] += 1

        if programId != None:
            if programType == 'serviceLearning':
                studentData['Description'] = programData[student.ruid].description
            if programType == 'bookclub':
                studentData['Discussion Leader'] = "Yes" if programData[student.ruid].leader else "No"
        studentsData.append(studentData)

    if download != None and len(studentsData) > 0:
        si = io.StringIO()
        w = csv.DictWriter(si, studentsData[0].keys())
        w.writeheader()
        w.writerows(studentsData)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output


    return render_template('students.html', students=studentsData, title=title, q=q, programId=programId)

@app.route("/keynotes", methods=['GET','POST','DELETE'])
def keynotes_page():
    deleteId = request.args.get("delete")
    if deleteId != None:
        keynote = Keynote.query.get(deleteId)
        if keynote == None:
            return "Error: no such keynote to delete"
        db.session.delete(keynote)
        db.session.commit()

    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students, _ = roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)

        speaker = request.form["speaker"]
        date = request.form['date']
        date = date.split('-')
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])

        keynote = Keynote(speaker, datetime.date(year, month, day))
        db.session.add(keynote)

        for student in students:
            attendance = Attendance(student, keynote)
            
        db.session.commit()
        return redirect(url_for('students_page', id=keynote.id))

    q = request.args.get("q")
    download = request.args.get("download")
    title = ""
    if q == None or q == "":
        q = ""
        keynotes = Keynote.query.all()
    else:
        keynotes = Keynote.query.filter(Keynote.id.contains(q) | Keynote.speaker.contains(q) | Keynote.date.contains(q)).all()
        title = "Filter: {}".format(q)
    
    keynotes = [{
        'Id': keynote.id,
        'Speaker': keynote.speaker,
        'Date': keynote.date
    } for keynote in keynotes]

    if download != None and len(keynotes) > 0:
        si = io.StringIO()
        w = csv.DictWriter(si, keynotes[0].keys())
        w.writeheader()
        w.writerows(keynotes)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return render_template('keynotes.html', keynotes=keynotes, title=title, q=q)

@app.route("/bookclubs", methods=['GET','POST'])
def bookclubs_page():
    deleteId = request.args.get("delete")
    if deleteId != None:
        bookclub = Bookclub.query.get(deleteId)
        if bookclub == None:
            return "Error: no such bookclub to delete"
        db.session.delete(bookclub)
        db.session.commit()

    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students, studentData = roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)

        year = int(request.form['year'])
        fallSemester = bool(request.form['fallSemester'])
        book = request.form['book']

        bookclub = Bookclub(year, fallSemester, book)

        for student in students:
            if "discussionLeader" not in studentData[student.ruid]:
                return "Error: No Discussion Leader Column"
            attendance = Attendance(student, bookclub, leader=studentData[student.ruid]["discussionLeader"])
        db.session.commit()
        return redirect(url_for('students_page', id=bookclub.id))

    q = request.args.get("q")
    download = request.args.get("download")
    title = ""
    if q == None or q == "":
        bookclubs = Bookclub.query.all()
        q = ""
    else:
        bookclubs = Bookclub.query.filter(Bookclub.id.contains(q) | Bookclub.year.contains(q) | Bookclub.book.contains(q) ).all()
        title = "Filter: {}".format(q)
    
    bookclubs = [
        {
            'Id': bookclub.id,
            'Year': bookclub.year,
            'Semester': "Fall" if bookclub.fallSemester else "Spring",
            'Book': bookclub.book
        }
    for bookclub in bookclubs]

    if download != None and len(bookclubs) > 0:
        si = io.StringIO()
        w = csv.DictWriter(si, bookclubs[0].keys())
        w.writeheader()
        w.writerows(bookclubs)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return render_template('bookclubs.html', bookclubs=bookclubs, title=title, q=q)

@app.route("/serviceLearnings", methods=['GET','POST'])
def service_learnings_page():

    deleteId = request.args.get("delete")
    if deleteId != None:
        servicelearning = ServiceLearning.query.get(deleteId)
        if servicelearning == None:
            return "Error: no such service learning to delete"
        db.session.delete(servicelearning)
        db.session.commit()

    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students, studentData = roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)

        title = request.form['title']

        servicelearning = ServiceLearning(title)

        for student in students:
            if "description" not in studentData[student.ruid]:
                return "Error: No Description Column"
            attendance = Attendance(student, servicelearning, description=studentData[student.ruid]["description"])

        db.session.commit()
        return redirect(url_for('students_page', id=servicelearning.id))

    q = request.args.get("q")
    download = request.args.get("download")
    title = ""
    if q == None or q == "":
        q = ""
        serviceLearnings = ServiceLearning.query.all()
    else:
        serviceLearnings = ServiceLearning.query.filter(ServiceLearning.id.contains(q) | ServiceLearning.title.contains(q) ).all()
        title = "Filter: {}".format(q)

    serviceLearnings = [
        {
            'Id': serviceLearning.id,
            'Title': serviceLearning.title
        }
    for serviceLearning in serviceLearnings]

    if download != None and len(serviceLearnings) > 0:
        si = io.StringIO()
        w = csv.DictWriter(si, serviceLearnings[0].keys())
        w.writeheader()
        w.writerows(serviceLearnings)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return render_template('serviceLearnings.html', serviceLearnings=serviceLearnings, title=title, q=q)

@app.route("/programs/<ruid>")
def programs_page(ruid):
    student = Student.query.get(ruid)

    if student:
        programs = {'keynote': [], 'bookclub': [], 'serviceLearning': [] }

        for attendance in student.attendances:
            program = attendance.program

            if program.type == "serviceLearning":
                programData = {
                    'Id': program.id,
                    'Title': program.title,
                    'Description': attendance.description
                }

            if program.type == 'bookclub':
                programData = {
                    'Id': program.id,
                    'Year': program.year,
                    'Semester': "Fall" if program.fallSemester else "Spring",
                    'Book': program.book,
                    'Discussion Leader': "Yes" if attendance.leader else "No"
                }
            
            if program.type == 'keynote':
                programData = {
                    'Id': program.id,
                    'Speaker': program.speaker,
                    'Date': program.date
                }

            programs[program.type].append(programData)

        title = "{}, {} {}".format(student.ruid, student.firstname, student.lastname)
        return render_template('programs.html', programs=programs, title=title)

    return "Error: No Such student"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
