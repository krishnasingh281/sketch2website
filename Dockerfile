FROM python:3.9-alpine3.18
LABEL maintainer="local01.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./scripts /scripts
COPY ./app /app
WORKDIR /app
EXPOSE 9000

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache mysql-client mariadb-connector-c-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base mariadb-dev musl-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    apk add --no-cache bash && \
    # Create directories with correct permissions
    mkdir -p /app/media && \
    mkdir -p /app/logs && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chmod 755 /app/media && \
    chmod 755 /app/logs && \
    chmod -R 755 /vol/web && \
    # Create temporary directory for vision API
    mkdir -p /tmp/vision_temp && \
    chmod 755 /tmp/vision_temp && \
    # Add the non-root user
    adduser --disabled-password --no-create-home appuser && \
    chmod -R +x /scripts && \
    # Make sure all directories are accessible
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /vol/web && \
    chown -R appuser:appuser /tmp/vision_temp

# Set a temp directory that appuser can write to
ENV PATH="/scripts:/py/bin:$PATH"
ENV TMPDIR="/tmp/vision_temp"

USER appuser

CMD ["run.sh"]