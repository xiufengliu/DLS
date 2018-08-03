from app import db
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2 import Geometry

class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    result_all = db.Column(db.String())


    def __init__(self, url, result_all):
        self.url = url
        self.result_all = result_all
        

    def __repr__(self):
        return '<id {}>'.format(self.id)


class Household(db.Model):
    __tablename__ = 'essex_meters'

    meterid = db.Column(db.Integer, primary_key=True)
    geom = db.Column(Geometry('POINT,4326'))

    def __repr__(self):
        return 'meterid = {}'.format(self.meterid)



class Neighborhood(db.Model):
    __tablename__ = 'essex_neighborhood'

    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String())
    geom = db.Column(Geometry('POLYGON,4326'))

    def __init__(self, id, name, geom):
        self.id = id
        self.name = name
        self.geom = geom

    def __repr__(self):
        return 'name = {}'.format(self.name)



