from student_list import db

class Student(db.Model):
	name = db.Column(db.String(100), primary_key=True, unique=True)
	password = db.Column(db.String(70))
	student_class = db.Column(db.String(100))

	def __init__(self, name, password, student_class):
		self.name = name
		self.password = password
		self.student_class = student_class
	
class Score(db.Model):
	id = db.Column(db.String, primary_key=True)
	subject = db.Column(db.String(100))
	score = db.Column(db.Float(3))
	name = db.Column(
		db.String(100), 
		db.ForeignKey("Student.name", ondelete="CASCADE", onupdate="CASCADE"),
		nullable=False
	)

	def __init__(self, id, subject, score, name):
		self.id = id
		self.subject = subject
		self.score = score
		self.name = name