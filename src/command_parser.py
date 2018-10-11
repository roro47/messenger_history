import argparse

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(message)

notice = " , when input name, use - for space"
get_parser = ArgumentParser(description='Retrieve all the messenger history with one user' + notice)
get_parser.add_argument("user")

update_parser = ArgumentParser(description="Update the messenger chat" + notice)
update_parser.add_argument("user")

show_parser = ArgumentParser(description="show the messenger history with a user"+notice)
show_parser.add_argument("user")
show_parser.add_argument("-f", "--format", default="default", help="format of output" )
show_parser.add_argument("-o", "--option", default=["all"], help="display options: all, texts, urls, images")
show_parser.add_argument("-r", "--regex", default=".*", help="regex used to search")
show_parser.add_argument("-s", "--stream", help="specify the file path as the output stream")

less_parser = ArgumentParser(description="show the messenger history with a user in a less format"+notice)
less_parser.add_argument("user")
less_parser.add_argument("-o", "--option", default=["all"], help="display options: all, texts, urls, images")
less_parser.add_argument("-r", "--regex", default=".*", help="regex used to search")
less_parser.add_argument("-s", "--stream", help="specify the file path as the output stream")
