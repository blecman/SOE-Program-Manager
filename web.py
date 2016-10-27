import datetime, os
from flask import Flask, render_template, request, redirect, url_for
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
    title = ""

    if programId != None:
        program = Program.query.get(programId)
        students = program.students
        title = program.string()
    elif q != None:
        students = Student.query.filter(Student.firstname.contains(q) | Student.lastname.contains(q) | Student.ruid.contains(q) | Student.classYear.contains(q)).all()
        title = "Filter: {}".format(q)
    else:
        q = ""
        students = Student.query.all()
    studentsData = []
    for student in students:
        studentData = {'firstname': student.firstname,
                        'lastname': student.lastname,
                        'ruid': student.ruid,
                        'classYear': student.classYear,
                        'keynoteCount': 0,
                        'bookclubCount': 0,
                        'serviceLearningCount': 0}

        #get counts for each type of program that the student has done
        for program in student.programs:
            studentData[program.type + "Count"] += 1
        studentsData.append(studentData)

    return render_template('students.html', students=studentsData, title=title, q=q, programId=programId)

@app.route("/keynotes", methods=['GET','POST'])
def keynotes_page():
    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students = roster.csvToRoster(f)
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
            student.programs.append(keynote)
        db.session.commit()
        return redirect(url_for('students_page', id=keynote.id))

    q = request.args.get("q")
    title = ""
    if q == None:
        q = ""
        keynotes = Keynote.query.all()
    else:
        keynotes = Keynote.query.filter(Keynote.id.contains(q) | Keynote.speaker.contains(q) | Keynote.date.contains(q)).all()
        title = "Filter: {}".format(q)

    return render_template('keynotes.html', keynotes=keynotes, title=title, q=q)

@app.route("/bookclubs", methods=['GET','POST'])
def bookclubs_page():
    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students = roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)

        year = int(request.form['year'])
        fallSemester = bool(request.form['fallSemester'])
        book = request.form['book']

        bookclub = Bookclub(year, fallSemester, book)

        for student in students:
            student.programs.append(bookclub)
        db.session.commit()
        return redirect(url_for('students_page', id=bookclub.id))

    q = request.args.get("q")
    title = ""
    if q == None:
        bookclubs = Bookclub.query.all()
        q = ""
    else:
        bookclubs = Bookclub.query.filter(Bookclub.id.contains(q) | Bookclub.year.contains(q) | Bookclub.book.contains(q) ).all()
        title = "Filter: {}".format(q)

    return render_template('bookclubs.html', bookclubs=bookclubs, title=title, q=q)

@app.route("/serviceLearnings", methods=['GET','POST'])
def service_learnings_page():

    if request.method == 'POST':
        f = request.files['file']

        if not f:
            return "No File"

        try:
            students = roster.csvToRoster(f)
        except ValueError as err:
            return "Error: " + str(err)

        description = request.form['description']

        servicelearning = ServiceLearning(description)

        for student in students:
            student.programs.append(servicelearning)
        db.session.commit()
        return redirect(url_for('students_page', id=servicelearning.id))

    q = request.args.get("q")
    title = ""
    if q == None:
        q = ""
        serviceLearnings = ServiceLearning.query.all()
    else:
        serviceLearnings = ServiceLearning.query.filter(ServiceLearning.id.contains(q) | ServiceLearning.description.contains(q) ).all()
        title = "Filter: {}".format(q)

    return render_template('serviceLearnings.html', serviceLearnings=serviceLearnings, title=title, q=q)

@app.route("/programs/<ruid>")
def programs_page(ruid):
    student = Student.query.get(ruid)

    if student:
        programs = {'keynote': [], 'bookclub': [], 'serviceLearning': [] }

        for program in student.programs:
            programs[program.type].append(program)

        title = "{}, {} {}".format(student.ruid, student.firstname, student.lastname)
        return render_template('programs.html', programs=programs, title=title)

    return "Error: No Such student"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
