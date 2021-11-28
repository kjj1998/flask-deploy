import os
import csv
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, send_file, current_app
#from src.db import get_db
from student_list.utils import (
	get_score, get_student, get_top2, parse_score, 
	parse_student, upload_score, upload_student, 
	save_file, allowed_file, get_headers, csv_writer)

UPLOAD_FOLDER = 'static/files'
DONWLOAD_FOLDER = 'static/downloads'
UPLOAD_TAGS = ['student', 'score']

from student_list import db
from student_list.models import Student, Score

bp = Blueprint('student_list', __name__)

@bp.route('/')
def index():
	"""results = db.execute(
		'SELECT s.name, class, subject, score'
		' FROM student s LEFT JOIN score t ON s.name = t.name'
	).fetchall()"""

	results = db.session.query(Student).join(Score, Student.name == Score.name, isouter=True).all()
	
	print(results)

	students = {}
	for result in results:
		name = result['name']
		student_class = result['class']
		subject = result['subject']
		score = result['score']
		
		details = {}
		if name not in students:
			details['class'] = student_class
			details['subject'] = { subject : score }
			students[name] = details
		else:
			details = students[name]
			details['subject'][subject] = score
	
	return render_template('app/index.html', students=students)

# done rf
@bp.route('/create_student', methods=('GET', 'POST'))
def create_student():
	if request.method == 'POST':
		name = request.form['name']
		student_class = request.form['class']
		password = request.form['password']
		db = get_db()
		error = None

		if not name:
			error = "Name is required"
		elif not student_class:
			error = "Class is required"
		elif not password:
			error = "Password is required"

		if error is None:
			try:
				db.execute(
					'INSERT INTO student (name, password, class)'
					' VALUES (?, ?, ?)',
					(name, password, student_class)
				)
				db.commit()
			except db.IntegrityError:
				error = f"Student {name} is already registered."
			else:
				return redirect(url_for('application.index'))
		flash(error)

	return render_template('app/create_student.html')

#rf done
@bp.route('/<name>/create_subject', methods=('GET', 'POST'))
def create_subject(name):
	if request.method == 'POST':
		subject = request.form['subject']
		score = request.form['score']
		db = get_db()
		error = None

		if not subject:
			error = "Subject is required"
		if not score:
			error = "Score is required"
		
		if error is None:
			try:
				id = name + subject
				db.execute(
					'INSERT INTO score (id, name, subject, score)'
					' VALUES (?, ?, ?, ?)',
					(id, name , subject, float(score))
				)
				db.commit()
			except db.IntegrityError:
				error = f"Subject {subject} for Student {name} is already registered."
			else:
				return redirect(url_for('application.index'))
		flash(error)
		
	return render_template('app/create_subject.html', name=name)

#rf done
@bp.route('/<name>/update', methods=('GET', 'POST'))
def update(name):
	student = get_student(name)

	if request.method == 'POST':
		student_name = name
		student_class = request.form['class']
		password = request.form['password']

		db = get_db()
		db.execute(
			'UPDATE student SET class = ?, password = ?'
			' WHERE name = ?',
			(student_class, password, student_name)
		)
		db.commit()
		return redirect(url_for('application.index'))

	return render_template('app/update_student.html', student=student)

#rf done
@bp.route('/<name>/<subject>/updatescore', methods=('GET', 'POST'))
def update_score(name, subject):
	score = get_score(name, subject)
	id = score['id']

	if request.method == 'POST':
		subject = request.form['subject']
		score = request.form['score']
		db = get_db()

		db.execute(
			'UPDATE score SET subject = ?, score = ?'
			' WHERE id = ?',
			(subject, score, id,)
		)
		db.commit()
		return redirect(url_for('application.index'))

	return render_template('app/update_score.html', score=score)

#rf done
@bp.route('/<name>/deletestudent', methods=('POST',))
def delete_student(name):
	db = get_db()
	db.execute(
		'DELETE FROM student'
		' WHERE name = ?', 
		(name, )	
	)
	db.commit()
	return redirect(url_for('application.index'))

#rf done
@bp.route('/<name>/<subject>/deletescore', methods=('POST',))
def delete_score(name, subject):
	db = get_db()
	db.execute(
		'DELETE FROM score'
		' WHERE name = ? AND subject = ?',
		(name, subject, )
	)
	db.commit()
	return redirect(url_for('application.index'))

@bp.route('/rankings')
def rankings():
	db = get_db()
	results = db.execute(
		'SELECT DISTINCT subject'
		' FROM score s'
	).fetchall()
	
	rankings = {}
	for result in results:
		subject = result['subject']
		top2 = get_top2(subject)
		rankings[subject] = top2
	
	return render_template('app/rankings.html', rankings=rankings)

@bp.route('/upload', methods=('GET', 'POST'))
def upload():
	if request.method == 'POST':
		for tag in UPLOAD_TAGS:
			if (request.files.get(tag, -1) != -1):
				correct_tag = tag
				break
		
		file = request.files[correct_tag]

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
	db = get_db()
	formatted_headers = get_headers('student')
	results = db.execute(
		'SELECT *'
		' FROM student s'
	).fetchall()

	downloaded_file = csv_writer(formatted_headers, results, 'student')
	return send_file(downloaded_file, as_attachment=True)

@bp.route('/downloadscore', methods=('POST',))
def download_score():
	db = get_db()
	formatted_headers = get_headers('score')
	
	results = db.execute(
		'SELECT *'
		' FROM score'
	).fetchall()
	downloaded_file = csv_writer(formatted_headers, results, 'score')
	return send_file(downloaded_file, as_attachment=True)




