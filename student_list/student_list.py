import os
import csv
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, send_file, current_app
#from src.db import get_db
"""from student_list.utils import (
	get_score, get_student, get_top2, parse_score, 
	parse_student, upload_score, upload_student, 
	save_file, allowed_file, get_headers, csv_writer)"""

from student_list.utils import get_student, get_score

UPLOAD_FOLDER = 'static/files'
DONWLOAD_FOLDER = 'static/downloads'
UPLOAD_TAGS = ['student', 'score']

from student_list import db
from student_list.models import Student, Score
from sqlalchemy.exc import IntegrityError


bp = Blueprint('student_list', __name__)

@bp.route('/')
def index():
	results = db.session.query(Student, Score).outerjoin(Score, Student.name == Score.name).all()
	
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
	student = get_student(name)

	if request.method == 'POST':
		student_name = name
		student_class = request.form['class']
		password = request.form['password']

		db.session.query(Student).filter(Student.name == student_name).update(
			{Student.student_class: student_class, Student.password: password},
			synchronize_session=False
		)
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

		"""db.execute(
			'UPDATE score SET subject = ?, score = ?'
			' WHERE id = ?',
			(subject, score, id,)
		)
		db.commit()"""
		db.session.query(Score).filter(Score.id == id).update(
			{Score.subject: subject, Score.score: score},
			synchronize_session=False
		)
		db.session.commit()
		return redirect(url_for('student_list.index'))

	return render_template('app/update_score.html', score=score)

"""
#rf done
@bp.route('/<name>/deletestudent', methods=('POST',))
def delete_student(name):
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
	db.execute(
		'DELETE FROM score'
		' WHERE name = ? AND subject = ?',
		(name, subject, )
	)
	db.commit()
	return redirect(url_for('application.index'))

@bp.route('/rankings')
def rankings():
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
	formatted_headers = get_headers('student')
	results = db.execute(
		'SELECT *'
		' FROM student s'
	).fetchall()

	downloaded_file = csv_writer(formatted_headers, results, 'student')
	return send_file(downloaded_file, as_attachment=True)

@bp.route('/downloadscore', methods=('POST',))
def download_score():
	formatted_headers = get_headers('score')
	
	results = db.execute(
		'SELECT *'
		' FROM score'
	).fetchall()
	downloaded_file = csv_writer(formatted_headers, results, 'score')
	return send_file(downloaded_file, as_attachment=True)


"""

