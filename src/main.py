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

from fbchat import Client, FBchatException

import os
from exception import MissEnvException

'''
variable exported from environment
1. MSGH_DB_PATH
     path of database
2. FB_JOIN_TIME
     the time you join facebook, in the form of year:month:day
'''

def check_env():
    env_vars = ['MSGH_DB_PATH', 'FB_JOIN_TIME']
    for env in env_vars:
        if not os.environ[env]:
            raise MissEnvException(env)

def get_client():
     while client is None:
        email = input('email> ')
        password = getpass('password> ')
        try:
            client = Client(email, password)
        except FBchatException:
            print('Incorrect password or email')
    return client


def pass_global(*args):
    def main_decorator(f):
        def f_wrapper(c_args):
            return f(c_args, *args)
        return f_wrapper
    return main_decorator

@pass_global(fbbot)
def get(args):
    """
        Get all the chat history with the user from FB_JOIN_TIME
    """
    args = get_parser.parse_args(args)
    if not args.user:
        return True
    fbbot.get_concurrent(args.user.replace('-', ' '))
    return True

@pass_global(fbbot)
def update(args):
    """
       Update the chat history with the user in the database
    """
    args = update_parser.parse_args(args)
    if not args.user:
        return True
    fbbot.update_concurrent(args.user)
    return True

@pass_global(fbbot, session);
def show(args, fbbot, session):
    """
       Show the chat history with the user

    Print the content to the terminal
    """
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

@pass_global(fbbot, session)    
def less(args, fbbot=fbbot, session=session):
    """
        Show the chat history with the user
        
    Show the content in a less (unix command) style
    """
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
    """
    Print help
    """
    get_parser.print_help()
    update_parser.print_help()
    show_parser.print_help()
    less_parser.print_help()
    return True

@pass_global(fbbot)
def quit_(args, fbbot=fbbot):
    """
    Quit and logout
    """
    fbbot.logout()
    return False

def reset(args, db_path=db_path):
    """
    Clear the database
    """
    open(db_path, 'w').close()

def main():

    # check environment variable 
    try:
        check_env()
    except MissEnvException as e:
        print(e.message)

    # setup database
    db_path = os.environ['MSGH_DB_PATH']
    engine = create_engine(''.join('sqlite://', db_path))
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    # setup time
    fb_jt = [int(x) for x in os.environ['FB_JOIN_TIME'].split(':')]
    start_time = datatime(year=fb_jt[0], month=fb_jt[1], day=fb_jt[2]) 

    # setup user and bot
    client = get_client()
    fbbot = FbBot(client, session, engine, start_time)

    ok = True


    # closure functions

    def get(args, fbbot=fbbot):
    """
        Get all the chat history with the user from FB_JOIN_TIME
    """
        args = get_parser.parse_args(args)
        if not args.user:
            return True
        fbbot.get_concurrent(args.user.replace('-', ' '))
        return True

    def update(args, fbbot=fbbot):
    """
        Update the chat history with the user in the database
    """
        args = update_parser.parse_args(args)
        if not args.user:
            return True
        fbbot.update_concurrent(args.user)
        return True

    def show(args, fbbot=fbbot, session=session):
    """
        Show the chat history with the user

    Print the content to the terminal
    """
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
    """
        Show the chat history with the user
    
    Show the content in a less (unix command) style
    """
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
    """
       Print help
    """
        get_parser.print_help()
        update_parser.print_help()
        show_parser.print_help()
        less_parser.print_help()
        return True
        
    def quit_(args, fbbot=fbbot):
    """
       Quit and logout
    """
        fbbot.logout()
        return False

    def reset(args, db_path=db_path):
    """
       Clear the database
    """
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
