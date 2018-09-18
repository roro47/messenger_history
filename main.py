from fb_chat import FbBot

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from messenger_db import User, Base, Message

# get [user]
# update [user]

# less [option]
#      -u (user)
#      -t (text)
# try to combine with less functionality


# 
def main():
    engine = create_engine("sqlite:///message.db")
    #engine = create_engine("") # fill this
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    
    email = "" # fill this
    password = "" # fill this
    fbbot = FbBot(email, password, session, engine)

    while True:
        command = input(">")
        command = command.split(' ', 1)
        if "get" in command[0]:
            user = command[1]
            #fbbot.get(user)
            fbbot.get_concurrent(user)
        elif "update" in command[0]:
            user = command[1]
            fbbot.update(user)
        elif "quit" in command[0]:
            fbbot.logout()
            break
        else:
            break
        
if __name__ == '__main__':
    main()
