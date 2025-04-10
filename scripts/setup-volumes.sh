#!/bin/bash

# Script to initialize Docker volumes with correct permissions
echo "Setting up Docker volumes with correct permissions..."

# Create temporary containers to set permissions
docker-compose -f docker-compose-deploy.yml down -v
docker volume rm static-data media-data app-logs || true
docker volume create static-data
docker volume create media-data
docker volume create app-logs

# Create temporary container to set permissions
docker run --rm -v static-data:/vol/web alpine sh -c "mkdir -p /vol/web/static /vol/web/media && chmod -R 755 /vol/web && chown -R 1000:1000 /vol/web"
docker run --rm -v media-data:/vol/media alpine sh -c "mkdir -p /vol/media && chmod -R 755 /vol/media && chown -R 1000:1000 /vol/media"
docker run --rm -v app-logs:/app/logs alpine sh -c "mkdir -p /app/logs && chmod -R 755 /app/logs && chown -R 1000:1000 /app/logs"

echo "Docker volumes initialized successfully!"