#!/bin/bash

install_path="/usr/local/bin"
db_path="~/.local/msgh"

if [ "$#" -ne 1 ]; then
    echo "msgh installed in "$install_path
elif [ ${1:0:1} == "-"]; then
    echo "./setup.sh [-h] <install_path or /usr/local/bin by default>"
else
    install_path=$1
fi

install_path="/homes/qs4617/usr/local/bin"

echo "creating hard link"

chmod +x `pwd`'/run.sh'
ln `pwd`'/run.sh' $install_path'/msgh'

echo "init database"
mkdir -p $db_path
touch $db_path'/message.db'

echo "add environment variable: MSGH_DB_PATH = "$db_path 
echo "add environment varaible: MSGH_PATH = path to project"
