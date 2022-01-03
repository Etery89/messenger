from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from commons import *
from datetime import datetime


class ClientWarehouse:

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.now()

    def __init__(self, client_name):

        self.database_engine = create_engine(f'sqlite:///client_{client_name}.db3', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_user', String),
                        Column('to_user', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        self.metadata.create_all(self.database_engine)

        mapper(self.Contacts, contacts)
        mapper(self.MessageHistory, history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    # add contact
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # delete contact
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    # show contacts
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # added exchange write in history messages
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция возвращающая историю переписки
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == "__main__":
    test_db = ClientWarehouse("client1")







