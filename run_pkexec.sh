#!/bin/bash

# FocusGuard launcher using pkexec for GUI privilege escalation
cd "$(dirname "$0")"

echo "Starting FocusGuard with elevated privileges using pkexec..."

# Use pkexec to run with elevated privileges while preserving GUI environment
pkexec env DISPLAY="$DISPLAY" \
    XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    HOME="$HOME" \
    USER="$USER" \
    /usr/bin/python3.12 main.py "$@"
