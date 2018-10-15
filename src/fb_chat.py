from fbchat import Client
from fbchat.models import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from urlextract import URLExtract
from sqlalchemy import exists, asc, desc, and_
from sqlalchemy.orm import sessionmaker, scoped_session

from src.messenger_db import *
from src.util import to_fb, from_fb

class FbBot:
    def __init__(self, client, dbsession, engine,
                 start_dtime):
        self.client = client
        self.dbsession = dbsession
        self.uid = int(self.client.uid)
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
        if before == -1: # fetch latest message
            return self.client.fetchThreadMessages(thread_id=uid,
                                                   limit=limit)
        return self.client.fetchThreadMessages(thread_id=uid,
                                               limit=limit,
                                               before=before)

    def store_user(self, name, uid):
        q = exists().where(User.user_uid == uid)
        
        if not self.dbsession.query(q).scalar():
            self.dbsession.add(User(name=name, user_uid=uid))
            self.dbsession.commit()
            return True
        return False

    def store_video(self, dbsession, video_uid, thread_uid, timestamp,
                    author_uid):
        q = exists().where((Video.timestamp == timestamp) &
                                (Video.author_uid == author_uid))
        if not dbsession.query(q).scalar():
            dbsession.add(Video(video_uid=video_uid,
                                thread_uid=thread_uid,
                                author_uid=author_uid,
                                timestamp=timestamp))
    
    def store_image(self, dbsession, image_uid, thread_uid, url,
                    author_uid, timestamp):
        q = exists().where((Image.timestamp == timestamp) &
                           (Image.author_uid == author_uid) &
                           (Image.image_uid == image_uid))
        if not dbsession.query(q).scalar():
            dbsession.add(Image(image_uid=image_uid,
                                thread_uid=thread_uid,
                                url=url,
                                author_uid=author_uid,
                                timestamp=timestamp))
            return True
        return False

    def store_file(self, dbsession, file_uid, thread_uid, author_uid,
                   name, url,size, timestamp):
        
        q = exists().where(and_(File.timestamp == timestamp,
                                File.author_uid == author_uid))
        
        if not dbsession.query(q).scalar():
            dbsession.add(File(file_uid=file_uid,
                               thread_uid=thread_uid,
                               author_uid=author_uid,
                               name=name,
                               url=url,
                               size=size,
                               timestamp=timestamp))
            return True
        return False

    def store_url(self, dbsession, url, thread_uid, author_uid,
                  timestamp):
        q = exists().where(and_(Url.timestamp == timestamp,
                                Url.author_uid == author_uid))
        if not dbsession.query(q).scalar():
            dbsession.add(Url(url=url,
                              thread_uid=thread_uid,
                              author_uid=author_uid,
                              timestamp=timestamp))
            dbsession.commit()
            return True
        return False
        
    def store_message(self, dbsession, timestamp, thread_uid,
                       message_id, text, author_uid):
        print("< " + text + " >")
        q = (exists()
            .where(Message.timestamp == timestamp)
            .where(Message.author_uid == author_uid))
        if not dbsession.query(q).scalar():
            dbsession.add(Message(timestamp=timestamp,
                                  thread_uid=thread_uid,
                                  author_uid=author_uid,
                                  message_uid=message_id,
                                  text=text))
            dbsession.commit()
            print("message added")
            return True
        else:
            print("message found")
            return False

    def get_concurrent(self, target_name, update=False):
        (name, uid) = self.find_thread(target_name)
        if not uid:
            eprint("No such friend")
            return
        self.store_user(name=name, uid=uid)
        
        last_tstamp = float(self.fetch_history(uid=uid,limit=1)[0]
                            .timestamp)
        if last_tstamp is None:
            return
        
        last_dtime = datetime.fromtimestamp(from_fb(last_tstamp))
        dtime = timedelta(days=62) # size of increment
        max_dates = 20

        if update:
            last_stored = float(self.dbsession
                                .query(Message)
                                .order_by(desc(Message.timestamp))[0]
                                .timestamp)
        
        while True:
            # establish one time range to collect text
            times = [(last_dtime-dtime, last_dtime)]
            timestamps = [((to_fb((last_dtime-dtime).timestamp()),
                            to_fb(last_dtime.timestamp())))]
    
            for i in range(1, max_dates):
                (start_t1, end_t1) = times[i-1]
                start_t2 = start_t1 - dtime
                times.append((start_t2, start_t1))
                timestamps.append((to_fb(start_t2.timestamp()),
                                   to_fb(start_t1.timestamp())))
            (last_tstamp,dummy) = timestamps[len(timestamps) - 1]
            last_dtime = datetime.fromtimestamp(from_fb(last_tstamp))
            
            Session = scoped_session(self.sessionmaker)

            # in each task, the worker fetch messages in
            # a given timestamp range
            # for example, (2018-01-03, 2018-04-28)
            def task(timestamp_pair, uid):
                Session()
                (from_tstamp, to_tstamp) = timestamp_pair
                prev = to_tstamp
                while float(to_tstamp) > from_tstamp:
                    fetched = (self
                              .fetch_history(uid=uid,
                                             limit=50,
                                             before=to_tstamp))
                    if len(fetched) == 0:
                        break
                    to_tstamp = fetched[len(fetched) - 1].timestamp
                    if float(to_tstamp) == float(prev):
                        break 
                    prev = to_tstamp
                    for msg in fetched:
                        # get all the attachment
                        for a in msg.attachments:
                            if isinstance(a, ImageAttachment):
                                url = self.client.fetchImageUrl(a.uid)
                                self.store_image(dbsession=Session,
                                                 image_uid=a.uid,
                                                 thread_uid=uid,
                                                 author_uid=
                                                 msg.author,
                                                 url=url,
                                                 timestamp=
                                                 msg.timestamp)
                            elif isinstance(a, FileAttachment):
                                self.store_file(dbsession=Session,
                                                file_uid=a.uid,
                                                thread_uid=uid,
                                                author_uid=
                                                msg.author,
                                                name=a.name,
                                                url=a.url,
                                                size=a.size,
                                                timestamp=
                                                msg.timestamp)
                                
                        # get texts and the url embedded
                        if msg.text is not None:
                            # extract url from text
                            urls = (self.urlextractor
                                       .find_urls(msg.text))
                            for url in urls:
                                self.store_url(dbsession=Session,
                                               url=url,
                                               thread_uid=uid,
                                               author_uid=msg.author,
                                               timestamp=
                                               int(msg.timestamp))

                            self.store_message(dbsession=Session,
                                               timestamp=
                                               int(msg.timestamp),
                                               thread_uid=uid,
                                               message_id=msg.uid,
                                               text=msg.text,
                                               author_uid=msg.author)
                Session.remove()  
                return True
            
            with ThreadPoolExecutor(25) as executor:
                futures = []
                for tstamp in timestamps:
                    future = executor.submit(task, tstamp, uid)
                    futures.append(future)
                    for future in futures:
                        future.result()
                        
            if update and to_fb(last_dtime.timstamp()) >= last_stored:
                break
            # break if time before user start using facebook
            if last_dtime < self.start_dtime:
                break
            
        return

    def update_concurrent(self, target_name):
        self.get_concurrent(target_name, update=True)
   
    def logout(self):
        self.client.logout()
