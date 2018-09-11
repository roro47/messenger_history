from fbchat import Client
from fbchat.models import *

from sqlalchemy import exists
from messenger_db import User, Base, Message

class FbBot:
    def __init__(self, email, password, dbsession):
        self.email = email
        self.password = password
        self.client = Client(email, password)
        self.dbsession = dbsession
        
    def login(self):
        if not self.client.isLoggedIn():
            self.client.login(email, password)
        
    def find_user(self, name):
        users = fetchAllUsers()
        count = 0
        for u in users:
            if name in u.name:
                user = u
                count = count + 1
        if count is 1:
            return user
        elif count > 1:
            return None
        else:
            return None

    def find_thread(self, name):
        threads = self.client.fetchThreadList()
        count = 0
        uid = 0
        
        for thread in threads:
            if name in thread.name:
                t = (thread.name, int(thread.uid))
                count = count + 1
        if count is 1:
            return t
        else:
            return 0

    def fetch_message_history(self, uid, limit=100, unlimited=False, echo=True):
        last_timestamp = self.client.fetchThreadMessages(thread_id=uid, \
                                                         limit=1)[0].timestamp
        messages = []
        last_len = len(messages)
        while len(messages) < limit or unlimited:
            fetched = self.client.fetchThreadMessages(thread_id=uid, \
                                                       limit=limit, \
                                                       before=last_timestamp)
            messages += fetched
            if echo:
                for message in fetched:
                    if message.text is not None:
                        print("fetched message : < " + message.text + " >")
            last_timestamp = messages[len(messages)-1].timestamp
            if len(messages) is last_len:
                break
            last_len = len(messages)
        return messages


    def store_message(self, timestamp, text, user_id, user, message_id):
        print("< " + text + " > added")
        if not self.dbsession.query(exists().where(Message.timestamp==timestamp)):
            message = Message(timestamp=timestamp, \
                              text=text, \
                              user_id=user_id, \
                              user=user, \
                              message_id=message_id)
            self.dbsession.add(message)
            self.dbsession.commit()

    # update
    def get(self, name):
        (user_name, user_uid) = self.find_thread(name)
        user = User(name=user_name, uid=user_uid)
        if not self.dbsession.query(exists().where(User.uid==user_uid)).scalar():
            self.dbsession.add(user)
            self.dbsession.commit()
        messages = self.fetch_message_history(user_uid)
        for i in range(0, len(messages)):
            if messages[i].text is None:
                continue
            self.store_message(timestamp=messages[i].timestamp, \
                               text=messages[i].text, \
                               user_id=user_uid, \
                               user=user, \
                               message_id=messages[i].uid)

    def update(self, name):
        return

    def logout(self):
        self.client.logout()
