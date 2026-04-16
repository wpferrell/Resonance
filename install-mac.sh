#!/bin/sh
# Resonance -- Mac Install Script
# https://resonance-layer.com

set -e

echo ""
echo "+----------------------------------------------------------+"
echo "|          Resonance -- Emotional Memory for AI           |"
echo "+----------------------------------------------------------+"
echo ""
echo "Installing Resonance on Mac..."
echo ""

if ! command -v python3 > /dev/null 2>&1; then
    echo "ERROR: Python 3 is required but not installed."
    echo "  Install it with: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 10 ]; then
    echo "ERROR: Python 3.10 or higher is required."
    echo "  You have Python 3.$PYTHON_VERSION"
    exit 1
fi

echo "OK: $(python3 --version) found"

VENV_DIR="$HOME/resonance"
echo "Creating virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"
echo "OK: Virtual environment created"
echo ""
echo "Installing resonance-layer..."
echo ""

"$VENV_DIR/bin/pip" install --disable-pip-version-check --quiet resonance-layer > /tmp/resonance_pip.log 2>&1 &
PIP_PID=$!

WIDTH=40
FILLED=0
START=$(date +%s)

while kill -0 $PIP_PID 2>/dev/null; do
    NOW=$(date +%s)
    ELAPSED=$((NOW - START))
    if [ "$ELAPSED" -lt 10 ]; then TARGET=$((ELAPSED * 2))
    elif [ "$ELAPSED" -lt 30 ]; then TARGET=$((20 + (ELAPSED - 10) / 2))
    elif [ "$ELAPSED" -lt 90 ]; then TARGET=$((30 + (ELAPSED - 30) / 10))
    else TARGET=36; fi
    if [ "$TARGET" -gt 38 ]; then TARGET=38; fi
    if [ "$FILLED" -lt "$TARGET" ]; then FILLED=$((FILLED + 1)); fi
    PCT=$(( (FILLED * 100) / WIDTH ))
    EMPTY=$((WIDTH - FILLED))
    BAR=$(printf '%*s' "$FILLED" | tr ' ' '#')$(printf '%*s' "$EMPTY" | tr ' ' '-')
    printf "\r  [%s] %d%%  " "$BAR" "$PCT"
    sleep 0.3
done

wait $PIP_PID
BAR=$(printf '%*s' "$WIDTH" | tr ' ' '#')
printf "\r  [%s] 100%%\n" "$BAR"
echo ""
echo "OK: Resonance installed"
echo ""
echo "Downloading model weights (first run only, ~700MB)..."
echo "This may take a few minutes depending on your connection."
echo ""

"$VENV_DIR/bin/python3" -c "
import os
os.makedirs(os.path.expanduser('~/.resonance'), exist_ok=True)
import json
config_path = os.path.expanduser('~/.resonance/config.json')
if not os.path.exists(config_path):
    with open(config_path, 'w') as f:
        json.dump({'first_run_complete': True, 'feedback_enabled': False}, f)
from resonance.model_loader import ensure_model_downloaded
ensure_model_downloaded()
"

echo ""
echo "+----------------------------------------------------------+"
echo "|               Resonance is ready                        |"
echo "+----------------------------------------------------------+"
echo ""
echo "Activate your environment any time:"
echo "  source ~/resonance/bin/activate"
echo ""
echo "Then in your Python project:"
echo "  from resonance import Resonance"
echo "  r = Resonance(user_id='your-user-id')"
echo "  result = r.process('your message here')"
echo ""
echo "To enable anonymous feedback to help improve Resonance:"
echo "  r.set_feedback(True)"
echo ""
echo "Developer guide: https://resonance-layer.com/guide"
echo ""
