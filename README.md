# messenger_history
This is a command-line tool that is used for fast retrieve of messenger massage

**Example**
```
~ msgh
>email # type in email
>password # type in password
>get Morty
.....# All your chat with Morty has been stored to the database
>less Morty
.... # View your chat with Morty like viewing document with less
>quit()
```

**Installation**
  messenger_history is currently only available on Unix platform.
1. pip
```
pip install messenger_history
```
2. Download
git clone the repistory and run setup.py
```
python setup.py install
```
For both pip and Download,
You need to specify the directory you want to store the database.
For example, you want to store the database at /homes/foo/database.db
then
```
export MSGH_DB_PATH=/homes/foo/database.db
```

Usage
```
get <user or chat group name>
  # Get all the chat history and stored it in the database.
```
   
```
update <user or chat group name>
  # Update the chat history in the database.
```

```
less <user or chat group name>
  # Display chat in less(unix command) style
```

```
quit()
  # Quit current session.
```
