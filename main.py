import re
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from messenger_db import User, Base, Message, Image, File, Url, Video

from curses import wrapper
import curses

import format
from fb_chat import FbBot
from command_parser import get_parser, update_parser, show_parser, less_parser
from datetime import datetime

def main():
    
    engine = create_engine("sqlite:///message.db")
    #engine = create_engine("") # fill this
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    
    email = "" # fill this
    password = "" # fill this
    #email = input("email> ")
    #password = input("password> ")
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
                                    else Message.user_uid==uid and \
                                    regex.search(Message.text))\
                            .order_by(asc(Message.timestamp))\
                            .all()
    
        if "images" in args.option or "all" in args.option:
            images += session.query(Image)\
                            .filter(Message.user_uid==uid and \
                                    regex.search(Image.url))\
                            .order_by(asc(Image.timestamp))\
                            .all()
            
        if "urls" in args.option or "all" in args.option:
            urls += session.query(Url)\
                           .filter(Url.user_uid==uid and \
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
        users = session.query(User)\
                       .filter(User.name==args.user.replace('-', ' ')).all()
        if len(users) is 0:
            print("No such user in database.")
            return
        uid = users[0].user_uid
        contents = []

        
        if "texts" in args.option or "all" in args.option:
            contents += session.query(Message)\
                               .filter(Message.user_uid==uid) \
                               .order_by(asc(Message.timestamp))\
                               .all()
            
        if "images" in args.option or "all" in args.option:
            contents += session.query(Image)\
                               .filter(Message.user_uid==uid)\
                               .order_by(asc(Image.timestamp))\
                               .all()
            
        if "urls" in args.option or "all" in args.option:
            contents += session.query(Url)\
                               .filter(Url.user_uid==uid)\
                               .order_by(asc(Url.timestamp))\
                               .all()

        def take_timestamp(c):
            return c.timestamp
        
        contents.sort(key=take_timestamp)

        for i in range(0, len(contents)):
            if isinstance(contents[i], Message):
                contents[i] = "text <" + contents[i].text + ">"
            elif isinstance(contents[i], Image):
                contents[i] = "image <" + contents[i].url + ">"
            elif isinstance(contents[i], Url):
                contents[i] = "url <" + contents[i].url + ">"
        maxlen = 0
        for c in contents:
            maxlen = len(c) if len(c) > maxlen else maxlen
            
        def display(stdscr):
            stdscr.clear()
            pad = curses.newpad(len(contents), maxlen)
            for i in range(0, len(contents)):
                pad.addstr(i, 0, contents[i])
            pad.refresh(0,0,0,0,curses.LINES-1,curses.COLS - 1)
            pad.keypad(1)
            x = 0
            y = 0
            while 1:
                ch = pad.getch()
                if ch in [curses.KEY_DOWN]:
                    # down
                    y = y + 1 if y < len(contents) - curses.LINES else y
                    pad.refresh(y, x, 0, 0, curses.LINES-1, curses.COLS - 1)
                elif ch in [curses.KEY_UP]:
                    y = y - 1 if y > 0 else y
                    pad.refresh(y, x, 0, 0, curses.LINES-1, curses.COLS - 1)
                else:
                    break
            pad.keypad(0)

        wrapper(display)
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
        
    commands_map =  { "get": get, \
                      "update": update, \
                      "show": show, \
                      "less": less, \
                      "quit": quit_ ,\
                      "help": help}
    
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
