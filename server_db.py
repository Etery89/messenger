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

    class UsersMessageHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.send = 0
            self.recv = 0

    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    def __init__(self, path):
        # create database
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200)
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
        # Create history message table
        users_history_message_table = Table('Message_history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('send', Integer),
                                    Column('recv', Integer)
                                    )
        # Create contacts table
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )
        # create tables
        self.metadata.create_all(self.database_engine)

        mapper(self.Users, users_table)
        mapper(self.UsersActive, active_users_table)
        mapper(self.UsersHistory, users_history_table)
        mapper(self.UsersMessageHistory, users_history_message_table)
        mapper(self.UsersContacts, contacts)

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

    def fix_user_message(self, sender, recipient):
        sender = self.session.query(self.Users).filter_by(name=sender).first().id
        recipient = self.session.query(self.Users).filter_by(name=recipient).first().id

        sender_row = self.session.query(self.UsersMessageHistory).filter_by(user=sender).first()
        sender_row.send += 1
        recipient_row = self.session.query(self.UsersMessageHistory).filter_by(user=recipient).first()
        recipient_row.recv += 1

        self.session.commit()

    # Create add contact for user
    def add_contact(self, user, contact):

        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        # check
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # Remove contact for user
    def remove_contact(self, user, contact):

        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        # check
        if not contact:
            return

        # Delete
        print(self.session.query(self.UsersContacts).filter(
                self.UsersContacts.user == user.id,
                self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def get_users(self):
        query = self.session.query(self.Users.name, self.Users.last_login)
        return query.all()

    def get_active_users(self):
        query = self.session.query(
            self.Users.name,
            self.UsersActive.host,
            self.UsersActive.port,
            self.UsersActive.time_login
        ).join(self.Users)
        return query.all()

    def get_history(self):
        query = self.session.query(
            self.Users.name,
            self.UsersHistory.host,
            self.UsersHistory.port,
            self.UsersHistory.date_time
        ).join(self.Users)
        return query.all()

    def get_message_history(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersMessageHistory.send,
            self.UsersMessageHistory.recv
        ).join(self.Users)
        return query.all()

    def get_contacts(self, username):
        user = self.session.query(self.Users).filter_by(name=username).one()

        # Запрашиваем список контактов пользователя
        query = self.session.query(self.UsersContacts, self.Users.name). \
            filter_by(user=user.id).join(self.Users, self.UsersContacts.contact == self.Users.id)

        # Возвращаем имена пользователей
        return [contact[1] for contact in query.all()]


if __name__ == "__main__":
    path = "server_warehouse.db3"
    db_test = ServerWarehouse(path)

