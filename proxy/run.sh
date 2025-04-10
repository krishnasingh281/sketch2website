#!/bin/sh

set -e

# Replace environment variables in the template
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

# Start nginx in foreground
nginx -g 'daemon off;'