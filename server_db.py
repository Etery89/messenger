import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from commons import *
import datetime


class ServerWarehouse:

    class Users:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_login = datetime.datetime.now()

    class UsersActive:
        def __init__(self, user_id, host, port, time_login):
            self.id = None
            self.user = user_id
            self.host = host
            self.port = port
            self.time_login = time_login

    class UsersHistory:
        def __init__(self, name, date, host, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.host = host
            self.port = port

    def __init__(self):
        # create database
        self.database_engine = create_engine('sqlite:///server_warehouse.db3', echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('host', String),
                                   Column('port', Integer),
                                   Column('time_login', DateTime)
                                   )

        users_history_table = Table('Users_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('host', String),
                                   Column('port', String)
                                   )
        # create tables
        self.metadata.create_all(self.database_engine)

        mapper(self.Users, users_table)
        mapper(self.UsersActive, active_users_table)
        mapper(self.UsersHistory, users_history_table)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        # clear table UsersActive for restart messenger
        self.session.query(self.UsersActive).delete()
        self.session.commit()

    # login user in db for connect
    def user_login(self, username, host, port):
            print(username, host, port)
            rez = self.session.query(self.Users).filter_by(name=username)
            # print(type(rez))
            if rez.count():
                user = rez.first()
                user.last_login = datetime.datetime.now()
            else:
                user = self.Users(username)
                self.session.add(user)
                self.session.commit()

            new_active_user = self.UsersActive(user.id, host, port, datetime.datetime.now())
            self.session.add(new_active_user)

            history = self.UsersHistory(user.id, datetime.datetime.now(), host, port)
            self.session.add(history)

            self.session.commit()

    # delete user in db for quit
    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.UsersActive).filter_by(user=user.id).delete()

        self.session.commit()

