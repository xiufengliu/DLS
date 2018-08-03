import click

from flask.cli import AppGroup

from app import app
import models
from app import db

db_cli = AppGroup('db')

@db_cli.command('drop')
def drop():
    db.drop_all()


@db_cli.command('create')
def create(default_data=True, sample_data=False):
    "Creates database tables from sqlalchemy models"
    db.create_all()

@db_cli.command('recreate')
def recreate(default_data=True, sample_data=False):
    "Recreates database tables (same as issuing 'drop' and then 'create')"
    db.drop_all()
    db.create_all()

app.cli.add_command(db_cli)

