FROM python:3.9-alpine3.13
LABEL maintainer="local01.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app

WORKDIR /app
EXPOSE 8000

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache mysql-client mariadb-connector-c-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base mariadb-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    apk add --no-cache bash && \
    # Create directory for media uploads
    mkdir -p /app/media && \
    chmod 777 /app/media && \
    # Create temporary directory for vision API
    mkdir -p /tmp/vision_temp && \
    chmod 777 /tmp/vision_temp && \
    # Add the non-root user
    adduser --disabled-password --no-create-home appuser && \
    # Make sure the app directory is accessible
    chown -R appuser:appuser /app

# Set a temp directory that appuser can write to
ENV PATH="/py/bin:$PATH"
ENV TMPDIR="/tmp/vision_temp"

USER appuser

CMD ["/py/bin/python", "manage.py", "runserver", "0.0.0.0:8000"]