#!/bin/sh
set -e

# Replace only required variables to avoid empty ones staying as-is
envsubst '${LISTEN_PORT} ${APP_HOST} ${APP_PORT}' < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"
