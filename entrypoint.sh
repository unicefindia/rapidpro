#!/bin/bash
set -e

case $4 in
    beat)
        /usr/bin/supervisord -n -c config/celery-$4.conf
;;
esac

case $1 in
    supervisor)
        /usr/bin/supervisord -n -c supervisor-app.conf
    ;;
    celery)
        case $6 in
            flows|handler|celery)
                /usr/bin/supervisord -n -c config/celery-$6.conf
            ;;
            *)
        esac
esac

exec "$@"