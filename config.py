import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = True
    TESTING = True
    CSRF_ENABLED = True
    TEMPLATES_AUTO_RELOAD = DEBUG
    SECRET_KEY = 'this-really-needs-to-be-changed'
    MAPBOX_ACCESS_KEY = 'pk.eyJ1IjoiYWZhbmN5IiwiYSI6ImNqaXFob2FwejAwdnYzcHFpaDJydzY0c3UifQ.aCQ2fGpSed-QsWEvyOITaA'
    SQLALCHEMY_DATABASE_URI = "postgresql://xiuli:Abcd1234@localhost:5432/testdb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False

