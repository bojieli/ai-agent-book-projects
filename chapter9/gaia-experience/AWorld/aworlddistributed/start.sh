#!/usr/bin/env bash
PORT="${PORT:-9099}"
HOST="${HOST:-0.0.0.0}"
# Default value for PIPELINES_DIR
PIPELINES_DIR=${PIPELINES_DIR:-./aworldspace/agents}

UVICORN_LOOP="${UVICORN_LOOP:-auto}"

# OSS mount configuration - read from environment variables
if [ -n "$OSS_BUCKET" ] && [ -n "$OSS_AK_ID" ] && [ -n "$OSS_AK_SECRET" ]; then
    echo "Configuring OSS mount..."

    # Create OSS credentials file
    echo "${OSS_BUCKET}:${OSS_AK_ID}:${OSS_AK_SECRET}" >> /etc/passwd-ossfs
    chmod 640 /etc/passwd-ossfs

    # Create mount point directories if they don't exist
    mkdir -p /app/logs
    mkdir -p /app/trace_data
    mkdir -p /app/aworldspace/datasets

    # Mount OSS directories
    echo "Mounting OSS directories..."
    if [ -n "$OSS_REGION_URL" ] && [ -n "$OSS_BUCKET_URL" ]; then
        # Use custom region and URL
        ossfs ${OSS_BUCKET}:/aworld/logs /app/logs -odirect_read -ononempty -oregion=${OSS_REGION_URL} -ourl=${OSS_BUCKET_URL} &
        ossfs ${OSS_BUCKET}:/aworld/trace_data /app/trace_data -odirect_read -ononempty -oregion=${OSS_REGION_URL} -ourl=${OSS_BUCKET_URL} &
        ossfs ${OSS_BUCKET}:/aworld/datasets /app/aworldspace/datasets -odirect_read -ononempty -oregion=${OSS_REGION_URL} -ourl=${OSS_BUCKET_URL} &
    else
        # Use default configuration
        ossfs ${OSS_BUCKET}:/aworld/logs /app/logs -odirect_read -ononempty &
        ossfs ${OSS_BUCKET}:/aworld/trace_data /app/trace_data -odirect_read -ononempty &
        ossfs ${OSS_BUCKET}:/aworld/datasets /app/aworldspace/datasets -odirect_read -ononempty &
    fi

    # Wait for mount to complete
    sleep 2
    echo "OSS mount configuration completed"
else
    echo "OSS configuration incomplete, skipping OSS mount"
fi


uvicorn main:app --host "$HOST" --port "$PORT" --forwarded-allow-ips '*' --loop "$UVICORN_LOOP"

