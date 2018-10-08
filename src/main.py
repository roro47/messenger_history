#!/usr/bin/python3
import re
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from .messenger_db import User, Base, Message, Image, File, Url, Video

from . import format
from .fb_chat import FbBot
from .command_parser import get_parser, update_parser, show_parser, less_parser
from datetime import datetime

import subprocess
from getpass import getpass

import os

def main():
    if not os.environ['MSGH_DB_PATH']:
        print("Not intalled")
    db_path = os.environ['MSGH_DB_PATH']
    engine = create_engine('sqlite://' + db_path)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    
    email = input("email> ")
    password = getpass("password> ")
    start_time = datetime(year=2018, month=1, day=1)
    fbbot = FbBot(email, password, session, engine, start_time)

    ok = True
    
    def get(args, fbbot=fbbot):
        args = get_parser.parse_args(args)
        if not args.user:
            return True
        fbbot.get_concurrent(args.user.replace('-', ' '))
        return True

    def update(args, fbbot=fbbot):
        args = update_parser.parse_args(args)
        if not args.user:
            return True
        fbbot.update_concurrent(args.user)
        return True

    def show(args, fbbot=fbbot, session=session):
        #TODO: update the session
        args = show_parser.parse_args(args)
        users = session.query(User)\
                       .filter(User.name==args.user.replace('-', ' ')).all()
        if len(users) is 0:
            print("No such user in database.")
            return
        uid = users[0].user_uid
        texts = []
        images = []
        urls = []
        regex = args.regex if args.regex else ".*"
        regex = re.compile(regex)
        
        
        if "texts" in args.option or "all" in args.option:
            texts += session.query(Message)\
                            .filter(False \
                                    if not Message.text \
                                    else Message.thread_uid==uid and \
                                    regex.search(Message.text))\
                            .order_by(asc(Message.timestamp))\
                            .all()
    
        if "images" in args.option or "all" in args.option:
            images += session.query(Image)\
                            .filter(Message.thread_uid==uid and \
                                    regex.search(Image.url))\
                            .order_by(asc(Image.timestamp))\
                            .all()
            
        if "urls" in args.option or "all" in args.option:
            urls += session.query(Url)\
                           .filter(Url.thread_uid==uid and \
                                   regex.search(Url.url))\
                           .order_by(asc(Url.timestamp))\
                           .all()

        # pretty print
        print("format: "+str(args.format))
        if args.format=="default":
            list(map(format.text_default, texts))
            list(map(format.image_default, images))
            list(map(format.url_default, urls))
        return True

    
    def less(args, fbbot=fbbot, session=session):
        args = less_parser.parse_args(args)
        args.user = args.user.replace('-', ' ')
        users = session.query(User)\
                       .filter(User.name==args.user).all()
        if len(users) is 0:
            print("No such user in database.")
            return
        uid = users[0].user_uid
        contents = []
        
        if "texts" in args.option or "all" in args.option:
            contents += session.query(Message)\
                               .filter(Message.thread_uid==uid) \
                               .order_by(asc(Message.timestamp))\
                               .all()

        
        if "images" in args.option or "all" in args.option:
            contents += session.query(Image)\
                               .filter(Image.thread_uid==uid)\
                               .order_by(asc(Image.timestamp))\
                               .all()

        
        if "urls" in args.option or "all" in args.option:
            contents += session.query(Url)\
                               .filter(Url.thread_uid==uid)\
                               .order_by(asc(Url.timestamp))\
                               .all()
        
        def take_timestamp(c):
            return c.timestamp
        
        contents.sort(key=take_timestamp)
        out = ""
        
        for i in range(0, len(contents)):
            header = "You: " if contents[i].author_uid == fbbot.uid \
                     else args.user + " "
            dtime = datetime.fromtimestamp(contents[i].timestamp/1000.0)
            header += str(dtime.year) + '-' + str(dtime.month) \
                      + '-' + str(dtime.day) + ' ' + \
                      str(dtime.hour) + ':' + str(dtime.minute) \
                      + ':' + str(dtime.second)
            m = ''
            if isinstance(contents[i], Message):
                m += "text <" + contents[i].text + ">"
            elif isinstance(contents[i], Image):
                m += "image <" + contents[i].url + ">"
            elif isinstance(contents[i], Url):
                m += "url <" + contents[i].url + ">"
            out += header + '\n'
            out += m + '\n'
        
            
        maxlen = 0
        out = out.encode('utf-8')
        pager = subprocess.Popen(['less'], stdin=subprocess.PIPE)
        p = pager.communicate(out)

        return True

    def help(args):
        get_parser.print_help()
        update_parser.print_help()
        show_parser.print_help()
        less_parser.print_help()
        return True
        
    def quit_(args, fbbot=fbbot):
        fbbot.logout()
        return False

    def reset(args, db_path=db_path):
        open(db_path, 'w').close()
        
    commands_map =  { "get": get, \
                      "update": update, \
                      "show": show, \
                      "less": less, \
                      "quit": quit_ ,\
                      "help": help, \
                      "reset": reset}
    
    while ok:
        command = input(">").split()
        args = command[1:]
        f = commands_map[command[0]]
        if not f:
            print("command " + command[0] + " not found")
        else:
            ok = f(args)
    return
        
if __name__ == '__main__':
    main()
