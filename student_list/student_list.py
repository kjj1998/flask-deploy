from flask import Blueprint, flash, g, redirect, render_template, request, url_for, send_file
from student_list import db
from student_list.models import Student, Score
from sqlalchemy.exc import IntegrityError

# import necessary utility functions
from student_list.utils import (
	get_headers, get_student, get_score, get_top2,
	allowed_file, save_file, parse_student,
	parse_score, upload_student, upload_score,
	csv_writer
)

UPLOAD_TAGS = ['student', 'score']	# declare constants
bp = Blueprint('student_list', __name__)

@bp.route('/')
def index():
	# LEFT OUTER JOIN on Student and Score where Student.name == Score.name
	# results is an array of tupples where in each tupple,
	# the first index is the Student object and the second is the Score object
	results = db.session.query(Student, Score) \
											.outerjoin(Score, Student.name == Score.name) \
											.all()
	
	""" store the results in a dictionary with name of student as key and the details (in the form of a dictionary) as values
			Eg. 
			{
				"student1" : {
												"class" : "class1"
												"subject" : {
																			"english" : 76, "science" : 85
																		}
										 }
			} 
	"""
	students = {}
	for result in results:
		name = result[0].name
		student_class = result[0].student_class
		if result[1] == None:
			subject = None
			score = None
		else:
			subject = result[1].subject
			score = result[1].score
		
		details = {}
		if name not in students:
			details['class'] = student_class
			details['subject'] = { subject : score }
			students[name] = details
		else:
			details = students[name]
			details['subject'][subject] = score
	
	return render_template('app/index.html', students=students)

@bp.route('/create_student', methods=('GET', 'POST'))
def create_student():
	if request.method == 'POST':
		name = request.form['name']
		student_class = request.form['class']
		password = request.form['password']
		error = None

		# check that all required fields are given
		if not name:
			error = "Name is required"
		elif not student_class:
			error = "Class is required"
		elif not password:
			error = "Password is required"

		if error is None:
			try:
				db.session.add(Student(name, password, student_class))
				db.session.commit()
			except IntegrityError:
				db.session.rollback()
				error = f"Student {name} is already registered."
			else:
				return redirect(url_for('student_list.index'))
		flash(error)

	return render_template('app/create_student.html')

@bp.route('/<name>/create_subject', methods=('GET', 'POST'))
def create_subject(name):
	if request.method == 'POST':
		subject = request.form['subject']
		score = request.form['score']
		error = None

		if not subject:
			error = "Subject is required"
		if not score:
			error = "Score is required"
		
		if error is None:
			try:
				id = name + subject
				db.session.add(Score(id, name, subject, score))
				db.session.commit()
			except IntegrityError:
				db.session.rollback()
				error = f"Subject {subject} for Student {name} is already registered."
			else:
				return redirect(url_for('student_list.index'))
		flash(error)
		
	return render_template('app/create_subject.html', name=name)

@bp.route('/<name>/update', methods=('GET', 'POST'))
def update(name):
	# get the current information of that particular student
	student = get_student(name)

	if request.method == 'POST':
		student_name = name
		student_class = request.form['class']
		password = request.form['password']

		# Update student_class and password of a single record in Student by filtering on student_name
		db.session.query(Student) \
							.filter(Student.name == student_name) \
							.update({
								Student.student_class: student_class, 
								Student.password: password}, 
								synchronize_session=False)			
		db.session.commit()
		return redirect(url_for('student_list.index'))

	return render_template('app/update_student.html', student=student)

@bp.route('/<name>/<subject>/updatescore', methods=('GET', 'POST'))
def update_score(name, subject):
	score = get_score(name, subject)
	id = score['id']

	if request.method == 'POST':
		subject = request.form['subject']
		score = request.form['score']

		# Update subject and score of a single record in Score by filtering on id
		db.session.query(Score) \
							.filter(Score.id == id) \
							.update(
								{Score.subject: subject, Score.score: score},
								synchronize_session=False
							)
		db.session.commit()
		return redirect(url_for('student_list.index'))

	return render_template('app/update_score.html', score=score)

@bp.route('/<name>/deletestudent', methods=('POST',))
def delete_student(name):
	db.session.query(Student).filter(Student.name == name).delete()
	db.session.commit()
	return redirect(url_for('student_list.index'))

@bp.route('/<name>/<subject>/deletescore', methods=('POST',))
def delete_score(name, subject):
	db.session.query(Score) \
						.filter(Score.name == name, Score.subject == subject) \
						.delete()
	db.session.commit()
	return redirect(url_for('student_list.index'))

@bp.route('/rankings')
def rankings():
	# Select records with distinct subject from Score 
	results = db.session.query(Score) \
							.distinct(Score.subject).all()
	
	rankings = {}
	for result in results:
		subject = result.subject
		top2 = get_top2(subject)	# get_top2(subject) returns a list containing information relating to the top 2 scores
		rankings[subject] = top2
	
	return render_template('app/rankings.html', rankings=rankings)

@bp.route('/upload', methods=('GET', 'POST'))
def upload():
	if request.method == 'POST':
		# Check if student or score files are being uploaded
		for tag in UPLOAD_TAGS:
			if (request.files.get(tag, -1) != -1):
				correct_tag = tag
				break
		
		file = request.files[correct_tag]		# get uploaded file object from the front-end

		# if user submits without selecting a file
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		# checks if file type is correct
		if (not allowed_file(file.filename)):
			flash('File type uploaded is not csv')
			return redirect(request.url)
	
		saved_path = save_file(file)	# saves uploaded file and return the file path
		
		# parses the uploaded file and check its format
		if (correct_tag == 'student'):
			error = parse_student(saved_path)				
		else:
			error = parse_score(saved_path)
		
		if (error):
			flash(error)
			return redirect(request.url)
		else:
			# upload to db if there are no errors
			if (correct_tag == 'student'):
				upload_student(saved_path)
			else:
				upload_score(saved_path)

	return render_template('app/upload.html')

@bp.route('/downloadpage', methods=('GET',))
def downloadpage():
	return render_template('app/downloadpage.html')

@bp.route('/downloadstudent', methods=('POST',))
def download_student():
	headers = get_headers('Student')														# get column headers
	results = db.session.query(Student).all()										# retrieve all rows from database
	downloaded_file = csv_writer(headers, results, 'student')		# write headers and retrieved rows into a csv file
	return send_file(downloaded_file, as_attachment=True)

@bp.route('/downloadscore', methods=('POST',))
def download_score():
	headers = get_headers('Score')
	results = db.session.query(Score).all()
	downloaded_file = csv_writer(headers, results, 'score')
	return send_file(downloaded_file, as_attachment=True)