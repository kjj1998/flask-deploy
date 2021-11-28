import click
from flask.cli import with_appcontext
from flask import Blueprint

from student_list import db
from .models import Student, Score

bp = Blueprint('commands', __name__)

@click.command('create-tables')
@with_appcontext
def create_tables():
	db.create_all()
	click.echo('Initialized the database.')

def init_app(app):
	app.cli.add_command(create_tables)