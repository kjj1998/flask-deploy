from student_list import db

class Student(db.Model):
	name = db.Column(db.String(100), primary_key=True, unique=True)
	password = db.Column(db.String(70))
	student_class = db.Column(db.String(100))

	def __init__(self, name, password, student_class):
		self.name = name
		self.password = password
		self.student_class = student_class
	
	def __repr__(self) -> str:
			rep = self.name + self.password + self.student_class
			return rep
	
class Score(db.Model):
	id = db.Column(db.String, primary_key=True)
	name = db.Column(
		db.String(100), 
		db.ForeignKey("student.name", ondelete="CASCADE", onupdate="CASCADE"),
		nullable=False
	)
	subject = db.Column(db.String(100))
	score = db.Column(db.Numeric(3))
	

	def __init__(self, id, name, subject, score):
		self.id = id
		self.subject = subject
		self.score = score
		self.name = name
	
	def __repr__(self) -> str:
			rep = self.id + self.subject + str(self.score) + self.name
			return rep