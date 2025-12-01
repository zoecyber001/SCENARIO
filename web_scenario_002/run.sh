#!/bin/bash
# SCENARIO 002 // The Printer That Knew Too Much
# PRINTMON Forensics Tool

echo "🔍 Starting PRINTMON Forensics Tool"
echo "📡 SCENARIO 002 // The Printer That Knew Too Much"
echo "📊 Open browser: http://localhost:5000"
echo ""

# Check dependencies
if ! python3 -c "import flask" &> /dev/null; then
    echo "⚠️  Flask not found. Install with: pip install flask flask-socketio"
    exit 1
fi

# Run the Flask app
python3 app.py
