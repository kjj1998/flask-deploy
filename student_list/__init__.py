import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
	app = Flask(__name__)
	app.config.from_mapping(
			SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key',
			SQLALCHEMY_DATABASE_URI = "postgresql://postgres:151398@localhost/student" or \
				'sqlite:///' + os.path.join(app.instance_path, 'task_list.sqlite'),
			SQLALCHEMY_TRACK_MODIFICATIONS = False,
			UPLOAD_FOLDER = '.\\static\\uploads',
			DOWNLOAD_FOLDER = '.\\static\\downloads'
	)
	db.init_app(app)
	migrate.init_app(app, db)

	from . import student_list
	app.register_blueprint(student_list.bp)
	return app