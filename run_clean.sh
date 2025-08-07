#!/bin/bash

# Clean launcher for FocusGuard - bypasses snap conflicts
cd "$(dirname "$0")"

echo "Starting FocusGuard with system Python (clean environment)..."

# Remove all snap paths and use only system libraries
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
unset LD_LIBRARY_PATH
unset PYTHONPATH

# Set up GUI environment
export DISPLAY=${DISPLAY:-:0}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER}
mkdir -p "$XDG_RUNTIME_DIR"

# Use system python directly with explicit path and no snap interference
export LD_LIBRARY_PATH=""
unset SNAP
unset SNAP_DATA
unset SNAP_COMMON

exec env -i \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    DISPLAY=${DISPLAY:-:0} \
    HOME=$HOME \
    USER=$USER \
    XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER} \
    /usr/bin/python3.12 main.py "$@"

"$0.run_clean.sh"
