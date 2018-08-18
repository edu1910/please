#!/bin/bash

set -e

PROJECT=/home/ubuntu/project/please
LOGFILE=$PROJECT/please.log
ERRORFILE=$PROJECT/error.log

LOGDIR=$(dirname $LOGFILE)

NUM_WORKERS=1

#The below address:port info will be used later to configure Nginx with Gunicorn

ADDRESS=127.0.0.1:8000

# user/group to run as

#USER=your_unix_user

#GROUP=your_unix_group

source /home/ubuntu/.virtualenvs/please/bin/activate
cd $PROJECT/

exec celery worker -A please -B
