import click
from flask.cli import with_appcontext
from student_list import db

# create a cli command to drop all existing tables and create new tables
@click.command('create-tables')
@with_appcontext
def create_tables():
	db.drop_all()
	db.create_all()
	click.echo('Initialized the database.')

def init_app(app):
	app.cli.add_command(create_tables)