#!/usr/bin/env bash
echo "====================================================================="
echo " Starting Intelligent Document Investigator (Algothon '26 ALG-AI-02)"
echo "====================================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python was not found in your system PATH."
        exit 1
    else
        PYTHON_CMD=python
    fi
else
    PYTHON_CMD=python3
fi

echo "Starting application server on http://localhost:8000 ..."
$PYTHON_CMD app.py
