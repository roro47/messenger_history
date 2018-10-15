import re
import subprocess
from datetime import datetime
from sqlalchemy import desc, asc

from src.messenger_db import *
from src.command_parser import *
from src.util import eprint, dtstr, to_fb, from_fb

"""

For all commands, if there are spaces in username,
replace with "-"

"""

def get(args, fbbot):
    """
        Get all the chat history with the user from FB_JOIN_TIME
    """
    args = get_parser.parse_args(args) 
    args.user = args.user.replace('-', ' ')
    
    if not args.user:
        eprint("format incorrect")
    else:
        fbbot.get_concurrent(args.user.replace('-', ' '))

    return True

def update(args, fbbot):
    """
       Update the chat history with the user in the database
    """
    args = update_parser.parse_args(args)
    args.user = args.user.replace('-', ' ')
    
    if not args.user:
        eprint("format incorrect")
    else:
        fbbot.update_concurrent(args.user)
        
    return True

def show(args, fbbot, session, stream):
    """
        Show the chat history with the user
        
    Show the content in a less (unix command) style
    """
    args = less_parser.parse_args(args)
    args.user = args.user.replace('-', ' ')
    if stream == 'less':
        args.stream = 'less'
    users = session.query(User).filter(User.name==args.user).all()
    
    if len(users) is 0:
        eprint("No such user in database.")
        return
    
    uid = users[0].user_uid
    contents = []

    if "texts" in args.option or "all" in args.option:
        contents += (session.query(Message)
                            .filter(Message.thread_uid==uid)
                            .order_by(asc(Message.timestamp))
                            .all())


    if "images" in args.option or "all" in args.option:
        contents += (session.query(Image)
                            .filter(Image.thread_uid==uid)
                            .order_by(asc(Image.timestamp))
                            .all())


    if "urls" in args.option or "all" in args.option:
        contents += (session.query(Url)
                            .filter(Url.thread_uid==uid)
                            .order_by(asc(Url.timestamp))
                            .all())

    def take_timestamp(c):
        return c.timestamp

    contents.sort(key=take_timestamp)
    out = ""

    for i in range(0, len(contents)):
        dtime = datetime.fromtimestamp(from_fb(contents[i].timestamp))
        
        header = ("You: " if contents[i].author_uid == fbbot.uid
                 else args.user + " ")
        header += dtstr(dtime)
        
        msg = ''
        if isinstance(contents[i], Message):
            msg += "text <" + contents[i].text + ">"
        elif isinstance(contents[i], Image):
            msg += "image <" + contents[i].url + ">"
        elif isinstance(contents[i], Url):
            msg += "url <" + contents[i].url + ">"
            
        out += header + '\n'
        out += msg + '\n'

    if args.stream == 'less':
        out = out.encode('utf-8')
        pager = subprocess.Popen(['less'], stdin=subprocess.PIPE)
        p = pager.communicate(out)
    elif args.stream == 'stdout':
        print(out)
    elif args.stream == 'stderr':
        eprint(out)
    else:
        try:
            with open(args.stream, 'w') as f:
                f.write(out)
        except Exception:
            eprint("Cannot write to file")
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

def quit_(args, fbbot):
    """
    Quit and logout
    """
    fbbot.logout()
    return False

def reset(args, db_path):
    """
    Clear the database
    """
    open(db_path, 'w').close()
    return True

