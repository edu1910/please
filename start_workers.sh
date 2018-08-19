#!/bin/bash

set -e

PROJECT=/home/www/please
LOGFILE=$PROJECT/please.log
ERRORFILE=$PROJECT/error.log

LOGDIR=$(dirname $LOGFILE)

NUM_WORKERS=1

#The below address:port info will be used later to configure Nginx with Gunicorn

ADDRESS=127.0.0.1:8000

# user/group to run as

#USER=your_unix_user

#GROUP=your_unix_group

source /home/www/.virtualenvs/please/bin/activate
cd $PROJECT/

exec python manage.py runworker
