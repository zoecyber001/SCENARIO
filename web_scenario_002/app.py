from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'scenario_002_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================================================
# CONFIGURATION
# ============================================================================

PRINTER_MODEL = "HP LaserJet 4250n (Legacy)"
PRINTER_IP = "10.22.18.44"
PRINTER_MAC = "00:1B:78:44:55:66"
FIRMWARE_VER = "20180201_4250_FW_REV_2.1"
COMPROMISED_FW = "20240901_4250_FW_REV_X.9"

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    emit('log', {'type': 'system', 'message': 'WebSocket connected'})

@socketio.on('start_scenario')
def handle_start_scenario():
    print("[DEBUG] ========== SCENARIO START REQUESTED ==========")
    try:
        # Start scenario in background task using socketio
        socketio.start_background_task(run_scenario)
        print("[DEBUG] Background task started successfully")
        return {'status': 'started'}
    except Exception as e:
        print(f"[ERROR] Failed to start scenario: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

# ============================================================================
# SCENARIO LOGIC
# ============================================================================

def emit_log(log_type, message, delay=0):
    """Emit log message to frontend"""
    if delay > 0:
        socketio.sleep(delay)
    print(f"[EMIT] Sending log: {log_type} - {message[:50]}...")
    socketio.emit('log', {
        'type': log_type,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

def emit_hex(addr, data):
    """Emit hex dump line"""
    hex_str = " ".join(f"{b:02X}" for b in data)
    ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
    socketio.emit('hex', {
        'addr': f"{addr:04X}",
        'hex': hex_str,
        'ascii': ascii_str
    })

def emit_telemetry(key, value):
    """Update telemetry panel"""
    socketio.emit('telemetry', {'key': key, 'value': value})

def emit_effect(effect_type):
    """Trigger visual effect"""
    socketio.emit('effect', {'type': effect_type})

def run_scenario():
    """Main scenario execution"""
    try:
        print("[DEBUG] ========== SCENARIO EXECUTION STARTED ==========")
        
        # Phase 0: The Hook - Show the printed message
        print("[DEBUG] Phase 0: Starting hook")
        emit_log('info', "Client complaint: 'Printers printing messages at night.'", 0)
        socketio.sleep(1)
        emit_log('warning', "Reported message: 'WHO CHECKED THE LOGS?'", 0)
        socketio.sleep(1)
        emit_log('info', "Occurrence: Every night at 02:17 AM", 0)
        socketio.sleep(2)
        
        # Phase 1: Connection
        emit_telemetry('status', 'CONNECTING')
        emit_log('cmd', f'connect --target={PRINTER_IP}', 1)
        emit_log('success', f'Connected to {PRINTER_IP}', 1)
        emit_telemetry('status', 'CONNECTED')
        emit_telemetry('ip', PRINTER_IP)
        emit_telemetry('model', PRINTER_MODEL)
        
        emit_log('cmd', 'check_print_server_logs', 0.5)
        socketio.sleep(1.5)
        emit_log('alert', 'LOG BUFFER EMPTY', 0)
        emit_log('warning', 'No print jobs found in last 24h.', 0)
        socketio.sleep(2)
        
        # Phase 2: Memory Dump
        emit_log('cmd', 'initiate_memory_dump --target=buffer_0x8000', 1)
        emit_telemetry('status', 'DUMPING MEMORY')
        
        # Simulate hex dump
        start_addr = 0x8000
        for i in range(25):
            data = bytes([random.randint(0, 255) for _ in range(8)])
            emit_hex(start_addr + (i*8), data)
            socketio.sleep(0.05)
        
        emit_log('info', 'Memory dump complete. Analyzing...', 1)
        socketio.sleep(2)
        
        # Phase 3: Firmware Extraction
        emit_telemetry('status', 'ANALYZING')
        emit_log('info', 'Comparing firmware checksums...', 0.5)
        socketio.sleep(1)
        emit_log('alert', 'CHECKSUM MISMATCH', 0)
        emit_log('success', f'Expected: {FIRMWARE_VER}', 0)
        emit_log('error', f'Actual:   {COMPROMISED_FW}', 0)
        socketio.sleep(2)
        
        emit_log('cmd', 'extract_firmware_module --offset=0x8400', 1)
        socketio.sleep(1.5)
        emit_log('success', "Embedded module extracted: 'scheduler.py'", 0)
        socketio.sleep(1)
        
        # Code Reveal
        emit_log('info', 'Displaying source code...', 1)
        
        code_lines = [
            "def nightly_task():",
            "    if time.now().hour == 2:",
            "        msg = random.choice(lines)",
            "        printer.print(msg)",
            "",
            "# ERROR: 'lines' source not found"
        ]
        for line in code_lines:
            socketio.emit('code', {'line': line})
            socketio.sleep(0.3)
        
        socketio.sleep(2)
        
        # Phase 4: The Twist
        emit_telemetry('status', 'INVESTIGATING')
        emit_log('info', "Tracing 'lines' variable source...", 1)
        socketio.sleep(1.5)
        emit_log('alert', 'REFERENCE FOUND: /scans/failed/archived/', 0)
        socketio.sleep(1)
        emit_log('cmd', 'ls /scans/failed/archived/ | wc -l', 0.5)
        socketio.sleep(0.5)
        emit_log('warning', '124 text fragments found', 0)
        socketio.sleep(1)
        emit_log('cmd', 'cat /scans/failed/archived/*', 0.5)
        socketio.sleep(1)
        
        # Creepy logs
        emit_log('info', 'Displaying fragment samples...', 0.5)
        socketio.sleep(0.5)
        
        creepy_logs = [
            "Someone accessed 10.22.18.44 at 15:04.",
            "Meeting Room B mic was live.",
            "Root login from unknown fingerprint.",
            "Conference call transcript: Project Nightfall",
            "WHO CHECKED THE LOGS?",
            "Executive summary document: Q4_Financials.pdf"
        ]
        
        for log in creepy_logs:
            emit_log('fragment', f'{log}', 0)
            socketio.sleep(1.2)
        
        # Conclusion
        emit_telemetry('status', 'COMPROMISED')
        emit_log('alert', 'REMOTE ACCESS TROJAN (RAT) DETECTED', 1)
        emit_log('info', 'Threat Level: CRITICAL', 0)
        socketio.sleep(1)
        emit_log('info', 'Attack Vector: Modified firmware with embedded interpreter', 0)
        socketio.sleep(1)
        emit_log('info', 'C2 Infrastructure: Hidden in printer scan metadata', 0)
        socketio.sleep(1)
        emit_log('info', 'Data Exfiltration: Active (124 fragments captured)', 0)
        socketio.sleep(2)
        emit_log('success', 'Evidence collected. Recommendation: Isolate device immediately.', 0)
        emit_telemetry('status', 'INVESTIGATION COMPLETE')
        print("[DEBUG] ========== SCENARIO COMPLETED ==========")
        
    except Exception as e:
        print(f"[ERROR] Scenario failed: {e}")
        import traceback
        traceback.print_exc()
        emit_log('error', f'System error: {str(e)}', 0)

# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    print("🌐 Starting Web Interface for SCENARIO 002")
    print("📡 Open browser: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
