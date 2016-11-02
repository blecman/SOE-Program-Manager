from web import db

#association table between students and programs
association_table = db.Table('association',
    db.Column('student_id', db.Integer, db.ForeignKey('student.ruid')),
    db.Column('program_id', db.Integer, db.ForeignKey('program.id'))
)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    studentId = db.Column(db.Integer, db.ForeignKey('student.ruid'), primary_key=True)
    programId = db.Column(db.Integer, db.ForeignKey('program.id'), primary_key=True)
    leader = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    program = db.relationship("Program", back_populates="attendances")
    student = db.relationship("Student", back_populates="attendances")

    def __init__ (self, student, program, description="", leader=False):

        self.program = program
        self.description = description
        self.leader = leader
        self.student = student

class Student(db.Model):
    __tablename__ = 'student'

    ruid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(256))
    lastname = db.Column(db.String(256))
    classYear = db.Column(db.Integer)
    attendances = db.relationship("Attendance", back_populates="student")

    def __init__ (self, ruid, firstname, lastname, classYear):
        self.ruid = ruid
        self.firstname = firstname
        self.lastname = lastname
        self.classYear = classYear

#make general program class which specific program will inherit from
class Program(db.Model):
    __tablename__ = 'program'

    id = db.Column(db.Integer, primary_key=True)
    #type field keeps track of program type for subclasses
    type = db.Column(db.String(30))

    attendances = db.relationship("Attendance", back_populates="program", cascade="save-update, merge, delete")

    __mapper_args__ = {
        'polymorphic_identity':'program',
        'polymorphic_on':type
    }

class Keynote(Program):
    __tablename__ = 'keynote'

    id = db.Column(db.Integer, db.ForeignKey('program.id'), primary_key=True)
    speaker  = db.Column(db.String(512))
    date = db.Column(db.Date)

    __mapper_args__ = {
        'polymorphic_identity':'keynote'
    }

    def __init__ (self, speaker, date):
        self.speaker = speaker
        self.date = date

    def string(self):
        return "Keynote({}): {}, {}".format(self.id, self.speaker, str(self.date))

class Bookclub(Program):
    __tablename__ = 'bookclub'

    id = db.Column(db.Integer, db.ForeignKey('program.id'), primary_key=True)
    year = db.Column(db.Integer)
    fallSemester = db.Column(db.Boolean)
    book = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity':'bookclub'
    }

    def __init__ (self, year, fallSemester, book):
         self.year = year
         self.fallSemester = fallSemester
         self.book = book

    def string(self):
        semester = "Fall" if self.fallSemester else "Spring"
        return "Book Club({}): {} - {} {}".format(self.id, self.book, semester, self.year)

class ServiceLearning(Program):
    __tablename__ = 'serviceLearning'

    id = db.Column(db.Integer, db.ForeignKey('program.id'), primary_key=True)
    title = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity':'serviceLearning'
    }

    def __init__ (self, title):
        self.title = title

    def string(self):
        return "Service Learning({})".format(self.id)
