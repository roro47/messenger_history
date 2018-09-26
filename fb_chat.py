from fbchat import Client
from fbchat.models import *

from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker, scoped_session
from messenger_db import User, Base, Message

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from datetime.datetime import fromtimestamp
from urlextract import URLExtract

class FbBot:
    def __init__(self, email, password, dbsession, engine, \
                 start_dtime):
        self.email = email
        self.password = password
        self.client = Client(email, password)
        self.dbsession = dbsession
        self.uid = self.client.uid
        self.engine = engine
        self.sessionmaker = sessionmaker(bind=engine, autoflush=False)
        self.urlextractor = URLExtract()
        self.start_dtime = start_dtime 
        
    def login(self):
        if not self.client.isLoggedIn():
            self.client.login(email, password)

    def find_thread(self, name):
        for thread in self.client.fetchThreadList():
            if name in thread.name:
                t = (thread.name, int(thread.uid))
        return t
    
    def fetch_history(self, uid, limit, before=-1, echo=False):
        if before is -1: # fetch latest message
            return self.client.fetchThreadMessages(thread_id=uid,\
                                                   limit=limit)
        return self.client.fetchThreadMessages(thread_id=uid,\
                                               limit=limit, \
                                               before=before)

    def store_user(self, name, uid):
        q = exists().where(User.user_uid==uid)
        
        if not self.dbsession.query(q).scalar():
            self.dbsession.add(User(name=name, user_uid=uid))
            self.dbsession.commit()
            return True
        return False

    def store_video(self, video_uid, user_uid, timestamp):
        if not self.dbsession\
                   .query(exists()\
                          .where(Video.video_uid==video_uid))\
                   .scalar():
            self.dbsession.add(Video(video_uid=video_uid,\
                                     user_uid=user_uid,\
                                     timestamp=timestamp))
    
    def store_image(self, image_uid, user_uid, url, timestamp):
        if not self.dbsession\
                   .query(exists()\
                          .where(Image.image_uid==image_uid))\
                   .scalar():
            self.dbsession.add(Image(image_uid=image_uid,\
                                     user_uid=user_uid, \
                                     url=url, \
                                     timestamp=timestamp))
            return True
        return False

    def store_file(self, file_uid, user_uid, name, url, size,\
                   timestamp):
        
        q = exists().where(File.file_uid==file_uid)
        
        if not self.dbsession.query(q).scalar():
            self.dbsession.add(File(file_uid=file_uid,\
                                    user_uid=user_uid,\
                                    name=name, \
                                    url=url,\
                                    size=size,\
                                    timestamp=timstamp))
            return True
        return False

    def store_message(self, timestamp, uid, message_id, \
                      text, author_uid, user):
        print("< " + text + " >")
        
        q = exists()\
            .where(Message.timestamp==timestamp)\
            .where(Message.user_uid==uid)
        
        if not self.dbsession.query(q).scalar():
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

    def store_url(self, dbsession, url, user_uid, author_uid,\
                  timestamp):
        q = exists().where(Url.url==url)
        if not dbsession.query(q).scalar():
            dbsession.add(Url(url=url, \
                              user_uid=user_uid, \
                              author_uid=author_uid,\
                              timestamp=timestamp))
            dbsession.commit()
            return True
        return False
        
    def store_message(self, dbsession, timestamp, user_uid, \
                       message_id, text, author_uid, user):
        print("< " + text + " >")
        q = exists()\
            .where(Message.timestamp==timestamp)\
            .where(Message.user_uid==uid)
        if not dbsession.query(q).scalar():
            dbsession.add(Message(timestamp=timestamp, \
                                  user_uid=uid, \
                                  message_uid=message_id, \
                                  text=text))
            dbsession.commit()
            return True
        else:
            return False

    def get_concurrent(self, target_name, update=False):
        (name, uid) = self.find_thread(target_name)
        if not uid:
            print("No such friend")
            return
        self.store_user(name=name, uid=uid)
        
        last_tstamp = float(self.fetch_history(uid=uid,limit=1)[0]\
                            .timestamp)
        if last_tstamp is None:
            return
        
        m = 1000.0
        last_dtime = fromtimestamp(last_tstamp/m)
        dtime = timedelta(days=62) # size of increment
        max_dates = 20
        count = 1

        last_stored = float(self.dbsession\
                            .query(Message)\
                            .order_by(asc(Message.timestamp))[0])
        
        while True:
            count = count + 1
            print('-' * 80)
            times = [(last_dtime-dtime, last_dtime)]
            timestamps = [((last_dtime-dtime).timestamp()*m,\
                            last_dtime.timestamp()*m)]
            for i in range(1, max_dates):
                (start_t1, end_t1) = times[i-1]
                start_t2 = start_t1 - dtime
                times.append((start_t2, start_t1))
                timestamps.append((start_t2.timestamp()*m,\
                                   start_t1.timestamp()*m))
                
            (last_tstamp,dummy) = timestamps[len(timestamps)-1]
            last_dtime = fromtimestamp(last_tstamp/m)
            
            Session = scoped_session(self.sessionmaker)
            
            def task(timestamp_pair, uid, user):
                Session()
                (t1, last_tstamp) = timestamp_pair
                while float(last_tstamp) > t1:
                    fetched = self\
                              .fetch_history(uid=uid,\
                                             limit=50,\
                                             before=last_tstamp)
                    if len(fetched) is 0:
                        Session.remove()
                        return False
                    last_tstamp = fetched[len(fetched)-1].timestamp
                    for msg in fetched:
                        if msg.text is None:
                            continue
                        for a in msg.attachments:
                            if isinstance(a, ImageAttachment):
                                url=self.client \
                                        .fetchImageUrl(a.uid)
                                self.store_image(image_uid=a.uid,\
                                                 user_uid=uid,\
                                                 url=url)
                            elif isinstance(a, FileAttachment):
                                self.store_file(file_uid=a.uid,\
                                                user_uid=uid,\
                                                name=a.name,\
                                                url=a.url,\
                                                size=a.size)
                                                
                        
                        urls = self.urlextractor.find_urls(msg.text)

                        for url in urls:
                            self.store_url(dbsession=Session,\
                                           url=url,\
                                           user_uid=uid,\
                                           author_uid=msg.author)
                            self.store_message(dbsession=Session,\
                                               timestamp=\
                                               int(msg.timestamp),\
                                               uid=uid,\
                                               message_id=msg.uid,\
                                               text=msg.text,\
                                               author_uid=msg.author,\
                                               user=user)
                        
                Session.remove()  
                return True
            
            with ThreadPoolExecutor(25) as executor:
                futures = []
                for tstamp in timestamps:
                    future = executor.submit(task, tstamp, uid, user)
                    futures.append(future)
                    for future in futures:
                        future.result()
                    if len(self.fetch_history(uid=uid, \
                                              limit=40, \
                                              before=last_tstamp)) \
                                              is 0:
                        return
            if update and last_dtime.timstamp()*m >= last_stored:
                break
            # break if time before user start using facebook
            if last_dtime < self.start_time:
                break
            
        return

    def update_concurrent(self, target_name):
        self.get_concurrent(target_name, update=True)
   
    def logout(self):
        self.client.logout()
