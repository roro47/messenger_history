import re
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from messenger_db import User, Base, Message

import format
from fb_chat import FbBot
from command_parser import get_parser, update_parser, show_parser

def main():
    engine = create_engine("sqlite:///message.db")
    #engine = create_engine("") # fill this
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    
    email = "" # fill this
    password = "" # fill this
    fbbot = FbBot(email, password, session, engine)

    ok = True
    
    def get(args, fbbot=fbbot):
        args = get_parser.parse_args(args)
        if not args.user:
            return
        fbbot.get_concurrent(args.user)
        return

    def update(args, fbbot=fbbot):
        args = update_parser.parse_args(args)
        if not args.user:
            return
        fbbot.update_concurrent(args.user)
        return

    def show(args, fbbot=fbbot, session=session):
        #TODO: update the session
        args = show_parser.parse_args(args)
        users = session.query(User).filter(User.name == args.user)
        if len(users) is 0:
            print("No such user in database.")
            return
        uid = users[0].uid
        texts = []
        images = []
        urls = []
        regex = args.regex if args.regex else ",*"
        regex = re.compile(regex)
        
        if "texts" in args.option:
            texts += session.query(Message)\
                            .filter(False \
                                    if not Message.text \
                                    else Message.user_uid==uid and \
                                    regex.search(Message.text))\
                            .order_by(desc(float(Message.timestamp)))
            break
        if "images" in args.option:
            images += session.query(Image)\
                            .filter(Message.user_uid==uid and \
                                    regex.search(Image.url))
            break
        if "urls" in args.option:
            urls += session.query(Url)\
                           .filter(Url.user_uid==uid and \
                                   regex.search(Url.url))

        # pretty print
        if args.format=="default":
            map(format.text_default, texts)
            map(format.image_default, images)
            map(format.url_default, images)
        
    def quit_(args, fbbot=fbbot, ok=ok):
        fbbot.loggout()
        ok = False
        
    commands_map =  { "get": get, \
                      "update": update, \
                      "show": show, \
                      "quit": quit_ }
    
    while ok:
        command = input(">").split()
        args = command[1:]
        f = commands_map[command[0]]
        if not f:
            print("command " + command[0] + " not found")
        else:
            f(args)
    return
        
if __name__ == '__main__':
    main()
