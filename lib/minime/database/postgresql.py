import psycopg2

from .base import Database
from minime.schema import PostgresqlSchema


class PostgresqlDatabase(Database):
    def __init__(self, host=None, port=None, dbname=None, user=None,
                 password=None):
        if dbname is None:
            raise Exception('dbname must have a value')
        if user is None:
            raise Exception('user must have a value')

        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.placeholder_symbol = '%s'
        self.schema_class = PostgresqlSchema
        self.connect()
        self.create_schema(PostgresqlSchema)

    @staticmethod
    def create_from_django_database(dj_details):
        return PostgresqlDatabase(
            host=dj_details['HOST'],
            port=dj_details['PORT'] or 5432,
            dbname=dj_details['NAME'],
            user=dj_details['USER'],
            password=dj_details['PASSWORD'])

    def connect(self):
        self.connection = psycopg2.connect(
            database=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port)

    def url(self):
        return 'postgresql://%s%s@%s:%s/%s' % (
            self.user,
            ':%s' % self.password if self.password is None else '',
            self.host,
            self.port,
            self.dbname)