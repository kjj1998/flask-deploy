
from werkzeug.utils import secure_filename
import pandas as pd
import os
import csv
from flask import current_app, flash
ALLOWED_EXTENSIONS = {'csv'}
STUDENT_COL_NAMES = ['name','password','class']
UPLOAD_TAGS = ['student', 'score']
from student_list import db
from student_list.models import Student, Score
from sqlalchemy.exc import IntegrityError

def get_student(name):
	student = db.session.query(Student).filter(Student.name == name).one()
	studentDict = {}
	studentDict['name'] = student.name
	studentDict['class'] = student.student_class
	studentDict['password'] = student.password
	
	return studentDict

def get_score(name, subject):
	score = db.session.query(Score).filter(
		Score.name == name, 
		Score.subject == subject
	).one()

	scoreDict = {}
	scoreDict['name'] = score.name
	scoreDict['subject'] = score.subject
	scoreDict['score'] = score.score
	scoreDict['id'] = score.id

	return scoreDict


def get_top2(subject):
	top2 = db.session.query(Student, Score) \
							.join(Score, Student.name == Score.name) \
							.filter(Score.subject == subject) \
							.order_by(Score.score.desc()) \
							.limit(2).all()

	top2_list = []
	for top in top2:
		temp = {}
		temp['score'] = top[1].score
		temp['subject'] = top[1].subject
		temp['name'] = top[0].name
		temp['class'] = top[0].student_class
		temp['password'] = top[0].password
		top2_list.append(temp)
	
	return top2_list

def save_file(uploaded_file):
	filename = secure_filename(uploaded_file.filename)
	#print(current_app.root_path)
	#print(current_app.config['UPLOAD_FOLDER'])
	file_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'][0], filename)
	print(file_path)
	uploaded_file.save(file_path)
		
	return file_path

def parse_score(filepath):
	col_names = ['name','subject','score']
	error = None
	col_num = 3
	csvData = pd.read_csv(filepath, header=0)
	csv_col_names = csvData.columns.values
	csv_col_names_len = len(csvData.columns)
	
	if (csv_col_names_len != col_num):
		error = f"CSV file has {len(csvData.columns)} columns, expected {col_num} columns"
	else: 
		for i in range(csv_col_names_len):
			if col_names[i] != csv_col_names[i]:
				error = f"CSV file has {csv_col_names[i]} column, expected {col_names[i]} column"
				break
	
	if error is None:
		for i,row in csvData.iterrows():
			formatted_score = ''.join(filter(str.isdigit, str(row['score'])))
			csvData.at[i, 'name'] = 'student' + row['name'][-1]
			csvData.at[i, 'score'] = formatted_score
		csvData.to_csv(filepath, index=False, header=True)
	else:
		os.remove(filepath)
		return error

def parse_student(filepath):
	error = None
	col_names = STUDENT_COL_NAMES
	col_len = len(col_names)
	csvData = pd.read_csv(filepath, header=0)
	csv_col_names = csvData.columns.values
	csv_col_names_len = len(csvData.columns)
	
	# check equal number of columns
	if (csv_col_names_len != col_len):
		error = f"CSV file has {len(csvData.columns)} columns, expected {col_len} columns"
	else:
		# check each col has the same name 
		for i in range(csv_col_names_len):
			if col_names[i] != csv_col_names[i]:
				error = f"CSV file has {csv_col_names[i]} column, expected {col_names[i]} column"
				break

	if error is not None:
		os.remove(filepath)
		return error

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_score(filepath):
	csvData = pd.read_csv(filepath, header=0)
	error = None
	for i,row in csvData.iterrows():
		try:
			id = row['name'] + row['subject']
			db.session.add(Score(id, row['name'], row['subject'], row['score']))
			db.session.commit()
		
		except IntegrityError:
			db.session.rollback()
			error = f"Subject {row['subject']} for Student {row['name']} is already registered."
			flash(error)	

def upload_student(filepath):
	col_names = STUDENT_COL_NAMES
	csvData = pd.read_csv(filepath,names=col_names, header=None)
	error = None
	
	# uploads each row (except for header) into the database
	for i,row in csvData.iterrows():
		try:
			if i != 0:
				db.session.add(Student(row['name'], row['password'], row['class']))
				db.session.commit()
		except IntegrityError:
			db.session.rollback()
			error = f"Student {row['name']} is already registered."
			flash(error)


def get_headers(name):
	if name == 'Student':
		headers = Student.__table__.columns.keys()
	else:
		headers = Score.__table__.columns.keys()
	
	return headers

def csv_writer(formatted_headers, results, name):
	temp_path = os.path.join(current_app.root_path, current_app.config['DOWNLOAD_FOLDER'], name + '.csv')
	print(results)

	contents = []
	for result in results:
		contents.append(result.contents_list())

	with open(temp_path, mode='w', newline='') as file:
		file_writer = csv.writer(file, delimiter=',')
		file_writer.writerow(formatted_headers)
		file_writer.writerows(contents)
	
	return temp_path
