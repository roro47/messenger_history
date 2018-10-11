#!/usr/bin/python3
import os
from functools import partial
from datetime import datetime
from getpass import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fbchat import Client, FBchatException
from sqlalchemy.ext.declarative import declarative_base

from src.exception import *
from src.fb_chat import FbBot
from src.command import *
from src.util import eprint

from src.messenger_db import Base

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
    client = None
    while client is None:
        email = input('email> ')
        password = getpass('password> ')
        try:
            client = Client(email, password)
        except FBchatException:
            print('Incorrect password or email')
    return client

def main():
    # check environment variable 
    try:
        check_env()
    except MissEnvException as e:
        print(e.message)

    # setup database
    db_path = os.environ['MSGH_DB_PATH']
    if os.path.isfile(db_path):
        engine = create_engine('sqlite:////'+db_path)
        Base.metadata.create_all(engine)
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
    else:
        return

    # setup time
    fb_jt = [int(x) for x in os.environ['FB_JOIN_TIME'].split('-')]
    start_time = datetime(year=fb_jt[0], month=fb_jt[1], day=fb_jt[2]) 

    # setup user and bot
    client = get_client()
    fbbot = FbBot(client, session, engine, start_time)

    commands_map =  { "get": partial(get, fbbot=fbbot), \
                      "update": partial(update, fbbot), \
                      "show": partial(show, fbbot=fbbot,\
                                      session=session), \
                      "less": partial(show, fbbot=fbbot,\
                                      session=session,\
                                      stream="less"), \
                      "quit": partial(quit_, fbbot=fbbot),\
                      "help": help, \
                      "reset": partial(reset, db_path=db_path)}
    
    ok = True

    while ok:
        command = input(">").split()
        args = command[1:]
        f = commands_map[command[0]]
        if f is None:
            eprint("command ", command[0], " not found")
        else:
            ok = f(args)
    return
        
if __name__ == '__main__':
    main()
