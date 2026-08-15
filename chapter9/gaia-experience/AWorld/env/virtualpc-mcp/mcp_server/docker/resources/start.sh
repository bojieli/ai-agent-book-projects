#!/bin/bash
set -e

echo "Starting services..."
echo "DISPLAY=$DISPLAY"

# Start supervisord to manage all processes
exec supervisord -c /etc/supervisor/supervisord.conf
