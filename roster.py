import csv, io
from web import db
from models import Student

def csvToRoster(f):
    roster = []
    studentData = {}

    stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)

    reader = csv.DictReader(stream)

    rowCount = 2

    for row in reader:
        if 'RUID' not in row:
            raise ValueError("No RUID field")

        ruid = row['RUID']

        try:
            ruid = int(ruid)
        except ValueError:
            raise ValueError("Non-numeric ruid on row {}".format(rowCount))

        student = Student.query.get(ruid)

        firstname = row["First Name"] if "First Name" in row else None
        lastname = row["Last Name"] if "Last Name" in row  else None
        classYear = row["Class Year"] if "Class Year" in row  else None
        if classYear == "":
            classYear = None

        if classYear:
            try:
                classYear = int(classYear)
            except ValueError:
                raise ValueError("Non-numeric Class Year on row {}".format(rowCount))

        if student == None:
            student = Student(ruid, firstname, lastname, classYear)
            db.session.add(student)
        else:
            if student.firstname == None:
                student.firstname = firstname
            if student.lastname == None:
                student.lastname = lastname
            if student.classYear == None:
                student.classYear = classYear

        roster.append(student)

        studentDatum = {}
        if "Discussion Leader" in row:
            studentDatum['discussionLeader'] = True if row["Discussion Leader"].lower() == "yes" else False
        if "Description" in row:
            studentDatum["description"] = row["Description"]
        
        studentData[ruid] = studentDatum
        rowCount += 1
        
    db.session.commit()
    return roster, studentData
