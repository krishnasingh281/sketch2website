server {
    listen ${LISTEN_PORT};
    listen 443 ssl;
    server_name api.testproject.live;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

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

server {
    listen 80;
    server_name api.testproject.live;
    return 301 https://$host$request_uri;
}