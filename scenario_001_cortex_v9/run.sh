#!/bin/bash
# SCENARIO 001 // The Whispering Laptop
# CORTEX-V9 AI Diagnostic Tool

echo "🧠 Starting CORTEX-V9 AI Diagnostic Tool"
echo "📡 SCENARIO 001 // The Whispering Laptop"
echo ""

# Check dependencies
if ! command -v edge-tts &> /dev/null; then
    echo "⚠️  edge-tts not found. Install with: pip install edge-tts"
    exit 1
fi

if ! command -v mpg123 &> /dev/null; then
    echo "⚠️  mpg123 not found. Install with: sudo apt install mpg123"
    exit 1
fi

# Run the Textual TUI
python3 cortex_v9.py
