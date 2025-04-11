server {
    listen ${LISTEN_PORT};
    server_name _;  # Accept all hostnames

    location /static {
        alias /vol/web/static;
    }

    location /media {
        alias /vol/media;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}