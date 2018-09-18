from fbchat import Client
from fbchat.models import *

from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker, scoped_session
from messenger_db import User, Base, Message

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from urlextract import URLExtract

class FbBot:
    def __init__(self, email, password, dbsession, engine):
        self.email = email
        self.password = password
        self.client = Client(email, password)
        self.dbsession = dbsession
        self.uid = self.client.uid
        self.engine = engine
        self.sessionmaker = sessionmaker(bind=engine, autoflush=False)
        self.urlextractor = URLExtract()
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
    def fetch_message_history(self, uid, limit, before=-1, echo=False):
        if before is -1: # fetch latest message
            return self.client.fetchThreadMessages(thread_id=uid, limit=limit)
        return self.client.fetchThreadMessages(thread_id=uid, limit=limit, before=before)

    def store_user(self, name, uid):
        if not self.dbsession.query(exists().where(User.uid==uid)).scalar():
            self.dbsession.add(User(name=name, uid=uid))
            self.dbsession.commit()
            return True
        return False

    def store_image(self, image_uid, user_uid, url):
        if not self.dbsession.query(exists().where(Image.image_uid==image_uid)).scalar():
            self.dbsession.add(Image(image_uid=image_uid, user_uid=user_uid, url=url))
            print("image added")
            return True
        print("image found")
        return False

    def store_file(self, file_uid, user_uid, name, url, size):
        if not self.dbsession.query(exists().where(File.file_uid==file_uid)).scalar():
            self.dbsession.add(File(file_uid=file_uid,\
                                    user_uid=user_uid,\
                                    name=name, \
                                    url=url,\
                                    size=size))
            return True
        return False

    def store_message(self, timestamp, uid, message_id, text, author_uid, user):
        print("< " + text + " >")
        if not self.dbsession.query(exists().where(Message.timestamp==timestamp)\
                                    .where(Message.user_uid==uid)).scalar():
            self.dbsession.add(Message(timestamp=timestamp, \
                                       user_uid=uid, \
                                       message_uid=message_id, \
                                       text=text,\
                                       user=user)) 
            self.dbsession.commit()
            print("message added")
            return True
        else:
            print("message found")
            return False

    def store_url(self, dbsession, url, user_uid, author_uid):
        if not dbsession.query(exists().where(Url.url==url)).scalar():
            dbsession.add(Url(url=url, user_uid=user_uid, author_uid=author_uid))
            dbsession.commit()
            return True
        return False
        
    def store_message2(self, dbsession, timestamp, uid, message_id, text, author_uid, user):
        print("< " + text + " >")
        if not dbsession.query(exists().where(Message.timestamp==timestamp)\
                               .where(Message.user_uid==uid)).scalar():
            dbsession.add(Message(timestamp=timestamp, \
                                  user_uid=uid, \
                                  message_uid=message_id, \
                                  text=text))
            dbsession.commit()
                                  #user=user)) 
            print("message added")
            return True
        else:
            print("message found")
            return False
        
    def get_last_stored_message(self, uid):
        msgs = self.dbsession.query(Message).filter_by(uid=uid)\
                                            .order_by(Message.timestamp)\
                                            .all()
        print("collected stored message: " + str(len(msgs)))
        return msgs[len(msgs)-1]

    def get_concurrent(self, target_name):
        (name, uid) = self.find_thread(target_name)
        self.store_user(name=name, uid=uid)
        user = self.dbsession.query(User).get(uid)
        latest_timestamp = float(self.fetch_message_history(uid=uid, limit=1)[0].timestamp)
        if latest_timestamp is None:
            return
        latest_datetime = datetime.fromtimestamp(latest_timestamp/1000.0)
        dtime = timedelta(days=62)
        max_dates = 20
        count = 1
        while True:
            count = count + 1
            print("-----------------------------------------------------------")
            times = [(latest_datetime - dtime, latest_datetime)]
            timestamps = [((latest_datetime - dtime).timestamp()*1000.0,\
                            latest_datetime.timestamp()*1000.0)]
            for i in range(1, max_dates):
                (t2,t3) = times[i-1]
                t1 = t2 - dtime
                times.append((t1, t2))
                timestamps.append((t1.timestamp()*1000.0,\
                                   t2.timestamp()*1000.0))
            (last_timestamp,dummy) = timestamps[len(timestamps)-1]
            latest_datetime = datetime.fromtimestamp(last_timestamp/1000.0)
            Session = scoped_session(self.sessionmaker)
            def task(dbsession, timestamp_pair, uid, user):
                Session()
                (t1, latest_timestamp) = timestamp_pair
                while float(latest_timestamp) > t1:
                    fetched = self.fetch_message_history(uid=uid,\
                                                         limit=50,\
                                                         before=latest_timestamp)
                    if len(fetched) is 0:
                        Session.remove()
                        return False
                    latest_timestamp = fetched[len(fetched)-1].timestamp
                    for msg in fetched:
                        if msg.text is None:
                            continue
                        self.store_message2(dbsession=Session,\
                                            timestamp=int(msg.timestamp),\
                                            uid=uid,\
                                            message_id=msg.uid,\
                                            text=msg.text,\
                                            author_uid=msg.author,\
                                            user=user)
                        
                Session.remove()  
                return True
            
            with ThreadPoolExecutor(25) as executor:
                futures = []
                dbsessions = []
                for timestamp in timestamps:
                    dbsession = self.sessionmaker()
                    dbsessions.append(dbsession)
                    future = executor.submit(task, dbsession, timestamp, uid, user)
                    futures.append(future)
                    for future in futures:
                        future.result()
                    if len(self.fetch_message_history(uid=uid, limit=40,before=last_timestamp)) is 0:
                        print("timestamp: " + str(last_timestamp))
                        print(datetime.fromtimestamp(last_timestamp/1000.0))
                        print("is zero")
                        return
                        break
        print("count: " + str(count))
        return
            
    '''
    def get(self, target_name):
        (name, uid) = self.find_thread(target_name)
        self.store_user(name=name, uid=uid)
        user = self.dbsession.query(User).get(uid)
        latest_timestamp = self.fetch_message_history(uid=uid, limit=1)[0].timestamp
        #print("latest timestamp: " + str(latest_timestamp))
        while True:
            fetched = self.fetch_message_history(uid=uid, limit=40, before=latest_timestamp)
            if len(fetched) is 0:
                break
            latest_timestamp = fetched[len(fetched)-1].timestamp
            print(latest_timestamp)
            for msg in fetched:
                if msg.text is None:
                    continue
                self.store_message(timestamp=int(msg.timestamp),\
                                   uid=uid,\
                                   message_id=msg.uid,\
                                   text=msg.text,\
                                   author_uid=msg.author,\
                                   user=user)
                for attach in msg.attachments:
                    if isinstance(attach, ImageAttachment):
                        self.store_image(image_uid=attach.uid,\
                                         user_uid=uid,\
                                         url=fetchImageUrl(attach.uid))
                    if isinstance(attah, FileAttachment):
                        self.store_file(file_uid=attach.uid,\
                                        user_uid=uid,\
                                        name=name,\
                                        url=attach.url,\
                                        size=attach.size)

    '''
    
    # update will get until the latest timestamp
    def update(self, target_name):
        (name, uid) = self.find_thread(target_name)
        self.store_user(name=name, uid=uid)
        user = self.dbsession.query(User).get(uid)
        latest_timestamp = self.fetch_message_history(uid=uid, limit=1)[0].timestamp
        ok = True
        while ok:
            fetched = self.fetch_message_history(uid=uid, limit=40, before=latest_timestamp)
            if len(fetched) is 0:
                break
            latest_timestamp = fetched[len(fetched)-1].timestamp
            for msg in fetched:
                if msg.text is None:
                    continue
                for attach in msg.attachments:
                    if isinstance(attach, ShareAttachment):
                        print("found share attachment")
                if not self.store_message(timestamp=int(msg.timestamp),\
                                          uid=uid,\
                                          message_id=msg.uid,\
                                          text=msg.text,\
                                          author_uid=msg.author,\
                                          user=user):
                    ok = False
                    break
                for attach in msg.attachments:
                    if isinstance(attach, ImageAttachment):
                        self.store_image(image_uid=attach.uid,\
                                         user_uid=uid,\
                                         url=fetchImageUrl(attach.uid))
                    if isinstance(attah, FileAttachment):
                        self.store_file(file_uid=attach.uid,\
                                        user_uid=uid,\
                                        name=name,\
                                        url=attach.url,\
                                        size=attach.size)
        return
    
    def logout(self):
        self.client.logout()
