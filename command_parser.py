import argparse

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(message)

get_parser = ArgumentParser(description='Retrieve all the messenger history with one user')
get_parser.add_argument("user")

update_parser = ArgumentParser(description="Update the messenger chat")
update_parser.add_argument("user")

show_parser = ArgumentParser(description="show the messenger history with a user")
show_parser.add_argument("user")
show_parser.add_argument("-f", "--format", help="format of output")
show_parser.add_argument("-o", "--option", help="display options: all, texts, urls, images", default="all")
show_parser.add_argument("-r", "--regex", help="regex used to search")

